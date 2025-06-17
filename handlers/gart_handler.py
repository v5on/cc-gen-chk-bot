
import os
import asyncio
import aiohttp
import aiofiles
import telebot
import re

async def generate_image(prompt, style="", amount=1):
    image_paths = []

    for i in range(min(amount, 4)):  # Max 4 images
        url = f"https://imggen-delta.vercel.app/?prompt={prompt}&style={style}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await res.json()
                image_url = data.get("url")

                if not image_url:
                    break

                async with session.get(image_url) as img_res:
                    img_bytes = await img_res.read()

                img_path = f"gart_result_{i+1}.png"
                async with aiofiles.open(img_path, mode='wb') as f:
                    await f.write(img_bytes)

                image_paths.append(img_path)

    return image_paths

def register(bot):
    @bot.message_handler(commands=['gart'])
    def gart_command(message):
        args = message.text.split()[1:]  # Remove the command itself
        
        if not args:
            bot.reply_to(message, "Please provide a prompt. Usage: /gart a cat .stl anime .cnt 2")
            return

        arg_string = " ".join(args)
        match = re.match(r"(.*?)(?:\s*\.stl\s*(.*?))?(?:\s*\.cnt\s*(\d+))?$", arg_string)

        prompt = match.group(1).strip() if match else ""
        style = match.group(2).strip() if match and match.group(2) else ""
        amount = int(match.group(3)) if match and match.group(3) else 1

        if not prompt:
            bot.reply_to(message, "Please provide a valid prompt.")
            return

        if amount > 4:
            amount = 4
            bot.reply_to(message, "You can generate a maximum of 4 images. Generating 4...")

        generating_msg = bot.reply_to(message, "Generating your image(s), please wait...")

        try:
            image_paths = asyncio.run(generate_image(prompt, style, amount))

            if not image_paths:
                bot.edit_message_text(
                    "Failed to generate images. Please try again later.",
                    chat_id=generating_msg.chat.id,
                    message_id=generating_msg.message_id
                )
                return

            # Send images one by one
            for path in image_paths:
                with open(path, 'rb') as f:
                    bot.send_photo(message.chat.id, f)

            # Edit the generating message with final result
            result_text = (
                f"🔍Imagine Result🔍\n\n📝Prompt: {prompt}\n" +
                (f"🎨Style: {style}\n" if style else "") +
                f"#️⃣Number of Images: {len(image_paths)}"
            )
            bot.edit_message_text(
                result_text,
                chat_id=generating_msg.chat.id,
                message_id=generating_msg.message_id
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Error generating images: {str(e)}")
        finally:
            # Clean up generated files
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
