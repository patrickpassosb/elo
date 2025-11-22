"""
Configuration for ELO Telegram Bot.
Provides typed access to environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from logging_config import logger

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation.
    Required keys are validated on startup.
    """
    # Required API keys
    openai_api_key: str
    telegram_token: str

    # Optional API keys
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    ngrok_authtoken: Optional[str] = None

    # Azure OpenAI configuration
    use_azure_openai: bool = False
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    azure_whisper_deployment: Optional[str] = None
    azure_tts_deployment: Optional[str] = None
    azure_vision_deployment: Optional[str] = None

    # OpenAI configuration
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    whisper_model: str = "whisper-1"
    tts_model: str = "tts-1"
    tts_voice: str = "onyx"  # alloy, echo, fable, onyx, nova, shimmer
    vision_max_tokens: int = 300

    # Application settings
    max_session_size: int = 1000
    session_ttl_hours: int = 24
    base_url: str = "http://localhost:8000"
    log_level: str = "INFO"
    log_file: str = "elo_bot.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def validate_required_keys(self) -> None:
        """Validate required environment variables based on mode."""
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "TELEGRAM_TOKEN": self.telegram_token,
        }
        if self.use_azure_openai:
            azure_required = {
                "AZURE_OPENAI_API_KEY": self.azure_openai_api_key,
                "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
                "AZURE_OPENAI_API_VERSION": self.azure_openai_api_version,
                "AZURE_WHISPER_DEPLOYMENT": self.azure_whisper_deployment,
                "AZURE_TTS_DEPLOYMENT": self.azure_tts_deployment,
                "AZURE_VISION_DEPLOYMENT": self.azure_vision_deployment,
            }
            required.update(azure_required)
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Please add them to your .env file."
            )

# Global settings instance
try:
    settings = Settings()
    settings.validate_required_keys()
except Exception as e:
    logger.error(f"❌ Configuration Error: {e}")
    logger.error("Please check your .env file and ensure all required variables are set.")
    raise

# Export settings
__all__ = ["settings"]
