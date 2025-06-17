import re

WHITELIST_USERNAMES = ['yourgroupusername', 'yourchannelusername']

BAD_WORDS = [
    'fuck', 'shit', 'bitch', 'bastard', 'asshole', 'cunt', 'nigger',
    'মাদারচোদ', 'চুদ', 'বালের', 'পঁচা', 'গান্ডু', 'খানকি', 'হারামজাদা', 'চোদ', 'ছ্যাদা',
]

LINK_REGEX = re.compile(r"(https?://\S+|t\.me/\S+|\w+\.(com|net|org|xyz|ru|info))", re.IGNORECASE)

def contains_bad_word(text):
    return any(word in text.lower() for word in BAD_WORDS)

def contains_external_link(text):
    return bool(LINK_REGEX.search(text))

def is_whitelisted(text):
    return any(whitelisted.lower() in text.lower() for whitelisted in WHITELIST_USERNAMES)

def register(bot):
    # /antispam test command
    @bot.message_handler(commands=['antispam'])
    def antispam_test(message):
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        bot.reply_to(message, f"✅ AntiSpam is working! Hello, {username}")

    # Main anti-spam checker
    @bot.message_handler(func=lambda message: message.text is not None)
    def handle_antispam(message):
        text = message.text
        chat_id = message.chat.id
        msg_id = message.message_id
        from_user = message.from_user

        print(f"\n📩 New message from @{from_user.username or from_user.first_name}: {text}")

        try:
            member = bot.get_chat_member(chat_id, from_user.id)
            print(f"👤 User status: {member.status}")

            if member.status in ['administrator', 'creator']:
                print("✅ Skipping admin/creator message.")
                return

            if contains_bad_word(text):
                print("🚨 Bad word detected.")
                try:
                    bot.delete_message(chat_id, msg_id)
                    print("🗑️ Deleted message containing bad word.")
                except Exception as e:
                    print(f"❌ Failed to delete bad word message: {e}")
                return

            if contains_external_link(text) and not is_whitelisted(text):
                print("🔗 External link detected.")
                try:
                    bot.delete_message(chat_id, msg_id)
                    print("🗑️ Deleted message containing external link.")
                except Exception as e:
                    print(f"❌ Failed to delete link message: {e}")
                return

            print("✅ Message passed all checks.")

        except Exception as e:
            print(f"❌ Error in antispam handler: {e}")
