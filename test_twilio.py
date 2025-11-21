import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

if not account_sid or not auth_token:
    print("ERROR: Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in .env")
    sys.exit(1)

client = Client(account_sid, auth_token)

# Twilio WhatsApp Sandbox number
from_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", 'whatsapp:+14155238886')

# Your WhatsApp number for testing
to_whatsapp_number = os.getenv("TEST_WHATSAPP_NUMBER")
if not to_whatsapp_number:
    print("ERROR: Please set TEST_WHATSAPP_NUMBER in .env (format: whatsapp:+1234567890)")
    sys.exit(1) 

try:
    message = client.messages.create(
        body="Olá! Este é um teste direto do servidor do ELO. Se você recebeu isso, suas credenciais estão corretas!",
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )
    print(f"Mensagem enviada com sucesso! SID: {message.sid}")
except Exception as e:
    print(f"Erro ao enviar mensagem: {e}")
