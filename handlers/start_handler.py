def register(bot):
    @bot.message_handler(commands=['start', 'arise'])
    def start_command(message):
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        welcome_text = (
            f"👋 <b>Welcome {username}!</b>\n\n"
            "You Arisied This Bot. Here are the available commands:\n\n"
            "<code>/gen</code> or <code>.gen</code> — Generate cards\n"
            "<code>/chk</code> or <code>.chk</code> — Check single card\n"
            "<code>/mas</code> — Mass check (reply to list)\n"
            "<code>/reveal</code> — Show all commands\n\n"
            "<code>/gen &lt;bin&gt; .cnt &lt;amount&gt;</code> — Control quantity\n\n"
            "📢 Join our Telegram Channel:\n"
            "<a href='https://t.me/bro_bin_lagbe'>https://t.me/bro_bin_lagbe</a>"
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")
