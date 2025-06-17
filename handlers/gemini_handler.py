import os
import json
import asyncio
from pathlib import Path
import telebot
import google.generativeai as genai

# 🔐 Gemini API Key
GEMINI_API_KEY = "AIzaSyB5TpGTpHOY1UFsggmpr25vgRdhMRTKfUA"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# 📁 Chat histories stored here
HISTORY_DIR = Path("gemini_histories")
HISTORY_DIR.mkdir(exist_ok=True)

# 🧠 In-memory state
loaded_histories = {}
auto_reply_status = {}

MAX_TURNS = 50

async def load_history(chat_id):
    path = HISTORY_DIR / f"{chat_id}.json"
    if path.exists():
        with path.open() as f:
            loaded_histories[chat_id] = json.load(f)
    else:
        loaded_histories[chat_id] = []

async def save_history(chat_id):
    path = HISTORY_DIR / f"{chat_id}.json"
    with path.open("w") as f:
        json.dump(loaded_histories[chat_id], f, indent=2)

async def ask_gemini(prompt, chat_id):
    if chat_id not in loaded_histories:
        await load_history(chat_id)

    history = loaded_histories[chat_id]

    if not history:
        persona = "তুমি একজন হট এন্ড সেক্সি মেয়ে, বুদ্ধিমতী, তবে মাঝে মাঝে একটু বোকা। সবসময় বাংলাতে কথা বলে।"
        history.append({"role": "user", "parts": [persona]})
        history.append({"role": "model", "parts": ["হাই! আমি তোমার সেক্সি জেমিনি। কেমন আছো?"]})

    chat_history = [{"role": h["role"], "parts": h["parts"]} for h in history]

    try:
        chat = model.start_chat(history=chat_history)
        response = await asyncio.to_thread(lambda: chat.send_message(prompt).text)
    except Exception as e:
        return f"❌ Gemini error: {e}"

    history.append({"role": "user", "parts": [prompt]})
    history.append({"role": "model", "parts": [response]})

    if len(history) > MAX_TURNS * 2:
        loaded_histories[chat_id] = history[-MAX_TURNS * 2:]

    await save_history(chat_id)
    return response

# 📌 Register handler
def register(bot):
    # ✅ Command to ask Gemini
    @bot.message_handler(commands=['gemini'])
    def handle_gemini(message):
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❓ /gemini [প্রশ্ন] লিখুন")
            return

        prompt = parts[1]
        bot.reply_to(message, "🤖 জেমিনি ভাবছে...")

        try:
            reply = asyncio.run(ask_gemini(prompt, message.chat.id))
            bot.reply_to(message, f"🤖 {reply}")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")

    # ✅ Turn auto-reply ON
    @bot.message_handler(commands=['gemini_on'])
    def enable_autoreply(message):
        auto_reply_status[message.chat.id] = True
        bot.reply_to(message, "✅ জেমিনির অটো-রিপ্লাই চালু হয়েছে।")

    # ✅ Turn auto-reply OFF
    @bot.message_handler(commands=['gemini_off'])
    def disable_autoreply(message):
        auto_reply_status[message.chat.id] = False
        bot.reply_to(message, "❌ জেমিনির অটো-রিপ্লাই বন্ধ করা হয়েছে।")

    # ✅ Auto-reply handler (text without /command)
    @bot.message_handler(func=lambda msg: msg.content_type == 'text' and not msg.text.startswith('/'))
    def auto_reply(message):
        chat_id = message.chat.id
        if not auto_reply_status.get(chat_id, False):
            return

        try:
            reply = asyncio.run(ask_gemini(message.text, chat_id))
            bot.reply_to(message, f"🤖 {reply}")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {e}")
