import os
import uuid
import subprocess
from flask import Flask, request
import telebot
from dotenv import load_dotenv

# ===============================
# 🌍 Load Environment Variables
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please set it in your .env file.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===============================
# 📁 Directory Setup
# ===============================
INPUT_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SCRIPT_PATH = os.path.join(BASE_DIR, "video_dubber_plus.py")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

user_sessions = {}

# ===============================
# 🤖 Bot Commands
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

@bot.message_handler(func=lambda msg: msg.text.strip() in ["1", "2", "3"])
def handle_language_choice(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        bot.reply_to(message, "⚠️ Please send a video first.")
        return

    lang_map = {"1": "en", "2": "ar", "3": "fa"}
    lang_code = lang_map[message.text.strip()]
    video_path = user_sessions[chat_id]["video_path"]
    output_path = os.path.join(OUTPUT_DIR, f"dubbed_{uuid.uuid4()}.mp4")

    bot.reply_to(
        message,
        f"🌐 You chose *{lang_code}*. Processing your video... ⏳",
        parse_mode="Markdown"
    )

    try:
        result = subprocess.run(
            ["python", SCRIPT_PATH, video_path, output_path, lang_code],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if os.path.exists(output_path):
            with open(output_path, "rb") as vid:
                bot.send_video(chat_id, vid, caption="🎬 Here's your dubbed video!")
            # ✅ Cleanup user session after success
            user_sessions.pop(chat_id, None)
        else:
            bot.reply_to(message, "⚠️ Dubbed video not found. Something went wrong.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ===============================
# 🌐 Flask Webhook Routes
# ===============================
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    json_str = request.stream.read().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "🤖 Nazilal Dubs Bot is live with webhook mode!"

# ===============================
# 🚀 Main Entry Point
# ===============================
if __name__ == '__main__':
    render_host = os.getenv("RENDER_EXTERNAL_URL", "<your-render-app-name>.onrender.com")
    if not render_host.startswith("https://"):
        render_host = f"https://{render_host}"
    render_url = f"{render_host}/{BOT_TOKEN}"

    bot.remove_webhook()
    bot.set_webhook(url=render_url)

    # ✅ Confirm webhook status
    set_status = bot.get_webhook_info()
    print(f"✅ Webhook active: {set_status.url}")

    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Flask server running on port {port}")
    app.run(host='0.0.0.0', port=port)
