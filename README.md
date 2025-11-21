# 🤖 ELO - O Assistente Cidadão

**Hackathon: Devs de Impacto 2025 (Powered by OpenAI)**

## 📖 Sobre o Projeto

ELO é um chatbot inteligente que atua como um "Neto Digital", ajudando cidadãos (especialmente idosos) a entenderem documentos complexos, leis e cartas de forma simples e acessível.

### 🎯 Problema que Resolvemos

- **Abismo da Compreensão**: 88% da população brasileira tem dificuldade com textos complexos
- **Exclusão Digital**: Necessidade de soluções acessíveis via celular, sem apps pesados
- **Burocracia Incompreensível**: Documentos governamentais e jurídicos em linguagem difícil

### 💡 Nossa Solução

Um assistente conversacional no **Telegram** que:
- ✅ Aceita **áudio, texto e fotos**
- ✅ Responde em **áudio ou texto** (conforme preferência do usuário)
- ✅ Explica documentos de forma **simples e acolhedora**
- ✅ Mantém **contexto da conversa** (memória)
- ✅ **100% acessível** - sem barreiras geográficas ou de verificação

## 🚀 Como Usar

### Para Usuários Finais

1. **Abra o Telegram** no seu celular ou computador
2. **Procure pelo bot**: `@EloBot` (ou use o link que compartilhamos)
3. **Inicie a conversa**: Clique em "Start" ou envie `/start`
4. **Interaja**:
   - 📝 Mande uma mensagem de texto
   - 🎤 Grave um áudio (o bot responderá com áudio!)
   - 📷 Tire uma foto de uma carta/conta/documento

### Exemplos de Uso

**Texto:**
```
Você: "Me explica o que é IPTU"
ELO: "IPTU é o Imposto Predial e Territorial Urbano, vó! É aquele imposto que você paga todo ano pela sua casa ou apartamento..."
```

**Foto de Documento:**
```
[Você envia foto de uma conta de luz]
ELO: "Essa é sua conta de luz! O valor a pagar é R$ 150,00 e vence dia 25. Aquele número grande lá em cima é só o consumo em kWh, não precisa se preocupar com ele..."
```

**Áudio:**
```
[Você grava: "Oi, recebi uma carta do banco, tô preocupado"]
ELO: [Responde com áudio] "Oi! Tira uma foto dessa carta e me manda que eu leio pra você e explico se é algo importante..."
```

## 🛠️ Stack Tecnológica

- **Framework**: FastAPI + python-telegram-bot
- **IA Multimodal**: OpenAI GPT-4o (texto + visão)
- **Transcrição de Áudio**: OpenAI Whisper
- **Síntese de Voz**: OpenAI TTS
- **Memória Conversacional**: LangChain
- **Gerenciador de Pacotes**: UV (moderno e rápido)

## 📱 Compartilhando com a Equipe

### Opção 1: Link Direto (Mais Fácil)

Envie este link para seus colegas:
```
https://t.me/SeuBotUsername
```
*(Substitua `SeuBotUsername` pelo username que você escolheu no @BotFather)*

### Opção 2: Username

Peça para procurarem por: `@SeuBotUsername` no Telegram

### Opção 3: QR Code

1. Abra o bot no Telegram
2. Clique nos 3 pontinhos (⋮)
3. Selecione "Share"
4. Escolha "QR Code"
5. Mostre o QR Code para sua equipe escanear

## 🏗️ Para Desenvolvedores

### Pré-requisitos

- Python 3.11+
- UV (gerenciador de pacotes)
- Conta OpenAI com créditos
- Bot do Telegram (criado via @BotFather)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/elo.git
cd elo

# Instale as dependências
uv sync

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves
```

### Configuração

Crie um arquivo `.env` com:

```env
OPENAI_API_KEY=sk-...
TELEGRAM_TOKEN=123456789:ABC...
```

### Executando

```bash
# Versão Telegram (recomendado)
uv run telegram_app.py

# Versão WhatsApp (branch master - requer Twilio)
git checkout master
uv run uvicorn app:app --reload
```

## 🏆 Diferenciais do Projeto

1. **Acessibilidade Total**: Áudio-in/Áudio-out para pessoas com dificuldade de leitura
2. **Visão Computacional**: Lê documentos em fotos usando GPT-4o Vision
3. **Persona Humanizada**: "Neto Digital" - linguagem acolhedora e simples
4. **Memória Contextual**: Lembra da conversa anterior
5. **Zero Barreiras**: Funciona no Telegram sem restrições geográficas

## 📊 Arquitetura

```
┌─────────────┐
│  Telegram   │
│   (Input)   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  telegram_app   │ ◄── Orquestração
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────┐
│ utils  │ │brain │
│(OpenAI)│ │(Lang │
│        │ │Chain)│
└────────┘ └──────┘
```

## 🎨 Persona: "Neto Digital"

O ELO foi projetado para ser:
- 💙 **Acolhedor**: Trata o usuário com carinho ("vó", "vô")
- 🗣️ **Simples**: Evita juridiquês e termos técnicos
- 🎯 **Direto**: Respostas curtas e objetivas
- 🤝 **Prestativo**: Sempre pergunta se a pessoa entendeu

## 📝 Licença

MIT License - Sinta-se livre para usar e modificar!

## 👥 Equipe

[Adicione os nomes da sua equipe aqui]

## 🙏 Agradecimentos

- OpenAI pelo patrocínio do Hackathon
- Organizadores do "Devs de Impacto 2025"
- Comunidade open-source

---

**Feito com ❤️ para democratizar o acesso à informação**
