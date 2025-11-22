import os
import pytest

# Set dummy environment variables BEFORE importing any modules that use settings
os.environ["TELEGRAM_TOKEN"] = "dummy_token"
os.environ["OPENAI_API_KEY"] = "sk-dummy-key"
os.environ["TWILIO_ACCOUNT_SID"] = "ACdummy"
os.environ["TWILIO_AUTH_TOKEN"] = "dummy_token"

@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch):
    """Make time.sleep instant to speed up retries."""
    monkeypatch.setattr("time.sleep", lambda x: None)
