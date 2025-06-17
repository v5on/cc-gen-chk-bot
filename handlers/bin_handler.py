import aiohttp
import asyncio
import telebot
from flag_data import COUNTRY_FLAGS

def register(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda m: m.text and m.text.lower().startswith(('/bin', '.bin')))
    def handle_bin_command(message):
        parts = message.text.strip().split()
        if len(parts) < 2:
            bot.reply_to(message, "❗ একটি BIN দিন যেমন: `/bin 426633`", parse_mode="Markdown")
            return

        bin_number = parts[1]

        try:
            bin_info = asyncio.run(lookup_bin(bin_number))

            if "error" in bin_info:
                bot.reply_to(message, f"❌ ত্রুটি: {bin_info['error']}")
                return

            formatted = (
                f"𝗕𝗜𝗡: `{bin_number}`\n"
                f"𝗧𝘆𝗽𝗲: {bin_info.get('card_type', 'NOT FOUND').upper()} ({bin_info.get('network', 'NOT FOUND').upper()})\n"
                f"𝗕𝗿𝗮𝗻𝗱: {bin_info.get('tier', 'NOT FOUND').upper()}\n"
                f"𝐈𝐬𝐬𝐮𝐞𝐫: {bin_info.get('bank', 'NOT FOUND').upper()}\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {bin_info.get('country', 'NOT FOUND').upper()} {bin_info.get('flag', '🏳️')}\n"
                f"𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆: {bin_info.get('currency', 'NOT FOUND')} | 𝗖𝗼𝗱𝗲: {bin_info.get('country_code', 'N/A')}\n"
                f"𝗣𝗿𝗲𝗽𝗮𝗶𝗱: {'YES' if bin_info.get('prepaid') else 'NO'} | 𝗟𝘂𝗵𝗻 𝗩𝗮𝗹𝗶𝗱: {'YES' if bin_info.get('luhn') else 'NO'}"
            )

            bot.reply_to(message, formatted, parse_mode="Markdown")

        except Exception as e:
            bot.reply_to(message, f"❌ Internal error: {str(e)}")


async def lookup_bin(bin_number: str) -> dict:
    bin_to_use = ''.join(filter(str.isdigit, bin_number))[:6]

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # ✅ HandyAPI (primary)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://data.handyapi.com/bin/{bin_to_use}",
                headers={**headers, "x-api-key": "handyapi-pub-4c5376b7b41649ce93d4b7f93984f088"}
            ) as res:
                if res.status == 200:
                    data = await res.json()
                    country = data.get("Country", {}).get("Name", "").upper()
                    return {
                        "card_type": data.get("Type"),
                        "network": data.get("Scheme"),
                        "tier": data.get("CardTier"),
                        "bank": data.get("Issuer"),
                        "country": country,
                        "currency": "N/A",
                        "country_code": data.get("Country", {}).get("Alpha2", "N/A"),
                        "flag": COUNTRY_FLAGS.get(country, "🏳️"),
                        "prepaid": False,
                        "luhn": True
                    }
    except Exception as e:
        print("handyapi fallback:", e)

    # ✅ binlist.net
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lookup.binlist.net/{bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    country = data.get("country", {}).get("name", "").upper()
                    return {
                        "card_type": data.get("type"),
                        "network": data.get("scheme"),
                        "tier": data.get("brand"),
                        "bank": data.get("bank", {}).get("name"),
                        "country": country,
                        "currency": data.get("country", {}).get("currency"),
                        "country_code": data.get("country", {}).get("alpha2"),
                        "flag": data.get("country", {}).get("emoji", "🏳️"),
                        "prepaid": data.get("prepaid", False),
                        "luhn": data.get("number", {}).get("luhn", True)
                    }
    except Exception as e:
        print("binlist fallback:", e)

    # ✅ drlabapis
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://drlabapis.onrender.com/api/bin?bin={bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    if data.get("status") == "ok":
                        country = data.get("country", "").upper()
                        return {
                            "card_type": data.get("type"),
                            "network": data.get("scheme"),
                            "tier": data.get("tier"),
                            "bank": data.get("issuer"),
                            "country": country,
                            "currency": "N/A",
                            "country_code": "N/A",
                            "flag": COUNTRY_FLAGS.get(country, "🏳️"),
                            "prepaid": False,
                            "luhn": True
                        }
    except Exception as e:
        print("drlab fallback:", e)

    # ✅ bingen.vercel.app
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bingen-rho.vercel.app/?bin={bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    bin_info = data.get("bin_info", {})
                    country = bin_info.get("country", "").upper()
                    return {
                        "card_type": bin_info.get("type"),
                        "network": bin_info.get("scheme"),
                        "tier": bin_info.get("brand"),
                        "bank": bin_info.get("bank"),
                        "country": country,
                        "currency": "N/A",
                        "country_code": bin_info.get("country_code", "N/A"),
                        "flag": bin_info.get("flag", "🏳️"),
                        "prepaid": False,
                        "luhn": True
                    }
    except Exception as e:
        print("bingen fallback:", e)

    return {"error": "BIN info not found in any source"}
