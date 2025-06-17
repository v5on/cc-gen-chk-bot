import os
import requests
from moviepy.editor import VideoFileClip

VIDEO_PATH = "temp_video.mp4"
RESIZED_VIDEO_PATH = "temp_video_resized.mp4"
AUDIO_PATH = "output_audio.mp3"

MAX_FILE_SIZE_MB = 50
MAX_DURATION = 60  # seconds

def cleanup_files():
    for file in [VIDEO_PATH, RESIZED_VIDEO_PATH, AUDIO_PATH]:
        if os.path.exists(file):
            os.remove(file)

def register(bot):
    @bot.message_handler(commands=['convert'])
    def convert_handler(message):
        try:
            # ভিডিও ফাইলের URL বা reply থেকে ফাইল লিংক নেওয়া
            if message.reply_to_message and message.reply_to_message.video:
                file_id = message.reply_to_message.video.file_id
                file_info = bot.get_file(file_id)
                file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
            else:
                args = message.text.split(maxsplit=1)
                if len(args) < 2:
                    bot.reply_to(message, "ভিডিও ফাইল রিপ্লাই করো অথবা `/convert [ভিডিও URL]` লিখে পাঠাও।")
                    return
                file_url = args[1]

            bot.reply_to(message, "ভিডিও ডাউনলোড করা হচ্ছে, অপেক্ষা করুন...")

            # ভিডিও ডাউনলোড
            r = requests.get(file_url, stream=True)
            r.raise_for_status()
            with open(VIDEO_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            clip = VideoFileClip(VIDEO_PATH)

            # ডিউরেশন চেক, প্রয়োজনে কাটা
            if clip.duration > MAX_DURATION:
                clip = clip.subclip(0, MAX_DURATION)

            # রিসাইজ, শুধু হাইট ফিক্স করে রাখবো, প্রপোরশনাল রিসাইজ
            clip = clip.resize(height=480)

            # ভিডিও রিসাইজ ফাইল সেভ করা
            clip.write_videofile(RESIZED_VIDEO_PATH, codec='libx264', audio_codec='aac', verbose=False, logger=None)

            # নতুন ভিডিও থেকে অডিও বের করা
            clip_resized = VideoFileClip(RESIZED_VIDEO_PATH)
            clip_resized.audio.write_audiofile(AUDIO_PATH, bitrate="64k", verbose=False, logger=None)

            audio_size_mb = os.path.getsize(AUDIO_PATH) / (1024 * 1024)
            if audio_size_mb > MAX_FILE_SIZE_MB:
                bot.reply_to(message, f"ফাইল সাইজ {audio_size_mb:.2f}MB, যা অনুমোদিত সাইজ ({MAX_FILE_SIZE_MB}MB) এর বেশি। ছোট ভিডিও ব্যবহার করুন।")
                cleanup_files()
                return

            with open(AUDIO_PATH, "rb") as audio_file:
                bot.send_audio(message.chat.id, audio_file, caption="🎵 ভিডিও থেকে কনভার্ট করা অডিও।")

            cleanup_files()

        except Exception as e:
            bot.reply_to(message, f"❌ এরর হয়েছে: {str(e)}")
            cleanup_files()
