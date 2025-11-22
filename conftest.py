
import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Set dummy env vars for testing if not present
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "sk-test-key"
if "TELEGRAM_TOKEN" not in os.environ:
    os.environ["TELEGRAM_TOKEN"] = "TEST_TOKEN_DO_NOT_USE"
