import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

# O número do Sandbox (geralmente +14155238886)
from_whatsapp_number = 'whatsapp:+14155238886' 

# O SEU número (que você usou para mandar "oi")
# Substitua pelo seu número se necessário, ou pegue do log anterior
to_whatsapp_number = 'whatsapp:+5511996861402' 

try:
    message = client.messages.create(
        body="Olá! Este é um teste direto do servidor do ELO. Se você recebeu isso, suas credenciais estão corretas!",
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )
    print(f"Mensagem enviada com sucesso! SID: {message.sid}")
except Exception as e:
    print(f"Erro ao enviar mensagem: {e}")
