import os
import requests
import base64
import logging
import tempfile
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import settings
from .logging_config import logger
from openai import OpenAI

# Initialize OpenAI client with validated API key
client = OpenAI(api_key=settings.openai_api_key)

@contextmanager
def temporary_file(suffix: str = "") -> str:
    """Create a temporary file that is automatically cleaned up.
    Returns the file path as a string.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # Close the low‑level descriptor
    try:
        yield path
    finally:
        try:
            os.remove(path)
            logger.debug(f"Temporary file removed: {path}")
        except OSError:
            pass

@retry(retry=retry_if_exception_type(requests.RequestException),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
def download_media(media_url: str, file_extension: str) -> str:
    """Download media from a URL and save it to a temporary file.
    Returns the temporary file path. Raises on HTTP errors.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    response = requests.get(media_url, auth=(account_sid, auth_token), timeout=10)
    response.raise_for_status()
    with temporary_file(suffix=f".{file_extension}") as tmp_path:
        with open(tmp_path, "wb") as f:
            f.write(response.content)
        return tmp_path

@retry(retry=retry_if_exception_type(Exception),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using OpenAI Whisper (whisper-1)."""
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=settings.whisper_model,
            file=audio_file
        )
    return transcription.text

@retry(retry=retry_if_exception_type(Exception),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
def text_to_speech(text: str) -> str:
    """Convert text to speech using OpenAI TTS (tts-1)."""
    response = client.audio.speech.create(
        model=settings.tts_model,
        voice=settings.tts_voice,
        input=text
    )
    with temporary_file(suffix=".mp3") as tmp_path:
        response.stream_to_file(tmp_path)
        return tmp_path

def cleanup_file(file_path: str) -> None:
    """Remove a temporary file if it exists (fallback)."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.debug(f"Removed temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {file_path}: {e}")

@retry(retry=retry_if_exception_type(Exception),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
def describe_image(image_url: str) -> str:
    """Describe an image from a URL using GPT-4o vision model."""
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva detalhadamente o conteúdo desta imagem, focando em ler qualquer texto visível e explicar o contexto (ex: se é uma conta, uma carta, um aviso)."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        max_tokens=settings.vision_max_tokens,
    )
    return response.choices[0].message.content

@retry(retry=retry_if_exception_type(Exception),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
def describe_image_local(image_path: str) -> str:
    """Describe a local image file using GPT-4o vision model."""
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Descreva detalhadamente o conteúdo desta imagem, focando em ler qualquer texto visível e explicar o contexto (ex: se é uma conta, uma carta, um aviso)."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }
        ],
        max_tokens=settings.vision_max_tokens,
    )
    return response.choices[0].message.content
