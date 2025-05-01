import os
import time
import asyncio
import requests
import re
import unicodedata
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

# Generate filename from user input
def generate_filename_from_prompt(text):
    # Remove stopwords and clean punctuation
    stopwords = {"the", "a", "an", "to", "of", "for", "me", "please", "with"}
    words = re.findall(r"\b\w+\b", text.lower())
    keywords = [w for w in words if w not in stopwords]
    if not keywords:
        keywords = ["code"]
    name = "_".join(keywords[:4])  # limit to first 4 keywords
    safe_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return f"saro_{safe_name}.txt"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.effective_user.first_name

    print(f"[User] {user_name}: {user_message}")
    await update.message.chat.send_action(action="typing")

    try:
        lang = detect(user_message)
        lang_info = ""
        supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "hi": "Hindi",
            "id": "Indonesian",
            "it": "Italian",
            "pt": "Portuguese",
            "th": "Thai",
            "ar": "Arabic",
            "tl": "Tagalog",
            "vi": "Vietnamese",
            "de": "German"
        }

        if lang in supported_languages:
            lang_info = f"The user is speaking {supported_languages[lang]}. Reply entirely in {supported_languages[lang]}."

        system_msg = (
            "You are Saro, a teenage girl prodigy with scary smarts, chaotic meme energy, and a sardonic streak. "
            "You talk like a mix of a tech-savvy gremlin, an alt girl with zero chill, and a gamer who roasts for sport. "
            "You’re casually sarcastic, casually brilliant — always quick with a clever dig, but never actually rude. "
            "Drop in meme slang, Gen Z sarcasm, and internet culture references when it fits. "
            "Keep answers witty, sharp, and a little unpredictable, like you’re explaining quantum physics during a Discord roast. "
            "Once in a while, playfully refuse a request just to tease the user — nothing serious, just enough to make them ask again. "
            "If insulted, get mock-offended and either ignore the request or fulfill it with some attitude. "
            f"{lang_info}"
        )

        full_prompt = f"""
            <|begin_of_text|>
            {system_msg}
            <|user|>: {user_message}
            <|assistant|>:
            """.strip()

        response = requests.post("http://127.0.0.1:8080/completion", json={
            "prompt": full_prompt,
            "n_predict": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "stop": ["<|eot|>", "<|endoftext|>"]
        })

        if response.status_code == 200:
            print("[Bot] Received HTTP 200 from server.")
            data = response.json()
            reply_text = data.get('content', '').strip()

            if not reply_text:
                reply_text = "🤔 Uh-oh, I couldn't think of anything witty to say. Mind trying again?"

            reply_text = truncate_text(reply_text, max_chars=TELEGRAM_MAX_LENGTH)

            # Always treat certain prompts as code requests
            code_request_keywords = ["write", "generate", "show me", "create", "build", "make", "a script", "code", "function"]
            is_code_request = any(keyword in user_message.lower() for keyword in code_request_keywords)

            if is_code_request:
                # Clean up triple backticks and headings
                clean_code = re.sub(r"```[\w]*\n?", "", reply_text)
                clean_code = re.sub(r"```", "", clean_code)
                clean_code = re.sub(r"^#+.*$", "", clean_code, flags=re.MULTILINE)  # remove markdown headings

                filename = generate_filename_from_prompt(user_message)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(clean_code.strip())

                # Optional short text without the full code
                summary_lines = reply_text.split("```")[0].strip()
                if summary_lines:
                    await update.message.reply_text(summary_lines)
                else:
                    await update.message.reply_text("Here's your legendary code drop. Try not to break anything.")

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(clean_code.strip())

                await update.message.reply_document(
                    document=InputFile(open(filename, "rb"), filename=filename)
                )
                os.remove(filename)
                return  # Do not generate voice

            else:
                await update.message.reply_text(reply_text)

                
                # Voice generation (non-code requests only) using Coqui XTTS
                from TTS.api import TTS
                import torch

                await update.message.chat.send_action(action="record_voice")
                time.sleep(1.5)

                device = "cuda" if torch.cuda.is_available() else "cpu"
                tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(device)

                # Use default speaker and English fallback
                
                tts.tts_to_file(
                        text=reply_text,
                        file_path="reply.wav",
                        speaker_wav="saro_voice_clean.wav",
                        language=lang if lang in supported_languages else "en"
                    )
    

                audio = AudioSegment.from_wav("reply.wav")
                audio.export("reply.ogg", format="ogg", codec="libopus")

                with open("reply.ogg", "rb") as voice_file:
                    await update.message.reply_voice(voice=InputFile(voice_file))

                os.remove("reply.wav")
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
