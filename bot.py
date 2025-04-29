import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from langdetect import detect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Now safely get your token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in .env file!")

# URL of the running llama-server
LLAMA_SERVER_URL = 'http://127.0.0.1:8080/completion'

# User memory to store user-specific facts
user_memory = {}

# Conversation memory for context
chat_memory = []

# Max characters allowed by Telegram
MAX_TELEGRAM_MESSAGE_LENGTH = 4000

# Function to split large replies
def split_message(text, limit=MAX_TELEGRAM_MESSAGE_LENGTH):
    parts = []
    while len(text) > limit:
        safe_text = text[:limit]
        # Prefer to split at the last period or exclamation/question mark
        cut_points = [safe_text.rfind("."), safe_text.rfind("!"), safe_text.rfind("?")]
        best_cut = max(cut_points)

        if best_cut != -1 and best_cut > 100:  # ensure not cutting too early
            split_point = best_cut + 1
        else:
            split_point = limit

        parts.append(text[:split_point].strip())
        text = text[split_point:].strip()

    if text:
        parts.append(text)
    return parts


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_first_name = update.effective_user.first_name or "User"
    print(f"[User] {user_first_name}: {user_message}")

    # Detect language
    try:
        detected_lang = detect(user_message)
    except Exception:
        detected_lang = 'en'

    print(f"[System] Detected language: {detected_lang}")

    # Initialize user memory if not present
    if user_first_name not in user_memory:
        user_memory[user_first_name] = []

    # Very basic preference detection
    preferences_keywords = ["like", "love", "hate", "prefer", "enjoy", "fan of"]
    lower_message = user_message.lower()
    for keyword in preferences_keywords:
        if keyword in lower_message:
            user_memory[user_first_name].append(user_message)
            print(f"[Memory] Stored preference for {user_first_name}: {user_message}")
            break

    # Save the user message
    chat_memory.append({"role": "user", "content": user_message})

    # Build system prompt
    system_message = f"You are Saro, a young genius girl with a sarcastic, witty, playful attitude. Always clever, funny, and confident. The user's name is {user_first_name}. Feel free to occasionally mention their name when replying in a sarcastic or playful way."

    # Add user memory if any
    user_facts = user_memory.get(user_first_name, [])
    if user_facts:
        system_message += " Here are some things you know about the user: "
        for fact in user_facts[-3:]:
            system_message += f"\"{fact}\". "

    # Adjust sarcasm style based on detected language
    if detected_lang != 'en':
        if detected_lang == 'es':
            system_message += " In Spanish, your sarcasm should be sharp but still friendly, like a witty teenager."
        elif detected_lang == 'fr':
            system_message += " In French, your sarcasm should be ironic and playful, sophisticated but not too mean."
        elif detected_lang == 'ja':
            system_message += " In Japanese, your sarcasm should be light and teasing, slightly mischievous but polite."
        else:
            system_message += f" In {detected_lang.upper()}, keep your sarcasm playful but not too harsh."

        system_message += f" Important: The user wrote in {detected_lang.upper()}. You MUST reply ONLY in {detected_lang.upper()}. Do NOT reply in English unless the user switches back."

    # Build conversation history
    memory_text = f"<|start_header_id|>system<|end_header_id|>\n\n{system_message}<|eot_id|>"
    for message in chat_memory:
        memory_text += f"<|start_header_id|>{message['role']}<|end_header_id|>\n\n{message['content']}<|eot_id|>"
    memory_text += "<|start_header_id|>assistant<|end_header_id|>\n\n"

    # Build payload
    payload = {
        "prompt": memory_text,
        "n_predict": 256,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["<|eot_id|>"]
    }

    print("[Bot] Sending request to Llama Server...")
    try:
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=120)
        if response.status_code == 200:
            print("[Bot] Received HTTP 200 from server.")
            result = response.json()
            reply_text = result.get("content", "").strip()

            if not reply_text:
                reply_text = "🤔 Uh-oh, Saro couldn't think of anything witty to say. Try poking her again."

            # Enforce Telegram limit
            if len(reply_text) > MAX_TELEGRAM_MESSAGE_LENGTH:
                print("[Bot] Reply too long, splitting...")
                messages = split_message(reply_text)
            else:
                messages = [reply_text]

            for part in messages:
                if part.strip():  # Avoid sending empty strings
                    print(f"[Bot] Typing and replying part: {part[:80]}...")
                    await update.message.chat.send_action(action="typing")
                    await asyncio.sleep(min(len(part) / 100, 3))  # simulate typing delay
                    await update.message.reply_text(part)

            # Save only the first 4096 characters to chat memory
            chat_memory.append({"role": "assistant", "content": reply_text[:4096]})

        else:
            print(f"[Bot] Error contacting llama server: HTTP {response.status_code}")
            await update.message.reply_text("❌ Server error. Please try again later.")
    except Exception as e:
        print(f"[Bot] Exception: {e}")
        await update.message.reply_text("❌ Server unreachable. Please make sure llama-server is running.")

async def main():
    print("[System] Starting Telegram bot...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("[System] Bot is now polling for messages!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
