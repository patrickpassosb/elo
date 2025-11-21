import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

from utils import download_media, transcribe_audio, text_to_speech, describe_image, cleanup_file
from brain import process_message

load_dotenv()

app = FastAPI()

# Mount a directory to serve generated audio files
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# In-memory user preferences: sender_id -> 'audio' | 'text'
user_preferences = {}

# Base URL for this server (Must be set to Ngrok URL for Twilio to access media)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@app.get("/")
async def root():
    return {"message": "ELO Chatbot is running!"}

@app.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaContentType0: str = Form(None),
    MediaUrl0: str = Form(None),
):
    sender_id = From
    user_input = ""
    
    # Default preference if not set
    if sender_id not in user_preferences:
        user_preferences[sender_id] = 'text'

    # 1. Process Input
    try:
        if NumMedia > 0:
            if MediaContentType0 and MediaContentType0.startswith('audio/'):
                # Handle Audio
                print(f"Recebido Áudio de {sender_id}")
                user_preferences[sender_id] = 'audio' # Switch to audio mode
                
                # Download and Transcribe
                # Twilio audio extension usually .ogg or .mp3
                ext = MediaContentType0.split('/')[-1]
                if 'ogg' in ext: ext = 'ogg' # Fix for audio/ogg; codecs=opus
                
                local_audio_path = download_media(MediaUrl0, ext)
                user_input = transcribe_audio(local_audio_path)
                cleanup_file(local_audio_path)
                print(f"Transcrição: {user_input}")
                
            elif MediaContentType0 and MediaContentType0.startswith('image/'):
                # Handle Image
                print(f"Recebido Imagem de {sender_id}")
                # Use GPT-4o Vision directly with the URL
                user_input = describe_image(MediaUrl0)
                print(f"Descrição da Imagem: {user_input}")
                
            else:
                user_input = "Enviei um arquivo que não consigo ler. Pode mandar áudio, texto ou foto?"
        else:
            # Handle Text
            user_input = Body or ""
            print(f"Recebido Texto de {sender_id}: {user_input}")
            
            # Check for keywords to switch preference
            lower_input = user_input.lower()
            if "áudio" in lower_input or "voz" in lower_input or "falar" in lower_input:
                user_preferences[sender_id] = 'audio'
            elif "texto" in lower_input or "escrever" in lower_input:
                user_preferences[sender_id] = 'text'

        # 2. Process Logic (LangChain)
        response_text = process_message(sender_id, user_input)
        print(f"Resposta ELO: {response_text}")

        # 3. Generate Response
        resp = MessagingResponse()
        
        if user_preferences[sender_id] == 'audio':
            # Generate Audio
            audio_filename = text_to_speech(response_text)
            # Move to media folder
            final_path = os.path.join("media", audio_filename)
            os.rename(audio_filename, final_path)
            
            # Add Media to TwiML
            msg = resp.message("")
            msg.body(response_text) # Optional: send text transcript too? User asked for Audio.
            # Let's send just audio as requested, or maybe both? 
            # "Se o usuário manda áudio... o bot responde com ÁUDIO."
            # Usually better to send just audio or audio + text. 
            # Let's send Audio.
            media_url = f"{BASE_URL}/media/{audio_filename}"
            msg.media(media_url)
        else:
            # Send Text
            resp.message(response_text)

        return Response(content=str(resp), media_type="application/xml")

    except Exception as e:
        print(f"Erro: {e}")
        resp = MessagingResponse()
        resp.message("Desculpe, tive um problema técnico. Pode tentar de novo?")
        return Response(content=str(resp), media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
