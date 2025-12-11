
import telebot
from telebot import types
import os
import random
import json
from datetime import datetime, timedelta
import time
import threading

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable TOKEN is not set.")

bot = telebot.TeleBot(TOKEN)

STATS_FILE = "stats.json"


def load_stats():
    if not os.path.exists(STATS_FILE):
        data = {"users": {}, "photos": {}, "langs": {}, "paid": {}, "clicked": {}}
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def register_user(user_id: int):
    data = load_stats()
    uid = str(user_id)
    data.setdefault("users", {})
    data.setdefault("photos", {})
    data.setdefault("langs", {})
    data.setdefault("paid", {})
    data.setdefault("clicked", {})
    data["users"][uid] = datetime.now().strftime("%Y-%m-%d")
    save_stats(data)


def get_random_photo(user_id: int):
    data = load_stats()
    uid = str(user_id)
    data.setdefault("photos", {})
    photos_dir = "photos"
    if not os.path.isdir(photos_dir):
        return None
    files = [f for f in os.listdir(photos_dir) if not f.startswith(".")]
    if not files:
        return None
    if uid not in data["photos"]:
        photo_name = random.choice(files)
        data["photos"][uid] = photo_name
        save_stats(data)
    else:
        photo_name = data["photos"][uid]
    return os.path.join(photos_dir, photo_name)


TEXTS = {
    "EN": "EXCLUSIVE CHRISTMAS PROMO\n\nThis is just a preview. Full uncensored content is waiting for you inside.\n\nLimited Christmas offer — full videos, no censorship.\n\nIf you can't pay, message support 👉 @laraoficial",
    "MX": "PROMO DE NAVIDAD\n\nEsto es solo una probadita. El contenido completo sin censura está adentro.\n\nOferta navideña limitada — videos completos sin cortes.\n\nSi no puedes pagar, escribe al soporte 👉 @laraoficial",
    "BR": "PROMO DE NATAL DA LARAH\n\nAqui é só o gostinho. O conteúdo completo sem censura está lá dentro.\n\nPromoção limitada — vídeos completos sem cortes.\n\nSe não conseguir pagar, chama no suporte 👉 @laraoficial",
}

REMINDERS_SOFT = {
    "EN": [
        "Just checking on you… VIP access is still open.",
        "You know you want it… exclusive uncensored content is waiting.",
        "Reminder: Telegram doesn’t show the real content… WhatsApp VIP does.",
    ],
    "MX": [
        "Solo para recordarte… tu acceso VIP sigue disponible.",
        "Lo deseas… lo sé. El contenido sin censura te espera.",
        "Recuerda: lo fuerte no está en Telegram… está en mi WhatsApp VIP.",
    ],
    "BR": [
        "Só passando pra lembrar… seu VIP ainda tá liberado.",
        "Você quer… eu sei. O conteúdo sem censura te espera.",
        "Lembrete: o pesado não tá aqui… tá no WhatsApp VIP.",
    ],
}

REMINDERS_HARD = {
    "EN": [
        "I know you're getting hard reading this… imagine the videos inside.",
        "Stop teasing yourself. Get in and see everything uncensored.",
        "I’m waiting naked in the VIP. Don’t make me wait too long…",
    ],
    "MX": [
        "Sé que te pones duro leyendo esto… imagina los videos.",
        "Deja de torturarte. Entra y míralo TODO sin censura.",
        "Te espero desnuda en el VIP… no tardes demasiado.",
    ],
    "BR": [
        "Eu sei que você ficou duro só de ler isso… imagina os vídeos.",
        "Para de se torturar. Entra e vê TUDO sem censura.",
        "Tô te esperando peladinha no VIP… não demora.",
    ],
}

CHECKOUT_URL_1 = "https://www.mariamoments.com/checkouts/cn/hWN6Jvmvt2IlLNqxt7cd0yH3/en-ua?_r=AQABDGmwQ_zl-Ob2_e4B2Q40YUPl7SN2y-Ca6EStQGrfIIk&preview_theme_id=157844832476"
CHECKOUT_URL_2 = "https://www.mariamoments.com/checkouts/cn/hWN6JvtmdIWclh1bDPpLhNon/en-ua?_r=AQABS9ZgBxs59yvSWr_gxtKQut1eBtvnApjLyxbq9w3ohTY&preview_theme_id=157844832476"


def payment_buttons():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            "Exclusive WhatsApp Access (ONLY 18+) R$11,97",
            callback_data="buy_1",
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            "HARD Exclusive WhatsApp Access (ONLY 18+) R$14,97",
            callback_data="buy_2",
        )
    )
    return kb


def mark_clicked(user_id: int):
    data = load_stats()
    uid = str(user_id)
    data.setdefault("clicked", {})
    data["clicked"][uid] = True
    save_stats(data)


@bot.message_handler(commands=["start"])
def cmd_start(message):
    register_user(message.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("English", callback_data="lang_EN"))
    kb.add(types.InlineKeyboardButton("Español MX", callback_data="lang_MX"))
    kb.add(types.InlineKeyboardButton("Português BR", callback_data="lang_BR"))
    bot.send_message(
        message.chat.id,
        "Choose language / Elegir idioma / Escolha o idioma:",
        reply_markup=kb,
    )


@bot.message_handler(commands=["language"])
def cmd_language(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("English", callback_data="lang_EN"))
    kb.add(types.InlineKeyboardButton("Español MX", callback_data="lang_MX"))
    kb.add(types.InlineKeyboardButton("Português BR", callback_data="lang_BR"))
    bot.send_message(
        message.chat.id,
        "Choose language / Elegir idioma / Escolha o idioma:",
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def on_language(call):
    lang = call.data.replace("lang_", "")
    data = load_stats()
    uid = str(call.from_user.id)
    data.setdefault("langs", {})
    data["langs"][uid] = lang
    save_stats(data)

    photo_path = get_random_photo(call.from_user.id)
    if not photo_path:
        bot.answer_callback_query(call.id, "No photos found on server.")
        return

    with open(photo_path, "rb") as photo:
        bot.send_photo(
            call.message.chat.id,
            photo,
            caption=TEXTS.get(lang, TEXTS["EN"]),
            reply_markup=payment_buttons(),
            parse_mode="Markdown",
        )


@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def on_buy(call):
    mark_clicked(call.from_user.id)
    if call.data == "buy_1":
        url = CHECKOUT_URL_1
    else:
        url = CHECKOUT_URL_2
    try:
        bot.answer_callback_query(callback_query_id=call.id, url=url)
    except Exception:
        bot.answer_callback_query(callback_query_id=call.id, text="Opening checkout...")


@bot.message_handler(commands=["paid"])
def cmd_paid(message):
    data = load_stats()
    uid = str(message.from_user.id)
    data.setdefault("paid", {})
    data["paid"][uid] = True
    save_stats(data)
    bot.reply_to(message, "Marked as PAID. Reminders disabled.")


@bot.message_handler(commands=["unpaid"])
def cmd_unpaid(message):
    data = load_stats()
    uid = str(message.from_user.id)
    data.setdefault("paid", {})
    data["paid"][uid] = False
    save_stats(data)
    bot.reply_to(message, "Marked as NOT PAID. Reminders enabled.")


@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    data = load_stats()
    users = data.get("users", {})
    total = len(users)
    cutoff = datetime.now() - timedelta(days=30)
    last_30 = 0
    for date_str in users.values():
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            if d >= cutoff:
                last_30 += 1
        except Exception:
            continue
    bot.send_message(
        message.chat.id,
        f"Stats\n\nUsers last 30 days: {last_30}\nTotal users: {total}",
    )


def reminder_loop():
    while True:
        try:
            data = load_stats()
            users = data.get("users", {})
            langs = data.get("langs", {})
            paid = data.get("paid", {})
            clicked = data.get("clicked", {})
            for uid in list(users.keys()):
                if paid.get(uid) is True:
                    continue
                if clicked.get(uid) is True:
                    continue
                lang = langs.get(uid, "EN")
                soft_list = REMINDERS_SOFT.get(lang, REMINDERS_SOFT["EN"])
                hard_list = REMINDERS_HARD.get(lang, REMINDERS_HARD["EN"])
                all_texts = soft_list + hard_list
                text = random.choice(all_texts)
                photo_path = get_random_photo(int(uid))
                if not photo_path:
                    continue
                try:
                    with open(photo_path, "rb") as photo:
                        bot.send_photo(
                            int(uid),
                            photo,
                            caption=text,
                            reply_markup=payment_buttons(),
                            parse_mode="Markdown",
                        )
                except Exception:
                    continue
            time.sleep(4 * 60 * 60)
        except Exception:
            time.sleep(60)


if __name__ == "__main__":
    t = threading.Thread(target=reminder_loop, daemon=True)
    t.start()
    bot.polling(none_stop=True)
