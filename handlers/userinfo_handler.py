import requests
from telebot.types import Message, InputFile
from io import BytesIO

def register(bot):
    @bot.message_handler(commands=["info"])
    def handle_userinfo(message: Message):
        identifier = None

        args = message.text.split(maxsplit=1)

        # Case 1: /info @username or /info user_id
        if len(args) > 1:
            identifier = args[1].strip()
            # যদি ইউজারনেম না হয় এবং ডেটা ডিজিট না হয়, @ যুক্ত করো
            if not identifier.startswith("@") and not identifier.isdigit():
                identifier = "@" + identifier

        # Case 2: Reply করলে রিপ্লাই করা ইউজারের ইনফো
        elif message.reply_to_message:
            user = message.reply_to_message.from_user or message.reply_to_message.forward_from
            if user:
                if user.username:
                    identifier = f"@{user.username}"
                else:
                    identifier = str(user.id)
            else:
                bot.reply_to(message, "❌ রিপ্লাই করা মেসেজ থেকে ইউজার পাওয়া যায়নি।")
                return

        # Case 3: অন্যথায় নিজের ইনফো
        else:
            if message.from_user.username:
                identifier = f"@{message.from_user.username}"
            else:
                identifier = str(message.from_user.id)

        try:
            api_url = f"https://tele-user-info-api-production.up.railway.app/get_user_info?username={identifier}"
            response = requests.get(api_url, timeout=15)

            if response.status_code != 200:
                bot.reply_to(message, f"❌ API Error: HTTP {response.status_code}")
                return

            if not response.text.strip():
                bot.reply_to(message, "❌ API থেকে কোনো তথ্য পাওয়া যায়নি।")
                return

            # API রেসপন্স থেকে প্রোফাইল পিকচার URL আলাদা করা
            lines = response.text.strip().splitlines()
            profile_pic_url = None
            msg_lines = []

            for line in lines:
                if line.lower().startswith("↯ profile picture url:"):
                    profile_pic_url = line.split(":", 1)[1].strip()
                    continue
                msg_lines.append(line)

            final_msg = "\n".join(msg_lines)

            # প্রোফাইল পিকচার থাকলে ডাউনলোড করে ছবি হিসেবে পাঠাও
            if profile_pic_url and profile_pic_url.startswith("http"):
                try:
                    pic_response = requests.get(profile_pic_url, timeout=10)
                    pic_response.raise_for_status()
                    photo_file = BytesIO(pic_response.content)
                    photo_file.name = "profile.jpg"

                    bot.send_photo(
                        message.chat.id,
                        InputFile(photo_file),
                        caption=f"<b>{final_msg}</b>",
                        parse_mode="HTML"
                    )
                except Exception:
                    bot.send_message(
                        message.chat.id,
                        f"<b>{final_msg}</b>\n\n⚠️ প্রোফাইল পিকচার লোড করতে সমস্যা হয়েছে।",
                        parse_mode="HTML"
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    f"<b>{final_msg}</b>",
                    parse_mode="HTML"
                )

        except requests.exceptions.Timeout:
            bot.reply_to(message, "❌ Request timeout. আবার চেষ্টা করুন।")
        except requests.exceptions.ConnectionError:
            bot.reply_to(message, "❌ কানেকশন সমস্যা। ইন্টারনেট চেক করুন।")
        except requests.exceptions.RequestException as e:
            bot.reply_to(message, f"❌ নেটওয়ার্ক সমস্যা: {str(e)}")
        except Exception as e:
            bot.reply_to(message, f"❌ অপ্রত্যাশিত সমস্যা: {str(e)}")
