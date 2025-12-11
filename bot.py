import telebot
from telebot import types
import os
import random
import json
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# ---- Load or create stats file ----
if not os.path.exists("stats.json"):
    with open("stats.json", "w") as f:
        json.dump({"users": {}}, f)

def load_stats():
    with open("stats.json", "r") as f:
        return json.load(f)

def save_stats(data):
    with open("stats.json", "w") as f:
        json.dump(data, f)

# ---- Random photo system ----
def get_random_photo(user_id):
    # User-specific random photo (saved once)
    stats = load_stats()

    if "photos" not in stats:
        stats["photos"] = {}

    if str(user_id) not in stats["photos"]:
        photo = random.choice(os.listdir("photos"))
        stats["photos"][str(user_id)] = photo
        save_stats(stats)
    else:
        photo = stats["photos"][str(user_id)]

    return f"photos/{photo}"


# ---- Save user stats ----
def register_user(user_id):
    stats = load_stats()
    stats["users"][str(user_id)] = datetime.now().strftime("%Y-%m-%d")
    save_stats(stats)


# ---- Texts for 3 languages ----
TEXTS = {
    "EN": """🔥 CHRISTMAS PROMO 🔥

This is just a preview 😏 The full content is available inside — uncensored and exclusive.

🎅 Limited Christmas offer — full videos, no cuts, no censorship.

If you can't pay, message support 👉 @laraoficial""",

    "MX": """🔥 PROMO DE NAVIDAD 🔥

Esto es solo una probadita 😏 El contenido completo está adentro — sin censura y exclusivo.

🎅 Oferta navideña limitada — videos completos sin cortes.

Si no puedes pagar, escribe al soporte 👉 @laraoficial""",

    "BR": """🔥 PROMO DE NATAL DA LARAH 🔥

Aqui é só o gostinho 😏 O conteúdo completo está lá dentro — sem censura e exclusivo.

🎅 Promoção limitada — vídeos completos sem cortes.

Se não conseguir pagar, chama no suporte 👉 @laraoficial"""
}

# ---- Payment buttons ----
def payment_buttons():
    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        "💗 Exclusive WhatsApp Access (ONLY 18+) R$11,97🔥",
        url="https://www.mariamoments.com/checkouts/cn/hWN6Jvmvt2IlLNqxt7cd0yH3/en-ua?_r=AQABDGmwQ_zl-Ob2_e4B2Q40YUPl7SN2y-Ca6EStQGrfIIk&preview_theme_id=157844832476"
    ))

    kb.add(types.InlineKeyboardButton(
        "💗 HARD Exclusive WhatsApp Access (ONLY 18+) R$14,97🍑",
        url="https://www.mariamoments.com/checkouts/cn/hWN6JvtmdIWclh1bDPpLhNon/en-ua?_r=AQABS9ZgBxs59yvSWr_gxtKQut1eBtvnApjLyxbq9w3ohTY&preview_theme_id=157844832476"
    ))

    return kb

# ---- START ----
@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user.id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_EN"))
    kb.add(types.InlineKeyboardButton("🇲🇽 Español MX", callback_data="lang_MX"))
    kb.add(types.InlineKeyboardButton("🇧🇷 Português BR", callback_data="lang_BR"))

    bot.send_message(
        message.chat.id,
        "Choose language / Elegir idioma / Escolha o idioma:",
        reply_markup=kb
    )


# ---- LANGUAGE SELECT ----
@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def send_promo(call):
    lang = call.data.replace("lang_", "")

    photo_path = get_random_photo(call.from_user.id)
    photo = open(photo_path, "rb")

    bot.send_photo(
        call.message.chat.id,
        photo,
        caption=TEXTS[lang],
        reply_markup=payment_buttons(),
        parse_mode="HTML"
    )


# ---- STATS ----
@bot.message_handler(commands=["stats"])
def stats(message):
    stats = load_stats()["users"]

    total = len(stats)

    last_30_days = 0
    cutoff = datetime.now() - timedelta(days=30)

    for date_str in stats.values():
        if datetime.strptime(date_str, "%Y-%m-%d") > cutoff:
            last_30_days += 1

    bot.send_message(
        message.chat.id,
        f"📊 *Stats*\n\nUsers last 30 days: *{last_30_days}*\nTotal users: *{total}*",
        parse_mode="Markdown"
    )


bot.polling(none_stop=True)
