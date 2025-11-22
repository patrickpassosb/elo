import os
import pytest

# Set environment variables for testing before any imports
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["TELEGRAM_TOKEN"] = "test-token"
os.environ["LLM_MODEL"] = "gpt-4o-test"
os.environ["TTS_MODEL"] = "tts-1"
os.environ["TTS_VOICE"] = "alloy"
os.environ["WHISPER_MODEL"] = "whisper-1"

@pytest.fixture(scope="session", autouse=True)
def set_env():
    """Fixture to ensure env vars are set (redundant but keeps fixture structure)."""
    pass
