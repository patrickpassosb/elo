import os
import asyncio
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from config import settings
from logging_config import logger
from storage import preference_store
from ai.openai_client import transcribe_audio, text_to_speech, describe_image_local
from utils.media import cleanup_file
from ai.brain import process_message
from exceptions import APIError, MediaError, ValidationError

# Helper functions for user preferences
def get_user_pref(user_id: str) -> str:
    """Get the user's response preference, defaulting to 'text'."""
    pref = preference_store.get(user_id)
    if pref is None:
        preference_store.set(user_id, "text")
        return "text"
    return pref

def set_user_pref(user_id: str, pref: str) -> None:
    """Set the user's response preference ('text' or 'audio')."""
    preference_store.set(user_id, pref)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text(
        "Olá! Sou o ELO, seu Neto Digital. 👴💙\n\n"
        "Pode mandar:\n"
        "🎤 Áudio - Eu respondo com áudio\n"
        "📝 Texto - Eu respondo com texto\n"
        "📷 Foto - Eu leio e explico o que tem nela\n\n"
        "**Comandos especiais:**\n"
        "/lei <tema> - Busco leis sobre um tema\n"
        "/deputado <nome> - Informações sobre um deputado\n"
        "/diario <cidade> <assunto> - Busco no Diário Oficial\n\n"
        "Estou aqui para te ajudar a entender documentos, leis e cartas!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main message handler for all supported message types."""
    user_id = str(update.effective_user.id)
    user_input = ""
    # Ensure a default preference exists
    _ = get_user_pref(user_id)

    try:
        # 1. Process Input
        if update.message.voice:
            logger.info(f"🎤 Recebido Áudio de {user_id}")
            set_user_pref(user_id, "audio")
            # Validate file size (max 20MB)
            if update.message.voice.file_size > 20 * 1024 * 1024:
                raise ValidationError("O arquivo de áudio é muito grande. Tente enviar um menor, por favor.")

            file_id = uuid.uuid4().hex[:8]
            file_path = f"temp_{user_id}_{file_id}.ogg"
            try:
                voice_file = await update.message.voice.get_file()
                await voice_file.download_to_drive(file_path)
                user_input = await asyncio.to_thread(transcribe_audio, file_path)
                logger.info(f"📝 Transcrição: {user_input}")
            finally:
                cleanup_file(file_path)
        elif update.message.photo:
            logger.info(f"📷 Recebido Foto de {user_id}")
            # Validate file size (max 20MB)
            photo = update.message.photo[-1]
            if photo.file_size > 20 * 1024 * 1024:
                raise ValidationError("A foto é muito pesada. Tente enviar uma menor ou com menos qualidade.")

            file_id = uuid.uuid4().hex[:8]
            file_path = f"temp_{user_id}_{file_id}.jpg"
            try:
                photo_file = await photo.get_file()
                await photo_file.download_to_drive(file_path)
                user_input = await asyncio.to_thread(describe_image_local, file_path)
                logger.info(f"🔍 Descrição: {user_input}")
            finally:
                cleanup_file(file_path)
        elif update.message.text:
            user_input = update.message.text
            
            # Validate text length
            if len(user_input) > 2000:
                raise ValidationError("O texto é muito longo. Tente mandar em pedaços menores, por favor.")

            logger.info(f"💬 Recebido Texto de {user_id}: {user_input}")
            lower = user_input.lower()
            if "áudio" in lower or "voz" in lower or "falar" in lower:
                set_user_pref(user_id, "audio")
            elif "texto" in lower or "escrever" in lower:
                set_user_pref(user_id, "text")
        else:
            await update.message.reply_text("Eu só entendo texto, áudio e fotos por enquanto, vó! 😊")
            return

        # 2. Process Logic (LangChain)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        # Run in thread to avoid blocking (now async in brain.py)
        response_text = await process_message(user_id, user_input)
        logger.info(f"🤖 Resposta ELO: {response_text}")

        # 3. Generate Response
        if get_user_pref(user_id) == "audio":
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")
            audio_path = await asyncio.to_thread(text_to_speech, response_text)
            try:
                with open(audio_path, "rb") as audio_file:
                    await update.message.reply_voice(voice=audio_file)
            finally:
                cleanup_file(audio_path)
        else:
            await update.message.reply_text(response_text)
    except ValidationError as e:
        logger.warning(f"⚠️ Validação: {e}")
        await update.message.reply_text(str(e))
    except MediaError as e:
        logger.error(f"❌ Erro de Mídia: {e}")
        await update.message.reply_text("Tive um problema para baixar ou processar seu arquivo. Pode tentar enviar de novo? 📁")
    except APIError as e:
        logger.error(f"❌ Erro de API: {e}")
        await update.message.reply_text("Estou com dificuldade para conectar com meu cérebro agora. Tente novamente em alguns instantes. 🧠")
    except Exception as e:
        logger.error(f"❌ Erro Inesperado: {e}", exc_info=True)
        await update.message.reply_text("Desculpe, tive um problema técnico inesperado. Pode tentar de novo? 🙏")

async def lei_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /lei <tema> command - searches for laws about a topic."""
    user_id = str(update.effective_user.id)
    
    # Check if user provided a topic
    if not context.args:
        await update.message.reply_text(
            "Por favor, me diga sobre qual tema você quer saber! 📜\n\n"
            "Exemplo: /lei educação"
        )
        return
    
    tema = " ".join(context.args)
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Import here to avoid circular imports
        from services.camara_api import get_proposicoes
        
        logger.info(f"🔍 Buscando leis sobre '{tema}' para usuário {user_id}")
        proposicoes = await get_proposicoes(tema, limit=5)
        
        if not proposicoes:
            await update.message.reply_text(
                f"Não encontrei nenhum projeto de lei sobre '{tema}' 😔\n\n"
                "Tente usar outras palavras-chave!"
            )
            return
        
        # Get the most recent one
        pl = proposicoes[0]
        
        # Create a summary message
        summary = (
            f"🔍 Encontrei {len(proposicoes)} projetos sobre '{tema}'.\n"
            f"Vou explicar o mais recente:\n\n"
            f"📜 {pl['tipo']} {pl['numero']}/{pl['ano']}\n\n"
        )
        
        # Use the brain to explain the law in simple terms
        explanation_prompt = (
            f"Explique de forma simples e clara o que é este projeto de lei:\n\n"
            f"{pl['ementa']}\n\n"
            f"Lembre-se de usar linguagem acessível para idosos."
        )
        
        explanation = await process_message(user_id, explanation_prompt)
        
        full_message = summary + explanation
        
        # Add reaction buttons hint
        full_message += "\n\n💡 Entendeu? Me mande uma mensagem se tiver dúvidas!"
        
        await update.message.reply_text(full_message)
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /lei: {e}", exc_info=True)
        await update.message.reply_text(
            "Desculpe, tive dificuldade para buscar as leis agora. "
            "Pode tentar de novo em alguns instantes? 📚"
        )

async def deputado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /deputado <nome> command - searches for deputy information."""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "Por favor, me diga o nome do deputado! 🏛️\n\n"
            "Exemplo: /deputado Tabata Amaral"
        )
        return
    
    nome = " ".join(context.args)
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        from services.camara_api import search_deputados, get_deputado
        
        logger.info(f"🔍 Buscando deputado '{nome}' para usuário {user_id}")
        deputados = await search_deputados(nome, limit=3)
        
        if not deputados:
            await update.message.reply_text(
                f"Não encontrei nenhum deputado com o nome '{nome}' 😔\n\n"
                "Verifique se escreveu corretamente!"
            )
            return
        
        # Get the first match
        dep = deputados[0]
        
        # Fetch detailed info
        dep_info = await get_deputado(dep['id'])
        
        if not dep_info:
            await update.message.reply_text("Não consegui buscar as informações desse deputado. Tente novamente!")
            return
        
        # Format the response
        message = (
            f"👤 **{dep_info['nome_parlamentar']}**\n\n"
            f"🏛️ Partido: {dep_info['partido']}/{dep_info['estado']}\n"
            f"📧 Email: {dep_info.get('email', 'Não disponível')}\n\n"
        )
        
        # Add a simple explanation using the brain
        explanation_prompt = (
            f"Explique de forma simples quem é o deputado {dep_info['nome_parlamentar']} "
            f"do partido {dep_info['partido']} do estado {dep_info['estado']}. "
            f"Seja breve e use linguagem acessível."
        )
        
        explanation = await process_message(user_id, explanation_prompt)
        message += explanation
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /deputado: {e}", exc_info=True)
        await update.message.reply_text(
            "Desculpe, tive dificuldade para buscar informações do deputado. "
            "Pode tentar de novo? 🏛️"
        )

async def diario_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /diario <cidade> <assunto> command - searches official gazettes."""
    user_id = str(update.effective_user.id)
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Por favor, me diga a cidade e o assunto! 📰\n\n"
            "Exemplo: /diario São Paulo merenda escolar"
        )
        return
    
    # First arg is city, rest is the query
    cidade = context.args[0]
    assunto = " ".join(context.args[1:])
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        from services.querido_diario_api import search_gazette
        
        logger.info(f"🔍 Buscando '{assunto}' no diário de {cidade} para usuário {user_id}")
        results = await search_gazette(cidade, assunto, limit=3)
        
        if not results:
            await update.message.reply_text(
                f"Não encontrei nada sobre '{assunto}' no Diário Oficial de {cidade} 😔\n\n"
                "Tente:\n"
                "• Usar outras palavras-chave\n"
                "• Verificar se o nome da cidade está correto\n"
                "• Buscar um assunto mais recente"
            )
            return
        
        # Get the most recent result
        entry = results[0]
        
        message = (
            f"📰 Encontrei {len(results)} menções a '{assunto}' no Diário de {cidade}!\n\n"
            f"📅 Publicação mais recente: {entry['date']}\n"
            f"📄 Edição: {entry.get('edition', 'N/A')}\n\n"
        )
        
        # Add excerpt if available
        if entry.get('excerpt'):
            message += f"📝 Trecho:\n{entry['excerpt'][:300]}...\n\n"
        
        # Use the brain to summarize
        summary_prompt = (
            f"Resuma de forma simples o que este trecho do Diário Oficial significa:\n\n"
            f"{entry.get('excerpt', 'Informação sobre ' + assunto)}\n\n"
            f"Use linguagem acessível para idosos."
        )
        
        summary = await process_message(user_id, summary_prompt)
        message += f"💡 **O que isso significa:**\n{summary}"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"❌ Erro no comando /diario: {e}", exc_info=True)
        await update.message.reply_text(
            "Desculpe, tive dificuldade para buscar no Diário Oficial. "
            "Pode tentar de novo? 📰"
        )

from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# ... (existing imports)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        pass  # Silence logs

def start_health_server():
    """Starts a dummy HTTP server to satisfy Render's port binding requirement."""
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"🌍 Health check server running on port {port}")

if __name__ == "__main__":
    # Start the dummy server for Render
    start_health_server()

    token = settings.telegram_token
    if not token:
        logger.error("❌ Erro: TELEGRAM_TOKEN não encontrado na configuração.")
        exit(1)
    application = (
        ApplicationBuilder()
        .token(token)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    start_handler = CommandHandler("start", start)
    lei_handler = CommandHandler("lei", lei_command)
    deputado_handler = CommandHandler("deputado", deputado_command)
    diario_handler = CommandHandler("diario", diario_command)
    msg_handler = MessageHandler(filters.ALL, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(lei_handler)
    application.add_handler(deputado_handler)
    application.add_handler(diario_handler)
    application.add_handler(msg_handler)
    logger.info("🤖 ELO Telegram Bot rodando...")
    logger.info("Pressione Ctrl+C para parar")
    application.run_polling()
