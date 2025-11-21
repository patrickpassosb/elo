import os
import logging
import asyncio
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

from utils import transcribe_audio, text_to_speech, describe_image_local, cleanup_file
from brain import process_message

load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# User preferences: user_id -> 'audio' | 'text'
user_preferences = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    await update.message.reply_text(
        "Olá! Sou o ELO, seu Neto Digital. 👴💙\n\n"
        "Pode mandar:\n"
        "🎤 Áudio - Eu respondo com áudio\n"
        "📝 Texto - Eu respondo com texto\n"
        "📷 Foto - Eu leio e explico o que tem nela\n\n"
        "Estou aqui para te ajudar a entender documentos, leis e cartas!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main message handler for all types of messages"""
    user_id = str(update.effective_user.id)
    user_input = ""
    
    # Default preference
    if user_id not in user_preferences:
        user_preferences[user_id] = 'text'

    try:
        # 1. Process Input
        if update.message.voice:
            # Handle Voice
            logging.info(f"🎤 Recebido Áudio de {user_id}")
            user_preferences[user_id] = 'audio'
            
            # Download with unique filename
            file_id = uuid.uuid4().hex[:8]
            file_path = f"temp_{user_id}_{file_id}.ogg"
            
            try:
                new_file = await update.message.voice.get_file()
                await new_file.download_to_drive(file_path)
                
                # Transcribe (run in thread to avoid blocking)
                user_input = await asyncio.to_thread(transcribe_audio, file_path)
                logging.info(f"📝 Transcrição: {user_input}")
            finally:
                cleanup_file(file_path)

        elif update.message.photo:
            # Handle Photo
            logging.info(f"📷 Recebido Foto de {user_id}")
            
            # Get the largest photo with unique filename
            file_id = uuid.uuid4().hex[:8]
            file_path = f"temp_{user_id}_{file_id}.jpg"
            
            try:
                photo_file = await update.message.photo[-1].get_file()
                await photo_file.download_to_drive(file_path)
                
                # Describe using GPT-4o Vision (run in thread)
                user_input = await asyncio.to_thread(describe_image_local, file_path)
                logging.info(f"🔍 Descrição: {user_input}")
            finally:
                cleanup_file(file_path)

        elif update.message.text:
            # Handle Text
            user_input = update.message.text
            logging.info(f"💬 Recebido Texto de {user_id}: {user_input}")
            
            # Check for preference keywords
            lower_input = user_input.lower()
            if "áudio" in lower_input or "voz" in lower_input or "falar" in lower_input:
                user_preferences[user_id] = 'audio'
            elif "texto" in lower_input or "escrever" in lower_input:
                user_preferences[user_id] = 'text'
        else:
            await update.message.reply_text("Eu só entendo texto, áudio e fotos por enquanto, vó! 😊")
            return

        # 2. Process Logic (LangChain)
        # Send "typing" action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        # Run in thread to avoid blocking
        response_text = await asyncio.to_thread(process_message, user_id, user_input)
        logging.info(f"🤖 Resposta ELO: {response_text}")

        # 3. Generate Response
        if user_preferences[user_id] == 'audio':
            # Send voice response
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='record_voice')
            
            # Generate audio (run in thread)
            audio_path = await asyncio.to_thread(text_to_speech, response_text)
            
            try:
                with open(audio_path, 'rb') as audio_file:
                    await update.message.reply_voice(voice=audio_file)
            finally:
                cleanup_file(audio_path)
        else:
            # Send text response
            await update.message.reply_text(response_text)

    except Exception as e:
        logging.error(f"❌ Erro: {e}", exc_info=True)
        await update.message.reply_text("Desculpe, tive um problema técnico. Pode tentar de novo? 🙏")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ Erro: TELEGRAM_TOKEN não encontrado no .env")
        print("Por favor, adicione: TELEGRAM_TOKEN=seu_token_aqui")
        exit(1)
        
    application = ApplicationBuilder().token(token).build()
    
    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.ALL, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    
    logging.info("🤖 ELO Telegram Bot rodando...")
    logging.info("Pressione Ctrl+C para parar")
    application.run_polling()
