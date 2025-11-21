import os
import sys
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

sid = "SM5f6ed763e24868c552c75f922b808d61" # New SID

try:
    message = client.messages(sid).fetch()
    print(f"Status: {message.status}")
    print(f"Error Code: {message.error_code}")
    print(f"Error Message: {message.error_message}")
    print(f"To: {message.to}")
    print(f"From: {message.from_}")
except Exception as e:
    print(f"Erro ao verificar: {e}")
