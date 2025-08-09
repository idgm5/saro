# Saro - The Sarcastic Genius Chatbot 🤖✨

**Saro** is a personal AI chatbot powered by **Llama 4**, running **locally** on your own hardware — no external APIs required.

She's witty, sarcastic, playful, multilingual, and talks directly on **Telegram**!

---

## 🚀 Features

- 🧑‍🔬 Built with Llama 4 (Llama-4-Scout-17B-16E-Instruct-UD-Q3_K_XL) via llama.cpp
- 🔥 Runs locally with CUDA acceleration (RTX 3090 Ti setup)
- 🔐 No API keys required (only Telegram Bot Token)
- 👤 Multi-language sarcasm (detects Spanish, French, Japanese, etc.)
- 🧹 Message auto-splitting (fits Telegram's 4096 character limit)
- 🛡️ Secure token management via dotenv
- 📊 Full system logging for events and errors
- 🎝️ Dynamic prodigy girl personality (adaptive, sarcastic, fun)
- 🗣️ Every text reply is also spoken using realistic voice synthesis (gTTS), sent as a Telegram voice message.

---

## 📦 Tech Stack

| Technology | Usage |
| :--- | :--- |
| Llama.cpp | Local AI inference (GPU accelerated) |
| Python 3.11 | Bot backend |
| python-telegram-bot | Telegram Bot API |
| requests | Communication with Llama server |
| python-dotenv | Environment variable management |
| langdetect | Detects input language |
| TTS | Text-to-Speech |
| pydub | audio conversion |

---

## ⚙️ How to Setup Saro

### 1. Clone the repo

```bash
git clone https://github.com/idgm5/saro.git
cd sarcasticbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

_(Python 3.13 recommended)_

---

### 3. Create `.env` file

At the project root, create a file `.env` and add your Telegram token:

```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
```

_(Make sure `.env` is listed in your `.gitignore`!)_

---

### 4. Launch the Llama Server

```bash
.\build\bin\Release\llama-server.exe --model "models\Llama-4-Scout-17B-16E-Instruct-UD-Q3_K_XL.gguf" --n-gpu-layers 32 --ctx-size 4096 --threads 12
```

This will start the local HTTP server where Saro will send requests.

---

### 5. Start the Bot

```bash
py -3.11 bot.py
```

👉️ Saro is now alive on Telegram and ready to talk (or roast you).

---

## 🧐 Why Saro?

- **Privacy:** No outside APIs, total local control.
- **Speed:** GPU-accelerated fast replies.
- **Fun:** Witty, sarcastic, and multilingual.
- **Customization:** Fully open source, easily extendable.

---

## 🛡️ License

**For personal/local use only.**  
Respect Meta's license for Llama models.

---

## ✨ Credits

- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Thanks to the open-source LLM community!

---

## 📊 Planned Features

- Persistent memory (remember user facts across chats)
- Local network/mobile access
- Better multilingual tone adjustment

---

> "Saro isn't just smart — she's smarter **than you**, and she'll make sure you know it."
