import base64
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APIError as OpenAIAPIError

from config import settings
from logging_config import logger
from exceptions import APIError
from utils.media import temporary_file

# Initialize OpenAI client with validated API key
client = OpenAI(api_key=settings.openai_api_key)

def _handle_api_error(func):
    """Decorator to wrap API calls and convert exceptions to APIError."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error in {func.__name__}: {e}")
            raise APIError(f"Error in {func.__name__}: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise APIError(f"Unexpected error in {func.__name__}: {str(e)}") from e
    return wrapper

@retry(retry=retry_if_exception_type(APIError),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
@_handle_api_error
def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using OpenAI Whisper (whisper-1).
    
    Args:
        file_path (str): Path to the audio file.
        
    Returns:
        str: The transcribed text.
    """
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=settings.whisper_model,
            file=audio_file
        )
    return transcription.text

@retry(retry=retry_if_exception_type(APIError),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
@_handle_api_error
def text_to_speech(text: str) -> str:
    """Convert text to speech using OpenAI TTS (tts-1).
    
    Args:
        text (str): The text to convert.
        
    Returns:
        str: Path to the generated audio file.
    """
    response = client.audio.speech.create(
        model=settings.tts_model,
        voice=settings.tts_voice,
        input=text
    )
    # Here temporary_file is used correctly as a context manager because stream_to_file writes to it.
    # But wait, if temporary_file deletes on exit, we have the same problem!
    # The original code returned the path.
    # I need to fix this too.
    
    import tempfile
    import os
    
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    
    try:
        response.stream_to_file(path)
        return path
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        raise e

@retry(retry=retry_if_exception_type(APIError),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
@_handle_api_error
def describe_image(image_url: str) -> str:
    """Describe an image from a URL using GPT-4o vision model.
    
    Args:
        image_url (str): URL of the image.
        
    Returns:
        str: Description of the image.
    """
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

@retry(retry=retry_if_exception_type(APIError),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       reraise=True)
@_handle_api_error
def describe_image_local(image_path: str) -> str:
    """Describe a local image file using GPT-4o vision model.
    
    Args:
        image_path (str): Path to the local image file.
        
    Returns:
        str: Description of the image.
    """
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
