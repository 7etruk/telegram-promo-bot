import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta
from flask import Flask

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web_server, daemon=True).start()

# ================= CONFIG =================
TOKEN = os.environ.get('BOT_TOKEN', os.environ.get('TOKEN', 'PUT_TOKEN_HERE'))
bot = telebot.TeleBot(TOKEN)

STATS_FILE = 'stats.json'
PHOTOS_DIR = 'photos'

# ================= LINKS =================
LINKS = {
    'EN': {
        'buy_1': "https://buy.stripe.com/EN_MONTH",
        'buy_2': "https://buy.stripe.com/EN_LIFE"
    },
    'MX': {
        'buy_1': "https://buy.stripe.com/MX_MONTH",
        'buy_2': "https://buy.stripe.com/MX_LIFE"
    },
    'BR': {
        'buy_1': "https://buy.stripe.com/BR_MONTH",
        'buy_2': "https://buy.stripe.com/BR_LIFE"
    }
}

# ================= TEXTS =================
TEXTS = {
    'EN': {
        'promo': "🔥 Exclusive private content\n👇 Choose access:",
        'btn1': "🌟Monthly Premium Access🌟♥",
        'btn2': "🌟Lifetime Premium Access🌟♥♥",
        'link_text': "🔗 OPEN LINK NOW",
        'click_text': "👇 Click below to access:",
        'soft': ["Hey! Don't miss out on this deal."],
        'hard': ["LAST CHANCE! Offer expires soon."]
    },
    'MX': {
        'promo': "🔥 Contenido privado exclusivo\n👇 Elige acceso:",
        'btn1': "🌟Acceso Premium Mensual🌟♥",
        'btn2': "🌟Acceso Premium Vitalicio🌟♥♥",
        'link_text': "🔗 ABRIR ENLACE AHORA",
        'click_text': "👇 Haga clic abajo para acceder:",
        'soft': ["¡Hola! No te pierdas esta oferta."],
        'hard': ["¡ÚLTIMA OPORTUNIDAD!"]
    },
    'BR': {
        'promo': "🔥 Conteúdo privado exclusivo\n👇 Escolha o acesso:",
        'btn1': "🌟Acesso Premium Mensal🌟♥",
        'btn2': "🌟Acesso Premium Vitalício🌟♥♥",
        'link_text': "🔗 ABRIR LINK AGORA",
        'click_text': "👇 Clique abaixo para acessar:",
        'soft': ["Oi! Não perca essa oferta."],
        'hard': ["ÚLTIMA CHANCE!"]
    }
}

# ================= DATA =================
def empty_data():
    return {
        "users": {},     # user_id → {first_seen, last_seen, visits}
        "langs": {},
        "photos": {},
        "clicked": {},   # user_id → count
        "paid": {}
    }

def load_data():
    if not os.path.exists(STATS_FILE):
        return empty_data()
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return empty_data()

def save_data():
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

data = load_data()

# ================= USER TRACKING =================
def update_user_activity(user_id):
    user_id = str(user_id)
    now = datetime.now().isoformat()

    if user_id not in data['users']:
        data['users'][user_id] = {
            "first_seen": now,
            "last_seen": now,
            "visits": 1
        }
    else:
        data['users'][user_id]['last_seen'] = now
        data['users'][user_id]['visits'] += 1

    save_data()

# ================= PHOTOS =================
def get_random_photo():
    try:
        files = [f for f in os.listdir(PHOTOS_DIR) if os.path.isfile(os.path.join(PHOTOS_DIR, f))]
        return os.path.join(PHOTOS_DIR, random.choice(files)) if files else None
    except:
        return None

def get_user_photo(user_id):
    user_id = str(user_id)
    if user_id in data['photos'] and os.path.exists(data['photos'][user_id]):
        return data['photos'][user_id]
    photo = get_random_photo()
    if photo:
        data['photos'][user_id] = photo
        save_data()
    return photo

# ================= START =================
@bot.message_handler(commands=['start', 'language'])
def send_welcome(message):
    update_user_activity(message.chat.id)

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_EN"),
        InlineKeyboardButton("🇲🇽 Español MX", callback_data="lang_MX"),
        InlineKeyboardButton("🇧🇷 Português BR", callback_data="lang_BR")
    )

    bot.send_message(
        message.chat.id,
        "Please select your language:",
        reply_markup=kb
    )

# ================= LANGUAGE =================
@bot.callback_query_handler(func=lambda c: c.data.startswith('lang_'))
def set_language(c):
    user_id = str(c.message.chat.id)
    lang = c.data.split('_')[1]

    data['langs'][user_id] = lang
    save_data()
    update_user_activity(user_id)

    txt = TEXTS[lang]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(txt['btn1'], callback_data="buy_1"),
        InlineKeyboardButton(txt['btn2'], callback_data="buy_2")
    )

    photo = get_user_photo(user_id)
    if photo:
        with open(photo, 'rb') as p:
            bot.send_photo(c.message.chat.id, p, caption=txt['promo'], reply_markup=kb)
    else:
        bot.send_message(c.message.chat.id, txt['promo'], reply_markup=kb)

    bot.delete_message(c.message.chat.id, c.message.message_id)

# ================= BUY CLICK =================
@bot.callback_query_handler(func=lambda c: c.data in ['buy_1', 'buy_2'])
def handle_buy(c):
    user_id = str(c.message.chat.id)
    update_user_activity(user_id)

    data['clicked'][user_id] = data['clicked'].get(user_id, 0) + 1
    save_data()

    lang = data['langs'].get(user_id, 'EN')
    txt = TEXTS[lang]
    url = LINKS.get(lang, LINKS['EN'])[c.data]

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(txt['link_text'], url=url))

    bot.send_message(c.message.chat.id, txt['click_text'], reply_markup=kb)

# ================= PAID =================
@bot.message_handler(commands=['paid'])
def set_paid(message):
    data['paid'][str(message.chat.id)] = True
    save_data()
    bot.reply_to(message, "✅ User marked as PAID")

@bot.message_handler(commands=['unpaid'])
def set_unpaid(message):
    data['paid'][str(message.chat.id)] = False
    save_data()
    bot.reply_to(message, "❌ User marked as UNPAID")

# ================= STATS =================
@bot.message_handler(commands=['stats'])
def stats(message):
    now = datetime.now()

    total = len(data['users'])

    active_month = 0
    for u in data['users'].values():
        last = datetime.fromisoformat(u['last_seen'])
        if last.month == now.month and last.year == now.year:
            active_month += 1

    clicked = sum(data['clicked'].values())
    paid = len([u for u, v in data['paid'].items() if v])

    text = (
        f"📊 STATISTICS\n\n"
        f"👥 Total users: {total}\n"
        f"📅 Active this month: {active_month}\n"
        f"🔗 Total clicks: {clicked}\n"
        f"💰 Paid users: {paid}"
    )

    bot.reply_to(message, text)

# ================= REMINDERS =================
def reminder_worker():
    while True:
        time.sleep(4 * 3600)
        for user_id in data['users']:
            if data['paid'].get(user_id):
                continue
            lang = data['langs'].get(user_id, 'EN')
            txt = TEXTS[lang]
            text = random.choice(txt['soft'] + txt['hard'])
            photo = get_user_photo(user_id)

            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(txt['btn1'], callback_data="buy_1"))

            try:
                if photo:
                    with open(photo, 'rb') as p:
                        bot.send_photo(user_id, p, caption=text, reply_markup=kb)
                else:
                    bot.send_message(user_id, text, reply_markup=kb)
                time.sleep(0.5)
            except:
                pass

threading.Thread(target=reminder_worker, daemon=True).start()

# ================= RUN =================
if __name__ == "__main__":
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    print("Bot is running...")
    bot.infinity_polling()
