import requests
import random
from telebot.types import Message

API_URL = "https://api.npoint.io/ad402f70ec811202c7b7"

def register(bot):
    @bot.message_handler(commands=["fake"])
    def handle_fake(message: Message):
        args = message.text.split(" ", 1)
        if len(args) < 2:
            bot.reply_to(message, "❌ Country name missing. উদাহরণ: <code>/fake US</code>, <code>/fake algeria</code>, <code>/fake kzt</code>")
            return

        country_input = args[1].strip().lower()

        try:
            response = requests.get(API_URL)
            if response.status_code != 200:
                bot.send_message(message.chat.id, "❌ Failed to fetch address database.")
                return

            address_data = response.json()

            matched_country = next((c for c in address_data if c.lower() == country_input), None)

            if not matched_country:
                bot.reply_to(message, "❌ Country not found in database.")
                return

            address = random.choice(address_data[matched_country])

            username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

            msg = (
                f"<b>Address for {matched_country}</b>\n"
                f"•{'━'*10}•\n"
                f"𝗦𝘁𝗿𝗲𝗲𝘁 𝗔𝗱𝗱𝗿𝗲𝘀𝘀: <code>{address.get('street', 'N/A')}</code>\n"
                f"𝗖𝗶𝘁𝘆: <code>{address.get('city', 'N/A')}</code>\n"
                f"𝗦𝘁𝗮𝘁𝗲: <code>{address.get('state', 'N/A')}</code>\n"
                f"𝗣𝗼𝘀𝘁𝗮𝗹 𝗖𝗼𝗱𝗲: <code>{address.get('postal_code', 'N/A')}</code>\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: <code>{address.get('country', matched_country)}</code>\n"
                f"•{'━'*10}•\n"
                f"Requested by: {username}"
            )

            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {str(e)}")


    @bot.message_handler(commands=["country"])
    def handle_country_list(message: Message):
        try:
            response = requests.get(API_URL)
            if response.status_code != 200:
                bot.send_message(message.chat.id, "❌ Failed to fetch country list.")
                return

            data = response.json()
            country_list = sorted(data.keys())

            country_text = "\n".join([f"• {name}" for name in country_list])
            msg = (
                "<b>✅ Available Countries</b>\n"
                f"{'━'*24}\n"
                f"{country_text}\n"
                f"{'━'*24}\n"
                "⚠️ Use exactly as shown. উদাহরণ: <code>/fake US</code>"
            )

            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
