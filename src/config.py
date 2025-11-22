"""
Centralized configuration management for ELO Telegram Bot.

This module provides type-safe, validated access to all configuration
parameters loaded from environment variables.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from logging_config import logger

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings with validation.
    
    All required environment variables are validated on startup.
    Missing required variables will raise a ValidationError with clear error messages.
    """
    
    # ==================== Required API Keys ====================
    openai_api_key: str
    telegram_token: str
    
    # ==================== Optional API Keys ====================
    # WhatsApp/Twilio (for future use)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    ngrok_authtoken: Optional[str] = None
    
    # ==================== OpenAI Configuration ====================
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    whisper_model: str = "whisper-1"
    tts_model: str = "tts-1"
    tts_voice: str = "onyx"  # Options: alloy, echo, fable, onyx, nova, shimmer
    vision_max_tokens: int = 300
    
    # ==================== Application Settings ====================
    # Session management
    max_session_size: int = 1000
    session_ttl_hours: int = 24
    
    # Server configuration
    base_url: str = "http://localhost:8000"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "elo_bot.log"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra env vars
    )
    
    def validate_required_keys(self) -> None:
        """
        Validate that all required API keys are present.
        Raises ValueError with helpful message if any are missing.
        """
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "TELEGRAM_TOKEN": self.telegram_token,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please add them to your .env file. See .env.example for reference."
            )


# Global settings instance
try:
    settings = Settings()
    settings.validate_required_keys()
except Exception as e:
    logger.error(f"❌ Configuration Error: {e}")
    logger.error("Please check your .env file and ensure all required variables are set.")
    raise
    print("Please check your .env file and ensure all required variables are set.")
    raise


# Export settings
__all__ = ["settings"]
