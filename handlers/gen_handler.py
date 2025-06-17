from telebot import types
from telebot.types import Message, CallbackQuery
import requests
import re
import base64

# ------------------------------
# Base64 encode/decode helpers
# ------------------------------
def encode_data(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_data(encoded: str) -> str:
    return base64.urlsafe_b64decode(encoded.encode()).decode()

# ------------------------------
# Emoji from country code
# ------------------------------
def country_code_to_emoji(country_code):
    if not country_code:
        return ""
    return ''.join(chr(127397 + ord(c.upper())) for c in country_code)

# ------------------------------
# BIN Info with 4-layer fallback
# ------------------------------
def get_bin_info(bin_number):
    # ✅ Primary: HandyAPI
    try:
        r = requests.get(
            f"https://data.handyapi.com/bin/{bin_number}",
            headers={"x-api-key": "handyapi-pub-4c5376b7b41649ce93d4b7f93984f088"}
        )
        if r.status_code == 200:
            data = r.json()
            a2 = data.get("Country", {}).get("A2", "")
            return {
                "brand": data.get("Scheme", "N/A").upper(),
                "type": data.get("Type", "N/A").upper(),
                "level": data.get("CardTier", "N/A").upper(),
                "bank": data.get("Issuer", "N/A"),
                "country": data.get("Country", {}).get("Name", "N/A"),
                "flag": country_code_to_emoji(a2)
            }
    except:
        pass

    # ✅ Fallback 1: binlist.net
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if r.status_code == 200:
            data = r.json()
            return {
                "brand": data.get("scheme", "N/A").upper(),
                "type": data.get("type", "N/A").upper(),
                "level": data.get("brand", "N/A").upper(),
                "bank": data.get("bank", {}).get("name", "N/A"),
                "country": data.get("country", {}).get("name", "N/A"),
                "flag": data.get("country", {}).get("emoji", "")
            }
    except:
        pass

    # ✅ Fallback 2: drlab
    try:
        r = requests.get(f"https://drlabapis.onrender.com/api/bin?bin={bin_number}")
        if r.status_code == 200:
            data = r.json()
            return {
                "brand": data.get("scheme", "N/A").upper(),
                "type": data.get("type", "N/A").upper(),
                "level": data.get("level", "N/A").upper(),
                "bank": data.get("bank", "N/A"),
                "country": data.get("country_name", "N/A"),
                "flag": data.get("country_emoji", "")
            }
    except:
        pass

    # ✅ Fallback 3: bingen.vercel.app
    try:
        r = requests.get(f"https://bingen-rho.vercel.app/?bin={bin_number}")
        if r.status_code == 200:
            data = r.json().get("bin_info", {})
            return {
                "brand": data.get("scheme", "N/A").upper(),
                "type": data.get("type", "N/A").upper(),
                "level": data.get("brand", "N/A").upper(),
                "bank": data.get("bank", "N/A"),
                "country": data.get("country", "N/A"),
                "flag": data.get("flag", "")
            }
    except:
        pass

    return None

# ------------------------------
# Card Length by BIN
# ------------------------------
def get_card_length(bin):
    first_digit = bin[0]

    if first_digit == '4':
        return 16  # Visa
    elif first_digit == '5':
        return 16  # Mastercard
    elif first_digit == '3':
        return 15  # Amex
    elif first_digit == '6':
        return 16  # Discover
    else:
        return 16  # Default

# ------------------------------
# API-based Card Generation
# ------------------------------
def generate_cards_via_api(bin_input, count):
    # Normalize input
    parts = bin_input.split('|')
    bin_part = parts[0].strip()

    # Get first 6 digits for BIN check
    bin_number = bin_part[:6].ljust(6, '0') if len(bin_part) >= 6 else bin_part.ljust(6, '0')

    # Auto-complete the BIN based on card type
    card_length = get_card_length(bin_number)
    required_x = card_length - len(bin_part)
    full_bin = bin_part + 'x' * required_x

    # Prepare the full query
    if len(parts) > 1:
        query = f"{full_bin}|{'|'.join(parts[1:])}"
    else:
        query = full_bin

    # Try API 2 first (supports CVV and more details)
    try:
        api2_url = f"https://web-production-6341e.up.railway.app/api/ccgenerator?bin={query}&count={count}"
        response = requests.get(api2_url)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                cards = []
                for card_data in data.get("generated", []):
                    card = f"{card_data.get('raw_card_number')}|{card_data.get('expiry_month')}|{card_data.get('expiry_year')[-2:]}|{card_data.get('cvv')}"
                    cards.append(card)

                # Get BIN info
                info = get_bin_info(bin_number)
                if not info and data.get("metadata"):
                    info = {
                        "brand": data.get("metadata", {}).get("card_type", "N/A").upper(),
                        "bank": data.get("metadata", {}).get("bin_bank", "N/A"),
                        "country": data.get("metadata", {}).get("bin_country", "N/A"),
                        "flag": ""
                    }

                return {
                    "cards": cards,
                    "info": info
                }
    except:
        pass

    # Fallback to API 1
    try:
        api1_url = f"https://drlabapis.onrender.com/api/ccgenerator?bin={query}&count={count}"
        response = requests.get(api1_url)

        if response.status_code == 200:
            cards = response.text.strip().split('\n')
            return {
                "cards": cards,
                "info": get_bin_info(bin_number)
            }
    except:
        pass

    return None

# ------------------------------
# Telegram Handlers
# ------------------------------
def register(bot):
    @bot.message_handler(commands=["gen", ".gen"])
    def handle_gen(message: Message):
        try:
            args = message.text.split(None, 2)
            if len(args) < 2:
                bot.reply_to(message, "❌ BIN missing.\nExample: `/gen 515462 .cnt 5`\nOr full format: `/gen 515462xxxxxx|02|28|573 .cnt 5`", parse_mode="Markdown")
                return

            full_input = ' '.join(args[1:])
            cnt_match = re.search(r"\.cnt\s*(\d+)", full_input, re.IGNORECASE)
            count = int(cnt_match.group(1)) if cnt_match else 10
            count = min(count, 30)

            base_input = re.sub(r"\.cnt\s*\d+", "", full_input, flags=re.IGNORECASE).strip()

            if not re.match(r"^([0-9]{6,16}|[0-9x]{12,16})(\|[0-9x]{1,4}){0,3}$", base_input):
                bot.reply_to(message, "❌ Invalid format.\nExamples:\n- `/gen 515462 .cnt 5`\n- `/gen 515462xxxxxx .cnt 5`\n- `/gen 515462xxxxxx|02|28 .cnt 5`\n- `/gen 515462xxxxxx|02|28|573 .cnt 5`", parse_mode="Markdown")
                return

            result = generate_cards_via_api(base_input, count)

            if not result or not result.get("cards"):
                bot.reply_to(message, "❌ Failed to generate cards. API may be down.")
                return

            cards = result["cards"]
            info = result.get("info")
            username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

            msg = (
                f"𝗕𝗜𝗡 ⇾ <code>{base_input.split('|')[0]}</code>\n"
                f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {count}\n\n"
                f"•──────────────────────•\n"
                + "\n".join([f"<code>{card}</code>" for card in cards]) +
                f"\n•──────────────────────•\n\n"
            )

            if info:
                msg += (
                    f"𝗜𝗻𝗳𝗼: {info['brand']} - {info['type']} - {info['level']}\n"
                    f"𝗕𝗮𝗻𝗸: {info['bank']}\n"
                    f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {info['country']} {info['flag']}\n"
                )

            msg += f"𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}"

            encoded_input = encode_data(base_input + f" .cnt {count}")
            cb_data = f"regen|{encoded_input}"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("♻️ Regenerate", callback_data=cb_data))

            bot.reply_to(message, msg, parse_mode="HTML", reply_markup=markup)

        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("regen|"))
    def handle_regen(call: CallbackQuery):
        try:
            _, encoded_input = call.data.split('|', 1)
            decoded_input = decode_data(encoded_input)

            cnt_match = re.search(r"\.cnt\s*(\d+)", decoded_input, re.IGNORECASE)
            count = int(cnt_match.group(1)) if cnt_match else 10
            count = min(count, 30)

            base_input = re.sub(r"\.cnt\s*\d+", "", decoded_input, flags=re.IGNORECASE).strip()

            result = generate_cards_via_api(base_input, count)

            if not result or not result.get("cards"):
                bot.answer_callback_query(call.id, "❌ Failed to generate cards. API may be down.")
                return

            cards = result["cards"]
            info = result.get("info")
            username = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name

            msg = (
                f"𝗕𝗜𝗡 ⇾ <code>{base_input.split('|')[0]}</code>\n"
                f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {count}\n\n"
                f"•──────────────────────•\n"
                + "\n".join([f"<code>{card}</code>" for card in cards]) +
                f"\n•──────────────────────•\n\n"
            )

            if info:
                msg += (
                    f"𝗜𝗻𝗳𝗼: {info['brand']} - {info['type']} - {info['level']}\n"
                    f"𝗕𝗮𝗻𝗸: {info['bank']}\n"
                    f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {info['country']} {info['flag']}\n"
                )

            msg += f"𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("♻️ Regenerate", callback_data=call.data))

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=msg,
                parse_mode="HTML",
                reply_markup=markup
            )
            bot.answer_callback_query(call.id, "✅ Cards regenerated.")

        except Exception as e:
            bot.answer_callback_query(call.id, f"⚠️ Error: {str(e)}")