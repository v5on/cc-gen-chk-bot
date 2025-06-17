import os
import aiohttp
import aiofiles
import json
from telebot.types import Message, InputMediaPhoto  # ✅ ঠিকভাবে ইমপোর্ট

os.makedirs("cache", exist_ok=True)

async def download_image(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(path, mode='wb')
                await f.write(await resp.read())
                await f.close()

def register(bot):
    @bot.message_handler(commands=["imagine"])
    def handle_imagine(message: Message):
        import asyncio

        prompt = message.text.split(" ", 1)
        if len(prompt) < 2:
            bot.reply_to(message, "❌ Prompt missing. উদাহরণ: /imagine cat with sunglasses")
            return

        search_prompt = prompt[1].strip()
        bot.reply_to(message, "🧠 Generating image(s), please wait...")

        async def process():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://raw.githubusercontent.com/MOHAMMAD-NAYAN-07/Nayan/main/api.json") as resp:
                        text = await resp.text()
                        apidata = json.loads(text)
                        api_base = apidata["api"]
                        image_api = f"{api_base}/nayan/img?prompt={search_prompt}"

                    async with session.get(image_api) as img_resp:
                        res = await img_resp.json()
                        images = res.get("imageUrls", [])

                        if not images:
                            await bot.send_message(message.chat.id, "❌ কোনো ছবি পাওয়া যায়নি।")
                            return

                        photo_files = []
                        for idx, url in enumerate(images):
                            filename = f"temp_{idx}.jpg"
                            path = os.path.join("cache", filename)
                            await download_image(url, path)
                            photo_files.append(open(path, 'rb'))

                        # ✅ এখন এখানে InputMediaPhoto সোজা ব্যবহার করা হচ্ছে
                        bot.send_media_group(
                            message.chat.id,
                            [InputMediaPhoto(p) for p in photo_files]
                        )

                        for file in photo_files:
                            file.close()
                            os.remove(file.name)

            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Error: {e}")

        asyncio.run(process())
