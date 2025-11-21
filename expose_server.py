import os
import sys
from pyngrok import ngrok
from dotenv import load_dotenv

load_dotenv()

def start_tunnel():
    # Authenticate with Ngrok
    authtoken = os.getenv("NGROK_AUTHTOKEN")
    if authtoken:
        ngrok.set_auth_token(authtoken)
    else:
        print("WARNING: NGROK_AUTHTOKEN not found in .env. Tunnel might fail.")

    # Open a HTTP tunnel on the default port 8000
    # <NgrokTunnel: "https://<public_sub>.ngrok.io" -> "http://localhost:8000">
    public_url = ngrok.connect(8000).public_url
    print(f" * Ngrok Tunnel URL: {public_url}")
    print(f" * Webhook URL for Twilio: {public_url}/webhook")
    print(f" * Update your .env BASE_URL to: {public_url}")
    
    # Keep the process alive
    try:
        # Block until CTRL-C
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
    except KeyboardInterrupt:
        print(" Shutting down tunnel...")
        ngrok.kill()

if __name__ == "__main__":
    start_tunnel()
