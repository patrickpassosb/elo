import os
import asyncio
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from .config import settings
from .logging_config import logger
from .storage import preference_store
from .utils import transcribe_audio, text_to_speech, describe_image_local, cleanup_file
from .brain import process_message

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
            file_id = uuid.uuid4().hex[:8]
            file_path = f"temp_{user_id}_{file_id}.jpg"
            try:
                photo_file = await update.message.photo[-1].get_file()
                await photo_file.download_to_drive(file_path)
                user_input = await asyncio.to_thread(describe_image_local, file_path)
                logger.info(f"🔍 Descrição: {user_input}")
            finally:
                cleanup_file(file_path)
        elif update.message.text:
            user_input = update.message.text
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
        response_text = await asyncio.to_thread(process_message, user_id, user_input)
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
    except Exception as e:
        logger.error(f"❌ Erro: {e}", exc_info=True)
        await update.message.reply_text("Desculpe, tive um problema técnico. Pode tentar de novo? 🙏")

if __name__ == "__main__":
    token = settings.telegram_token
    if not token:
        logger.error("❌ Erro: TELEGRAM_TOKEN não encontrado na configuração.")
        exit(1)
    application = ApplicationBuilder().token(token).build()
    start_handler = CommandHandler("start", start)
    msg_handler = MessageHandler(filters.ALL, handle_message)
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    logger.info("🤖 ELO Telegram Bot rodando...")
    logger.info("Pressione Ctrl+C para parar")
    application.run_polling()
