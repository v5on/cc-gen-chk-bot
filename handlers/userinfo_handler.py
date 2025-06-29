import requests
from telebot.types import Message, InputFile
from io import BytesIO

def register(bot):
    def fetch_info(bot, message: Message, target_type: str):
        identifier = None
        args = message.text.split(maxsplit=1)

        # USER / BOT
        if target_type in ["user", "bot"]:
            if len(args) > 1:
                identifier = args[1].strip()
                if not identifier.startswith("@") and not identifier.isdigit():
                    identifier = "@" + identifier
            elif message.reply_to_message:
                user = message.reply_to_message.from_user or message.reply_to_message.forward_from
                if user:
                    identifier = f"@{user.username}" if user.username else str(user.id)
                else:
                    bot.reply_to(message, "❌ রিপ্লাই করা মেসেজ থেকে ইউজার পাওয়া যায়নি।")
                    return
            else:
                identifier = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)

        # GROUP
        elif target_type == "group":
            if message.chat.type in ["group", "supergroup"]:
                if len(args) > 1:
                    identifier = args[1].strip()
                    if not identifier.startswith("@") and not identifier.lstrip("-").isdigit():
                        identifier = "@" + identifier
                else:
                    if message.chat.username:
                        identifier = f"@{message.chat.username}"
                    else:
                        # 🔁 Local fallback (no username)
                        local_msg = f"""✘《 Group Information ↯ 》
↯ Title: {message.chat.title}
↯ Chat ID: {message.chat.id}
↯ Type: {message.chat.type.title()}
↯ Username: Not set
↯ Description: Not available

↯ API Owner: @itz_mahir404 follow: https://t.me/bro_bin_lagbe
"""
                        bot.send_message(
                            message.chat.id,
                            f"<b>{local_msg}</b>",
                            parse_mode="HTML"
                        )
                        return
            else:
                bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র গ্রুপে ব্যবহারযোগ্য।")
                return

        # CHANNEL
        elif target_type == "channel":
            if len(args) > 1:
                identifier = args[1].strip()
                if not identifier.startswith("@") and not identifier.lstrip("-").isdigit():
                    identifier = "@" + identifier
            else:
                bot.reply_to(message, "ℹ️ চ্যানেলের ইনফো পেতে অবশ্যই ইউজারনেম দিতে হবে। যেমন: /cnnl @channelusername")
                return
        else:
            bot.reply_to(message, "❌ অনুপযুক্ত অনুরোধ।")
            return

        # API Request
        try:
            api_url = f"https://tele-user-info-api-production.up.railway.app/get_user_info?username={identifier}"
            response = requests.get(api_url, timeout=15)

            if response.status_code != 200:
                bot.reply_to(message, f"❌ API Error: HTTP {response.status_code}")
                return

            if not response.text.strip():
                bot.reply_to(message, "❌ API থেকে কোনো তথ্য পাওয়া যায়নি।")
                return

            lines = response.text.strip().splitlines()
            profile_pic_url = None
            msg_lines = []

            for line in lines:
                if line.lower().startswith("↯ profile picture url:"):
                    profile_pic_url = line.split(":", 1)[1].strip()
                else:
                    msg_lines.append(line)

            final_msg = "\n".join(msg_lines).strip()

            if not final_msg:
                bot.reply_to(message, "❌ তথ্য খালি।")
                return

            # ছবিসহ পাঠাও যদি প্রোফাইল পিকচার থাকে
            if profile_pic_url and profile_pic_url.startswith("http"):
                try:
                    pic_response = requests.get(profile_pic_url, timeout=10)
                    pic_response.raise_for_status()
                    photo_file = BytesIO(pic_response.content)
                    photo_file.name = "profile.jpg"

                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=InputFile(photo_file),
                        caption=f"<b>{final_msg}</b>",
                        parse_mode="HTML"
                    )
                except Exception:
                    bot.send_message(
                        message.chat.id,
                        f"<b>{final_msg}</b>\n⚠️ প্রোফাইল পিকচার লোড করতে সমস্যা হয়েছে।",
                        parse_mode="HTML"
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    f"<b>{final_msg}</b>",
                    parse_mode="HTML"
                )

        except requests.exceptions.Timeout:
            bot.reply_to(message, "❌ অনুরোধের সময় শেষ। আবার চেষ্টা করুন।")
        except requests.exceptions.ConnectionError:
            bot.reply_to(message, "❌ ইন্টারনেট সংযোগ সমস্যা।")
        except requests.exceptions.RequestException as e:
            bot.reply_to(message, f"❌ অনুরোধ ব্যর্থ: {str(e)}")
        except Exception as e:
            bot.reply_to(message, f"❌ অপ্রত্যাশিত সমস্যা: {str(e)}")

    # হ্যান্ডলার রেজিস্ট্রেশন
    @bot.message_handler(commands=["usr"])
    def handle_usr(message: Message):
        fetch_info(bot, message, target_type="user")

    @bot.message_handler(commands=["bot"])
    def handle_bot(message: Message):
        fetch_info(bot, message, target_type="bot")

    @bot.message_handler(commands=["grp"])
    def handle_grp(message: Message):
        fetch_info(bot, message, target_type="group")

    @bot.message_handler(commands=["cnnl"])
    def handle_cnnl(message: Message):
        fetch_info(bot, message, target_type="channel")
