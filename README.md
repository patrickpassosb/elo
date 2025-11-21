# ELO - WhatsApp Chatbot

ELO is a WhatsApp chatbot designed to help elderly people and those with reading difficulties understand documents, laws, and complex texts. It acts as a patient, welcoming "Digital Grandson" (Neto Digital).

## Features

- 📱 **WhatsApp Integration** via Twilio
- 🎤 **Audio Messages** - Transcription with OpenAI Whisper
- 🖼️ **Image Recognition** - Document analysis with GPT-4o Vision
- 🔊 **Text-to-Speech** - Audio responses with OpenAI TTS
- 💬 **Conversation Memory** - Context-aware responses using LangChain
- 🌐 **Ngrok Tunnel** - Easy local development setup

## Tech Stack

- **FastAPI** - Web framework
- **Twilio** - WhatsApp messaging
- **OpenAI** - GPT-4o, Whisper, TTS
- **LangChain** - Conversation memory
- **Ngrok** - Public URL tunneling

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `TWILIO_ACCOUNT_SID` - From Twilio Console
- `TWILIO_AUTH_TOKEN` - From Twilio Console
- `OPENAI_API_KEY` - From OpenAI Platform
- `NGROK_AUTHTOKEN` - From Ngrok Dashboard
- `BASE_URL` - Your Ngrok public URL (update after starting tunnel)

### 3. Start the Server

```bash
# Terminal 1: Start FastAPI server
uv run uvicorn app:app --reload

# Terminal 2: Start Ngrok tunnel
uv run expose_server.py
```

### 4. Configure Twilio Webhook

1. Copy the webhook URL from the Ngrok output (e.g., `https://abc123.ngrok.io/webhook`)
2. Go to Twilio Console → WhatsApp Sandbox Settings
3. Set "When a message comes in" to your webhook URL
4. Update `BASE_URL` in `.env` with your Ngrok URL

## Usage

Send messages to your Twilio WhatsApp Sandbox number:

- **Text** - Ask questions, get explanations
- **Audio** - Send voice messages (bot responds with audio)
- **Image** - Send photos of documents for analysis

## Project Structure

```
elo/
├── app.py              # FastAPI webhook endpoint
├── brain.py            # LangChain conversation logic
├── utils.py            # OpenAI utilities (Whisper, TTS, Vision)
├── expose_server.py    # Ngrok tunnel setup
├── check_status.py     # Twilio message status checker
├── test_twilio.py      # Send test messages
└── media/              # Generated audio files (gitignored)
```

## Development

### Testing Twilio Integration

```bash
# Send a test message
uv run test_twilio.py

# Check message status
uv run check_status.py <MESSAGE_SID>
```

## Notes

- This is a prototype/hackathon project
- Conversation history is stored in-memory (lost on restart)
- Media files accumulate in `media/` folder
- Not production-ready (see security and scalability considerations)

## License

MIT
