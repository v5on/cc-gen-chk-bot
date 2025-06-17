# handlers/gpt_handler.py
import requests

def register(bot):
    @bot.message_handler(commands=["gpt"])
    def handle_gpt(message):
        args = message.text.partition(" ")[2].strip()
        if not args:
            bot.reply_to(message, "অনুগ্রহ করে প্রশ্ন লিখুন। উদাহরণ: /gpt তোমার প্রশ্ন")
            return

        try:
            # প্রথমে কাস্টম API URL নিতে হবে
            api_list_url = "https://raw.githubusercontent.com/MOHAMMAD-NAYAN-07/Nayan/main/api.json"
            res = requests.get(api_list_url, timeout=10)
            res.raise_for_status()
            api_base = res.json().get("api")
            if not api_base:
                bot.reply_to(message, "API URL পাওয়া যায়নি।")
                return

            # এখন তোমার প্রশ্ন পাঠাও কাস্টম API তে
            gpt_url = f"{api_base}/nayan/gpt3?prompt={requests.utils.quote(args)}"
            gpt_res = requests.get(gpt_url, timeout=15)
            gpt_res.raise_for_status()
            data = gpt_res.json()

            reply_text = data.get("response") or "দুঃখিত, আমি আপনার প্রশ্নটি বুঝতে পারিনি।"
            bot.reply_to(message, reply_text)

        except Exception as e:
            bot.reply_to(message, f"API ত্রুটি: {str(e)}")
