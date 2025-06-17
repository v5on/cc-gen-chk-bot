import os
import aiohttp
import aiofiles
from telebot.types import Message
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # For consistent results from langdetect

async def download_file(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(path, mode='wb')
                await f.write(await resp.read())
                await f.close()
            else:
                raise Exception(f"Failed to download file: HTTP {resp.status}")

def register(bot):
    @bot.message_handler(commands=["say"])
    def handle_say2(message: Message):
        import asyncio

        text = message.text.split(" ", 1)
        if len(text) < 2:
            bot.reply_to(message, "❌ Text missing! Usage: /say your text\nExample: /say Hello world")
            return

        content = text[1].strip()

        # অটো detect language
        try:
            lang_code = detect(content)
        except:
            lang_code = "en"  # ডিফল্ট ইংরেজি যদি detect না হয়

        allowed_langs = ["ru", "en", "ko", "ja", "tl", "bn", "si", "fr", "de", "es"]  # তুমি চাইলে বাড়াতে পারো

        if lang_code not in allowed_langs:
            lang_code = "en"  # fallback

        async def process():
            try:
                filename = f"tts_{message.chat.id}_{message.message_id}.mp3"
                filepath = os.path.join("cache", filename)

                tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={aiohttp.helpers.quote(content)}&tl={lang_code}&client=tw-ob"

                await download_file(tts_url, filepath)

                with open(filepath, "rb") as voice:
                    bot.send_voice(message.chat.id, voice, reply_to_message_id=message.message_id)

                os.remove(filepath)

            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Error occurred: {str(e)}")

        # সরাসরি asyncio.run() না দিয়ে শুধু রান করানো (মেসেজ ছাড়া)
        asyncio.run(process())
