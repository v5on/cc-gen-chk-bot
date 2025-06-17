import requests
from telebot.types import Message

def register(bot):
    @bot.message_handler(commands=["translate"])
    def translate_handler(message: Message):
        args = message.text.split(" ")[1:]  # exclude /translate command
        if not args and not message.reply_to_message:
            bot.reply_to(message, "❌ Usage: /translate <lang_code> <text> অথবা কোনো টেক্সটে রিপ্লাই দাও\nউদাহরণ: /translate fr Hello!")
            return

        # Detect target language and text
        if message.reply_to_message:
            text_to_translate = message.reply_to_message.text or ""
            target_lang = args[0] if args else "en"
        else:
            target_lang = args[0]
            text_to_translate = " ".join(args[1:])

        if not text_to_translate:
            bot.reply_to(message, "❌ অনুগ্রহ করে অনুবাদযোগ্য টেক্সট দিন।")
            return

        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": target_lang,
                "dt": "t",
                "q": text_to_translate
            }

            resp = requests.get(url, params=params)
            if resp.status_code != 200:
                bot.reply_to(message, f"❌ অনুবাদ ব্যর্থ হলো (status {resp.status_code})")
                return

            data = resp.json()

            translated = ''.join([item[0] for item in data[0] if item[0]])
            source_lang = data[2] if data[2] != data[8][0][0] else data[8][0][0]

            reply_msg = (
                f"✅ <b>Translation:</b> {translated}\n"
                f"🌐 <i>From {source_lang.upper()} to {target_lang.upper()}</i>"
            )
            bot.send_message(
                message.chat.id,
                reply_msg,
                reply_to_message_id=message.message_id,
                parse_mode="HTML"
            )

        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")
