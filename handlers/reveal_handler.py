def register(bot):

    @bot.message_handler(commands=['reveal'])
    def show_help(message):
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        help_text = (
            "🛠 Available Commands:\n\n"
            "/arise — Start the bot\n"
            "/gen or .gen — Generate random cards with BIN info\n"
            "/chk or .chk — Check a single card's status\n"
            "/mas — Check all generated cards at once (reply to a list)\n"
            "/reveal — Show all the commands\n\n"
            "<code>/gen &lt;bin&gt; .cnt &lt;amount&gt;</code> — Control quantity\n"
           f"\n👤 Revealed by: {username}"
        )
        bot.reply_to(message, help_text)