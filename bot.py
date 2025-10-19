import telebot
import os
import subprocess
import uuid
import threading
from flask import Flask

# ===============================
# 🔐 Telegram Bot Token (Read from environment)
# ===============================
import telebot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ===============================
# 📁 Directory Setup
# ===============================
BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SCRIPT_PATH = os.path.join(BASE_DIR, "video_dubber_plus.py")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🌐 User Session Storage
user_sessions = {}

# ===============================
# 🤖 Start Command
# ===============================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Welcome to *Nazilal Dubs!*\n\n"
        "Send me a short video, and I’ll dub it into your chosen language.\n\n"
        "🌐 Available languages:\n"
        "1️⃣ English (en)\n"
        "2️⃣ Arabic (ar)\n"
        "3️⃣ Persian (fa)\n\n"
        "🎬 Send your video now!",
        parse_mode="Markdown"
    )

# ===============================
# 🎥 Handle Uploaded Video
# ===============================
@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.video.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    input_path = os.path.join(INPUT_DIR, f"{uuid.uuid4()}.mp4")
    with open(input_path, 'wb') as f:
        f.write(downloaded_file)

    user_sessions[chat_id] = {"video_path": input_path}
    bot.reply_to(
        message,
        "✅ Video received!\n\n"
        "Now choose your dubbing language:\n"
        "1️⃣ English (en)\n"
        "2️⃣ Arabic (ar)\n"
        "3️⃣ Persian (fa)\n\n"
        "Reply with 1, 2, or 3."
    )

# ===============================
# 🌐 Handle Language Choice
# ===============================
@bot.message_handler(func=lambda msg: msg.text in ["1", "2", "3"])
def handle_language_choice(message):
    chat_id = message.chat.id

    if chat_id not in user_sessions:
        bot.reply_to(message, "⚠️ Please send a video first.")
        return

    lang_map = {"1": "en", "2": "ar", "3": "fa"}
    lang_code = lang_map[message.text.strip()]
    video_path = user_sessions[chat_id]["video_path"]

    bot.reply_to(
        message,
        f"🌐 You chose *{lang_code}*. Processing your video... ⏳",
        parse_mode="Markdown"
    )

    # 🎬 Process video with chosen language
    output_path = os.path.join(OUTPUT_DIR, f"dubbed_{uuid.uuid4()}.mp4")

    try:
        subprocess.run(
            ["python", SCRIPT_PATH, video_path, output_path, lang_code],
            check=True
        )

        if os.path.exists(output_path):
            with open(output_path, "rb") as vid:
                bot.send_video(chat_id, vid, caption="🎬 Here's your dubbed video!")
        else:
            bot.reply_to(message, "⚠️ Dubbed video not found. Something went wrong.")

    except Exception as e:
        bot.reply_to(message, f"❌ Error while processing video: {e}")

# ===============================
# 🌍 Flask Keep-Alive Endpoint
# ===============================
@app.route('/')
def home():
    return "🤖 Bot is running and ready to dub your videos!"

# ===============================
# 🚀 Run Flask + Bot Together
# ===============================
def start_bot():
    print("🤖 Bot is running... Waiting for messages.")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=10000)
