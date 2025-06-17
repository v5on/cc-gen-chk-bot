import re
import os
import yt_dlp
from telebot import TeleBot
from telebot.types import Message

video_url_pattern = re.compile(r'(https?://[^\s]+)')

def download_video(url: str, output_path: str = "downloads/video.mp4"):
    ydl_opts = {
        "outtmpl": output_path,
        "format": "mp4",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

def register(bot: TeleBot):
    @bot.message_handler(commands=["download"])
    def handle_download(message: Message):
        urls = video_url_pattern.findall(message.text)
        if not urls:
            bot.reply_to(message, "⚠️ ভিডিওর লিংক দিন।")
            return

        url = urls[0]
        bot.reply_to(message, "📥 ডাউনলোড হচ্ছে...")

        try:
            os.makedirs("downloads", exist_ok=True)
            file_path = download_video(url)
            with open(file_path, "rb") as video_file:
                bot.send_video(message.chat.id, video_file, caption="✅ ভিডিও ডাউনলোড সফল")
            os.remove(file_path)
        except Exception as e:
            bot.reply_to(message, f"❌ ডাউনলোডে সমস্যা হয়েছে:\n`{str(e)}`")
