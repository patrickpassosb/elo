"""
OpenAI client wrapper with optional Azure OpenAI support.
"""

import base64
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, AzureOpenAI, APIError as OpenAIAPIError

from config import settings
from logging_config import logger
from exceptions import APIError

# Initialize client based on configuration
if settings.use_azure_openai:
    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
    )
else:
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


@retry(retry=retry_if_exception_type(APIError), wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
@_handle_api_error
def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using Whisper or Azure Whisper deployment.

    Args:
        file_path: Path to the audio file.
    Returns:
        Transcribed text.
    """
    model_name = settings.azure_whisper_deployment if settings.use_azure_openai else settings.whisper_model
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
        )
    return transcription.text


@retry(retry=retry_if_exception_type(APIError), wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
@_handle_api_error
def text_to_speech(text: str) -> str:
    """Convert text to speech using TTS model or Azure TTS deployment.

    Args:
        text: The text to convert.
    Returns:
        Path to the generated audio file.
    """
    model_name = settings.azure_tts_deployment if settings.use_azure_openai else settings.tts_model
    response = client.audio.speech.create(
        model=model_name,
        voice=settings.tts_voice,
        input=text,
    )
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        response.stream_to_file(path)
        return path
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        raise e


@retry(retry=retry_if_exception_type(APIError), wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
@_handle_api_error
def describe_image(image_url: str) -> str:
    """Describe an image from a URL using vision model or Azure vision deployment.

    Args:
        image_url: URL of the image.
    Returns:
        Description of the image.
    """
    model_name = settings.azure_vision_deployment if settings.use_azure_openai else settings.llm_model
    response = client.chat.completions.create(
        model=model_name,
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


@retry(retry=retry_if_exception_type(APIError), wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
@_handle_api_error
def describe_image_local(image_path: str) -> str:
    """Describe a local image file using vision model or Azure vision deployment.

    Args:
        image_path: Path to the local image file.
    Returns:
        Description of the image.
    """
    model_name = settings.azure_vision_deployment if settings.use_azure_openai else settings.llm_model
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    response = client.chat.completions.create(
        model=model_name,
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
