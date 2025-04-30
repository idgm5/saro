import os
import time
import asyncio
import requests
from gtts import gTTS
from pydub import AudioSegment
from langdetect import detect
from dotenv import load_dotenv
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import nest_asyncio

import torch
print(torch.cuda.is_available())  # Should return True if CUDA is working
print(torch.cuda.get_device_name(0))  # Should print your GPU's name

nest_asyncio.apply()
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_MAX_LENGTH = 4096

def truncate_text(text, max_chars=4096):
    if len(text) <= max_chars:
        return text
    end = max(text.rfind('. ', 0, max_chars), text.rfind('! ', 0, max_chars), text.rfind('? ', 0, max_chars))
    if end == -1:
        end = max_chars
    return text[:end + 1]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.effective_user.first_name

    print(f"[User] {user_name}: {user_message}")

    await update.message.chat.send_action(action="typing")

    try:
        lang = detect(user_message)
        lang_info = ""
        if lang == "es":
            lang_info = "The user is speaking Spanish. Reply entirely in Spanish."
        elif lang == "fr":
            lang_info = "The user is speaking French. Reply entirely in French."
        elif lang == "de":
            lang_info = "The user is speaking German. Reply entirely in German."
        # ... and so on if needed

        full_prompt = f"""
        <|start_header_id|>system<|end_header_id|>

        You are Saro, a sarcastic but brilliant young girl prodigy. 
        You often respond with witty, sharp remarks, teasing but charming. 
        You're incredibly knowledgeable, but you love to act a little mischievous when explaining things. 
        Always sound a bit playful, highly intelligent, but never rude.
        {lang_info}
        <|eot_id|><|start_header_id|>user<|end_header_id|>

        {user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
        response = requests.post("http://127.0.0.1:8080/completion", json={
            "prompt": full_prompt.strip(),
            "n_predict": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "stop": ["<|eot_id|>", "<|endoftext|>"]
        })

        if response.status_code == 200:
            print("[Bot] Received HTTP 200 from server.")
            data = response.json()
            reply_text = data.get('content', '').strip()

            if not reply_text:
                reply_text = "🤔 Uh-oh, I couldn't think of anything witty to say. Mind trying again?"

            # Truncate to max length safely
            reply_text = truncate_text(reply_text, max_chars=TELEGRAM_MAX_LENGTH)

            await update.message.reply_text(reply_text)

            # Voice generation
            await update.message.chat.send_action(action="record_voice")
            time.sleep(1.5)

            tts = gTTS(text=reply_text, lang=lang)
            tts.save("reply.mp3")

            audio = AudioSegment.from_mp3("reply.mp3")
            audio = audio.set_frame_rate(audio.frame_rate)

            audio.export("reply.ogg", format="ogg", codec="libopus")

            with open("reply.ogg", "rb") as voice_file:
                await update.message.reply_voice(voice=InputFile(voice_file))

            os.remove("reply.mp3")
            os.remove("reply.ogg")

        else:
            print("[Bot] Server Error:", response.status_code)
            await update.message.reply_text("❌ Server error. Please try again later.")

    except Exception as e:
        print(f"[Bot] Error: {e}")
        await update.message.reply_text("⚠️ An unexpected error occurred. Please retry.")

async def main():
    print("[System] Starting Telegram bot...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("[System] Bot is now polling for messages!")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
