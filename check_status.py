import os
import sys
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

if not account_sid or not auth_token:
    print("ERROR: Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in .env")
    sys.exit(1)

client = Client(account_sid, auth_token)

# Get message SID from environment variable or command line argument
sid = os.getenv("MESSAGE_SID") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not sid:
    print("Usage: python check_status.py <MESSAGE_SID>")
    print("Or set MESSAGE_SID in .env")
    sys.exit(1)

try:
    message = client.messages(sid).fetch()
    print(f"Status: {message.status}")
    print(f"Error Code: {message.error_code}")
    print(f"Error Message: {message.error_message}")
    print(f"To: {message.to}")
    print(f"From: {message.from_}")
except Exception as e:
    print(f"Erro ao verificar: {e}")
