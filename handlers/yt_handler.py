import os
import re
import requests
from telebot import TeleBot
from telebot.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

# === APIs ===
SEARCH_API = "https://smartytdl.vercel.app/search?q="
DOWNLOAD_API = "https://smartytdl.vercel.app/dl?url="

# === Store user-specific data ===
user_search_results = {}
user_sent_messages = {}

# === File download with progress ===
def download_file(url, filename, bot=None, chat_id=None):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        with open(filename, "wb") as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if bot and chat_id and total_size > 0:
                        percent = (downloaded * 100) // total_size
                        try:
                            bot.send_chat_action(chat_id, 'upload_document')
                        except:
                            pass

# === Bot Command Register ===
def register(bot: TeleBot):

    @bot.message_handler(commands=["yt"])
    def yt_command(message: Message):
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            bot.reply_to(message, "দয়া করে ইউটিউব সার্চ করার জন্য কিছু লিখুন।\nUsage: /yt <search>")
            return

        query = args[1]
        resp = requests.get(SEARCH_API + query)
        data = resp.json()

        if "result" not in data or not data["result"]:
            bot.reply_to(message, "❌ কোনো রেজাল্ট পাওয়া যায়নি।")
            return

        results = data["result"][:10]
        user_search_results[message.chat.id] = results

        msg_text = "🔍 সার্চ রেজাল্ট:\n\n"
        for i, video in enumerate(results):
            title = re.sub(r'[\\/:*?"<>|]', '', video["title"])
            duration = video.get("duration", "Unknown")
            msg_text += f"[{i+1}] 🕒 {duration} | {title}\n"

        markup = InlineKeyboardMarkup(row_width=5)
        buttons = [InlineKeyboardButton(str(i+1), callback_data=f"select_{i}") for i in range(len(results))]
        markup.add(*buttons)
        bot.send_message(message.chat.id, msg_text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
    def handle_select(call: CallbackQuery):
        idx = int(call.data.split("_")[1])
        chat_id = call.message.chat.id

        if chat_id not in user_search_results:
            bot.answer_callback_query(call.id, "Session expired. Please search again.")
            return

        video = user_search_results[chat_id][idx]
        title = re.sub(r'[\\/:*?"<>|]', '', video["title"])
        duration = video.get("duration", "Unknown")
        thumb_url = video.get("imageUrl")

        caption = f"🕒 {duration}\n{title}"
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎵 অডিও", callback_data=f"download_{idx}_audio"),
            InlineKeyboardButton("🎬 ভিডিও", callback_data=f"download_{idx}_video")
        )

        sent_msg = bot.send_photo(chat_id, photo=thumb_url, caption=caption, reply_markup=markup)

        # Track all sent message ids per user
        if chat_id not in user_sent_messages:
            user_sent_messages[chat_id] = []
        user_sent_messages[chat_id].append(sent_msg.message_id)

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
    def handle_download(call: CallbackQuery):
        parts = call.data.split("_")
        idx = int(parts[1])
        choice = parts[2]
        chat_id = call.message.chat.id

        if chat_id not in user_search_results:
            bot.answer_callback_query(call.id, "Session expired. Please search again.")
            return

        # ❌ Delete all previous result thumbnails/messages
        for msg_id in user_sent_messages.get(chat_id, []):
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
        user_sent_messages[chat_id] = []

        video = user_search_results[chat_id][idx]
        title = re.sub(r'[\\/:*?"<>|]', '', video["title"])
        link = video["link"]
        ext = "mp4" if choice == "video" else "m4a"
        filename = f"downloads/{title}.{ext}"

        wait_msg = bot.send_message(chat_id, f"📥 '{title}' ডাউনলোড হচ্ছে... অপেক্ষা করুন")

        try:
            res = requests.get(DOWNLOAD_API + link)
            ddata = res.json()

            if not ddata.get("success"):
                bot.send_message(chat_id, "❌ ডাউনলোড লিঙ্ক পাওয়া যায়নি।")
                return

            medias = ddata.get("medias", [])
            media_url = None

            for media in medias:
                if media["type"] == choice:
                    if choice == "video" and "480" in media.get("quality", ""):
                        media_url = media["url"]
                        break
                    elif choice == "audio":
                        media_url = media["url"]
                        break

            if not media_url:
                bot.send_message(chat_id, f"❌ {choice.upper()} ফরম্যাট পাওয়া যায়নি।")
                return

            os.makedirs("downloads", exist_ok=True)
            download_file(media_url, filename, bot, chat_id)

            with open(filename, "rb") as f:
                if choice == "audio":
                    bot.send_audio(chat_id, f, caption=f"✅ ডাউনলোড সম্পন্ন:\n{title}")
                else:
                    bot.send_video(chat_id, f, caption=f"✅ ডাউনলোড সম্পন্ন:\n{title}")

            os.remove(filename)
            bot.delete_message(chat_id, wait_msg.message_id)

        except Exception as e:
            bot.send_message(chat_id, f"⚠️ সমস্যা হয়েছে:\n{str(e)}")
            try:
                bot.delete_message(chat_id, wait_msg.message_id)
            except:
                pass
