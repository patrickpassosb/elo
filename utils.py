import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import base64

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def download_media(media_url: str, file_extension: str) -> str:
    """
    Downloads media from a Twilio URL and saves it locally.
    Returns the path to the saved file.
    """
    # Twilio requires basic auth if media protection is enabled, 
    # but often the URL provided in the webhook is accessible directly 
    # or contains a token. We'll try direct first, then auth if needed.
    # For the hackathon context, we assume standard accessible URLs or 
    # we would use TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    
    response = requests.get(media_url, auth=(account_sid, auth_token))
    
    if response.status_code == 200:
        filename = f"temp_media_{os.urandom(4).hex()}.{file_extension}"
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename
    else:
        raise Exception(f"Failed to download media: {response.status_code}")

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio using OpenAI Whisper (whisper-1).
    """
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcription.text

def text_to_speech(text: str) -> str:
    """
    Converts text to speech using OpenAI TTS (tts-1).
    Returns the path to the generated audio file.
    """
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx", # Or 'nova' as requested
        input=text
    )
    
    output_filename = f"response_{os.urandom(4).hex()}.mp3"
    response.stream_to_file(output_filename)
    return output_filename

def cleanup_file(file_path: str):
    """Removes a temporary file."""
    if os.path.exists(file_path):
        os.remove(file_path)

def describe_image(image_url: str) -> str:
    """
    Uses GPT-4o to describe an image from a URL.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva detalhadamente o conteúdo desta imagem, focando em ler qualquer texto visível e explicar o contexto (ex: se é uma conta, uma carta, um aviso)."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content
