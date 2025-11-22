# src/telegram_bot/bot.py
"""Telegram bot entry point integrating all hackathon phases.

Features:
- Basic interaction (audio, text, photo)
- Commands: /start, /fiscalizar, /minhas_inscricoes, /lei, /deputado, /diario
- Feedback callbacks
- Subscription management (phase 3)
"""

import os
import asyncio
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import settings
from logging_config import logger
from storage import preference_store
from ai.openai_client import transcribe_audio, text_to_speech, describe_image_local
from utils.media import cleanup_file
from ai.brain import process_message
from exceptions import APIError, MediaError, ValidationError

# Phase 3: Engagement features
from services.subscription_service import subscribe_topic, get_subscriptions
from services.feedback_service import save_feedback, get_sentiment_summary

# ---------------------------------------------------------------------------
# Helper functions for user preferences
# ---------------------------------------------------------------------------

def get_user_pref(user_id: str) -> str:
    """Return the user's response preference ("text" or "audio")."""
    pref = preference_store.get(user_id)
    if pref is None:
        preference_store.set(user_id, "text")
        return "text"
    return pref


def set_user_pref(user_id: str, pref: str) -> None:
    """Set the user's response preference."""
    preference_store.set(user_id, pref)

# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

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
        "/diario <cidade> <assunto> - Busco no Diário Oficial\n"
        "/fiscalizar <tema> - Acompanhar votações\n"
        "/minhas_inscricoes - Ver temas que você acompanha\n\n"
        "Estou aqui para te ajudar a entender documentos, leis e cartas!"
    )

# ---------------------------------------------------------------------------
# Phase 3: Engagement commands
# ---------------------------------------------------------------------------

async def fiscalizar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe the user to a topic for voting updates."""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "Por favor, me diga qual tema você quer fiscalizar!\n\n"
            "Exemplo: /fiscalizar educação\n"
            "Temas disponíveis: educação, saúde, meio ambiente"
        )
        return
    topic = " ".join(context.args)
    success = subscribe_topic(user_id, topic)
    if success:
        emojis = {"educação": "📚", "saúde": "🏥", "meio ambiente": "🌳"}
        emoji = emojis.get(topic.lower(), "📋")
        await update.message.reply_text(
            f"Ótimo! Vou te avisar quando houver votações sobre {topic}. {emoji}\n\n"
            "Use /minhas_inscricoes para ver todos os temas que você acompanha."
        )
    else:
        await update.message.reply_text(
            "Ops! Não consegui te inscrever nesse tema. Tente novamente mais tarde."
        )

async def minhas_inscricoes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List the topics the user is subscribed to."""
    user_id = update.effective_user.id
    subs = get_subscriptions(user_id)
    if not subs:
        await update.message.reply_text(
            "Você ainda não está acompanhando nenhum tema.\n\n"
            "Use /fiscalizar <tema> para começar a acompanhar votações!"
        )
        return
    topics_list = "\n".join([f"• {t}" for t in subs])
    await update.message.reply_text(
        f"📋 Você está acompanhando:\n\n{topics_list}\n\n"
        f"Total: {len(subs)} tema(s)"
    )

# ---------------------------------------------------------------------------
# Feedback callback handler (phase 3)
# ---------------------------------------------------------------------------

async def handle_feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    try:
        _, bill_id, sentiment = query.data.split(":")
        success = save_feedback(user_id, bill_id, sentiment)
        if success:
            msgs = {
                "concordo": "👍 Obrigado! Registrei que você concorda com essa lei.",
                "discordo": "👎 Obrigado! Registrei que você discorda dessa lei.",
                "neutro": "🤷 Obrigado! Registrei sua posição neutra.",
            }
            message = msgs.get(sentiment, "Obrigado pelo feedback!")
            summary = get_sentiment_summary(bill_id)
            if summary.get("total", 0) > 0:
                message += f"\n\n📊 Resumo geral:\n👍 {summary['concordo']} | 👎 {summary['discordo']} | 🤷 {summary['neutro']}"
            await query.edit_message_text(text=message)
        else:
            await query.edit_message_text(text="Ops! Não consegui salvar seu feedback. Tente novamente.")

    except Exception as e:
        logger.error(f"Error handling feedback callback: {e}", exc_info=True)
        await query.edit_message_text(text="Erro ao processar feedback.")

# ---------------------------------------------------------------------------
# Main message handler (audio, text, photo)
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    _ = get_user_pref(user_id)
    user_input = ""
    try:
        if update.message.voice:
            logger.info(f"🎤 Recebido Áudio de {user_id}")
            set_user_pref(user_id, "audio")
            if update.message.voice.file_size > 20 * 1024 * 1024:
                raise ValidationError("O arquivo de áudio é muito grande. Tente enviar um menor, por favor.")
            fid = uuid.uuid4().hex[:8]
            path = f"temp_{user_id}_{fid}.ogg"
            voice_file = await update.message.voice.get_file()
            await voice_file.download_to_drive(path)
            user_input = await asyncio.to_thread(transcribe_audio, path)
            logger.info(f"📝 Transcrição: {user_input}")
            cleanup_file(path)
        elif update.message.photo:
            logger.info(f"📷 Recebido Foto de {user_id}")
            photo = update.message.photo[-1]
            if photo.file_size > 20 * 1024 * 1024:
                raise ValidationError("A foto é muito pesada. Tente enviar uma menor ou com menos qualidade.")
            fid = uuid.uuid4().hex[:8]
            path = f"temp_{user_id}_{fid}.jpg"
            photo_file = await photo.get_file()
            await photo_file.download_to_drive(path)
            user_input = await asyncio.to_thread(describe_image_local, path)
            logger.info(f"🔍 Descrição: {user_input}")
            cleanup_file(path)
        elif update.message.text:
            user_input = update.message.text
            if len(user_input) > 2000:
                raise ValidationError("O texto é muito longo. Tente mandar em pedaços menores, por favor.")
            logger.info(f"💬 Recebido Texto de {user_id}: {user_input}")
            lower = user_input.lower()
            if any(word in lower for word in ["áudio", "voz", "falar"]):
                set_user_pref(user_id, "audio")
            elif any(word in lower for word in ["texto", "escrever"]):
                set_user_pref(user_id, "text")
        else:
            await update.message.reply_text("Eu só entendo texto, áudio e fotos por enquanto, vó! 😊")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        response_text = await process_message(user_id, user_input)
        logger.info(f"🤖 Resposta ELO: {response_text}")
        if get_user_pref(user_id) == "audio":
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")
            audio_path = await asyncio.to_thread(text_to_speech, response_text)
            with open(audio_path, "rb") as af:
                await update.message.reply_voice(voice=af)
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

# ---------------------------------------------------------------------------
# Phase 4: Legislative commands
# ---------------------------------------------------------------------------

async def lei_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text(
            "Por favor, me diga sobre qual tema você quer saber! 📜\n\n"
            "Exemplo: /lei educação"
        )
        return
    tema = " ".join(context.args)
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        from services.camara_api import get_proposicoes
        proposicoes = await get_proposicoes(tema, limit=5)
        if not proposicoes:
            await update.message.reply_text(
                f"Não encontrei nenhum projeto de lei sobre '{tema}' 😔\n\n"
                "Tente usar outras palavras-chave!"
            )
            return
        pl = proposicoes[0]
        summary = (
            f"🔍 Encontrei {len(proposicoes)} projetos sobre '{tema}'.\n"
            f"Vou explicar o mais recente:\n\n"
            f"📜 {pl['tipo']} {pl['numero']}/{pl['ano']}\n\n"
        )
        prompt = (
            f"Explique de forma simples e clara o que é este projeto de lei:\n\n"
            f"{pl['ementa']}\n\n"
            "Lembre-se de usar linguagem acessível para idosos."
        )
        explanation = await process_message(user_id, prompt)
        await update.message.reply_text(summary + explanation + "\n\n💡 Entendeu? Me mande uma mensagem se tiver dúvidas!")
    except Exception as e:
        logger.error(f"❌ Erro no comando /lei: {e}", exc_info=True)
        await update.message.reply_text(
            "Desculpe, tive dificuldade para buscar as leis agora. "
            "Pode tentar de novo em alguns instantes? 📚"
        )

async def deputado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        deputados = await search_deputados(nome, limit=3)
        if not deputados:
            await update.message.reply_text(
                f"Não encontrei nenhum deputado com o nome '{nome}' 😔\n\n"
                "Verifique se escreveu corretamente!"
            )
            return
        dep = deputados[0]
        dep_info = await get_deputado(dep['id'])
        if not dep_info:
            await update.message.reply_text("Não consegui buscar as informações desse deputado. Tente novamente!")
            return
        message = (
            f"👤 **{dep_info['nome_parlamentar']}**\n\n"
            f"🏛️ Partido: {dep_info['partido']}/{dep_info['estado']}\n"
            f"📧 Email: {dep_info.get('email', 'Não disponível')}\n\n"
        )
        prompt = (
            f"Explique de forma simples quem é o deputado {dep_info['nome_parlamentar']} "
            f"do partido {dep_info['partido']} do estado {dep_info['estado']}. "
            "Seja breve e use linguagem acessível."
        )
        explanation = await process_message(user_id, prompt)
        await update.message.reply_text(message + explanation)
    except Exception as e:
        logger.error(f"❌ Erro no comando /deputado: {e}", exc_info=True)
        await update.message.reply_text(
            "Desculpe, tive dificuldade para buscar informações do deputado. "
            "Pode tentar de novo? 🏛️"
        )

async def diario_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    if len(context.args) < 2:
        await update.message.reply_text(
            "Por favor, me diga a cidade e o assunto! 📰\n\n"
            "Exemplo: /diario São Paulo merenda escolar"
        )
        return
    cidade = context.args[0]
    assunto = " ".join(context.args[1:])
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        from services.querido_diario_api import search_gazette
        results = await search_gazette(cidade, assunto, limit=3)
        if not results:
            await update.message.reply_text(
                f"Não encontrei nada sobre '{assunto}' no Diário Oficial de {cidade} 😔\n\n"
                "Tente:\n"
                "• Usar outras palavras-chave\n"
                "• Verificar o nome da cidade\n"
                "• Buscar um assunto mais recente"
            )
            return
        entry = results[0]
        msg = (
            f"📰 Encontrei {len(results)} menções a '{assunto}' no Diário de {cidade}!\n\n"
            f"📅 Publicação mais recente: {entry['date']}\n"
            f"📄 Edição: {entry.get('edition', 'N/A')}\n\n"
        )
        if entry.get('excerpt'):
            msg += f"📝 Trecho (primeiros 300 chars):\n{entry['excerpt'][:300]}...\n\n"
        prompt = (
            f"Resuma de forma simples o que este trecho do Diário Oficial significa:\n\n"
            f"{entry.get('excerpt', f'Informação sobre {assunto}') }\n\n"
            "Use linguagem acessível para idosos."
        )
        summary = await process_message(user_id, prompt)
        msg += f"💡 **O que isso significa:**\n{summary}"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"❌ Erro no comando /diario: {e}", exc_info=True)
        await update.message.reply_text(
            "Desculpe, tive dificuldade para buscar no Diário Oficial. "
            "Pode tentar de novo? 📰"
        )

# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------

def main() -> None:
    application = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .build()
    )
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fiscalizar", fiscalizar))
    application.add_handler(CommandHandler("minhas_inscricoes", minhas_inscricoes))
    application.add_handler(CommandHandler("lei", lei_command))
    application.add_handler(CommandHandler("deputado", deputado_command))
    application.add_handler(CommandHandler("diario", diario_command))
    application.add_handler(CallbackQueryHandler(handle_feedback_callback))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    logger.info("🤖 ELO Telegram Bot rodando...")
    application.run_polling()

if __name__ == "__main__":
    main()
