import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta
from flask import Flask

# ------------------ KEEP ALIVE ------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web_server, daemon=True).start()

# ------------------ CONFIG ------------------
TOKEN = os.environ.get('BOT_TOKEN', 'PUT_TOKEN_HERE')
bot = telebot.TeleBot(TOKEN)

STATS_FILE = 'stats.json'
PHOTOS_DIR = 'photos'

# ------------------ LINKS ------------------
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

# ------------------ TEXTS ------------------
TEXTS = {
    'EN': {
        'promo': "🔥 Exclusive private content\n👇 Choose access:",
        'btn1': "🌟 Monthly Access",
        'btn2': "💎 Lifetime Access",
        'link_text': "🔗 OPEN PAYMENT",
        'click_text': "👇 Click to continue"
    },
    'MX': {
        'promo': "🔥 Contenido privado exclusivo\n👇 Elige acceso:",
        'btn1': "🌟 Acceso Mensual",
        'btn2': "💎 Acceso Vitalicio",
        'link_text': "🔗 ABRIR PAGO",
        'click_text': "👇 Haz clic para continuar"
    },
    'BR': {
        'promo': "🔥 Conteúdo privado exclusivo\n👇 Escolha o acesso:",
        'btn1': "🌟 Acesso Mensal",
        'btn2': "💎 Acesso Vitalício",
        'link_text': "🔗 ABRIR PAGAMENTO",
        'click_text': "👇 Clique para continuar"
    }
}

# ------------------ DATA ------------------
def empty_data():
    return {
        "users": {},
        "langs": {},
        "refs": {},
        "clicked": {},
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

# ------------------ USER TRACKING ------------------
def update_user(user_id):
    user_id = str(user_id)
    now = datetime.now().isoformat()

    if user_id not in data['users']:
        data['users'][user_id] = {
            "first_seen": now,
            "last_seen": now,
            "visits": 1
        }
    else:
        data['users'][user_id]["last_seen"] = now
        data['users'][user_id]["visits"] += 1

    save_data()

# ------------------ START ------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    update_user(user_id)

    ref = message.text.replace('/start', '').strip() or 'direct'
    data['refs'][user_id] = ref
    save_data()

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_EN"),
        InlineKeyboardButton("🇲🇽 Español", callback_data="lang_MX"),
        InlineKeyboardButton("🇧🇷 Português", callback_data="lang_BR")
    )

    bot.send_message(
        message.chat.id,
        "Select language:",
        reply_markup=kb
    )

# ------------------ LANGUAGE ------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_lang(c):
    user_id = str(c.message.chat.id)
    lang = c.data.split("_")[1]

    data['langs'][user_id] = lang
    save_data()

    txt = TEXTS[lang]
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(txt['btn1'], callback_data="buy_1"),
        InlineKeyboardButton(txt['btn2'], callback_data="buy_2")
    )

    bot.send_message(c.message.chat.id, txt['promo'], reply_markup=kb)
    bot.delete_message(c.message.chat.id, c.message.message_id)

# ------------------ BUY CLICK ------------------
@bot.callback_query_handler(func=lambda c: c.data in ['buy_1', 'buy_2'])
def buy_click(c):
    user_id = str(c.message.chat.id)
    update_user(user_id)

    lang = data['langs'].get(user_id, 'EN')
    txt = TEXTS[lang]

    data['clicked'].setdefault(user_id, [])
    data['clicked'][user_id].append({
        "btn": c.data,
        "time": datetime.now().isoformat()
    })
    save_data()

    url = LINKS.get(lang, LINKS['EN'])[c.data]

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(txt['link_text'], url=url))
    bot.send_message(c.message.chat.id, txt['click_text'], reply_markup=kb)

# ------------------ PAID CONFIRM ------------------
@bot.message_handler(commands=['paid'])
def paid_cmd(message):
    uid = str(message.chat.id)
    data['paid'][uid] = True
    save_data()
    bot.reply_to(message, "✅ Payment confirmed")

@bot.message_handler(commands=['unpaid'])
def unpaid_cmd(message):
    uid = str(message.chat.id)
    data['paid'][uid] = False
    save_data()
    bot.reply_to(message, "❌ Payment removed")

# ------------------ STATS ------------------
@bot.message_handler(commands=['stats'])
def stats(message):
    now = datetime.now()
    total = len(data['users'])

    active_7d = 0
    for u in data['users'].values():
        last = datetime.fromisoformat(u['last_seen'])
        if last > now - timedelta(days=7):
            active_7d += 1

    clicked = len(data['clicked'])
    paid = len([u for u, v in data['paid'].items() if v])

    text = (
        f"📊 STATISTICS\n\n"
        f"👥 Total users: {total}\n"
        f"⚡ Active (7 days): {active_7d}\n"
        f"🔗 Clicked payment: {clicked}\n"
        f"💰 Paid users: {paid}\n"
    )

    bot.reply_to(message, text)

# ------------------ RUN ------------------
if __name__ == "__main__":
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    print("Bot running...")
    bot.infinity_polling()
