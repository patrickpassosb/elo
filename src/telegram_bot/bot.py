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

if __name__ == "__main__":
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
    msg_handler = MessageHandler(filters.ALL, handle_message)
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    logger.info("🤖 ELO Telegram Bot rodando...")
    logger.info("Pressione Ctrl+C para parar")
    application.run_polling()
