import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta
from flask import Flask

# --- ФЕЙКОВИЙ ВЕБ-СЕРВЕР ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

keep_alive_thread = threading.Thread(target=run_web_server)
keep_alive_thread.daemon = True
keep_alive_thread.start()

# --- КОНФІГУРАЦІЯ ---
TOKEN = os.environ.get('BOT_TOKEN', os.environ.get('TOKEN', 'ВСТАВ_СВІЙ_ТОКЕН_ТУТ'))

bot = telebot.TeleBot(TOKEN)

STATS_FILE = 'stats.json'
PHOTOS_DIR = 'photos'

# --- СИСТЕМА ПОСИЛАНЬ ---
LINKS = {
    'EN': { # США
        'buy_1': "https://buy.stripe.com/6oU5kwgFk4wA9Mh44mc3m03",
        'buy_2': "https://buy.stripe.com/6oU7sEagW3sw2jP8kCc3m02"
    },
    'MX': { # Мексика
        'buy_1': "https://buy.stripe.com/5kQ8wIexcgfi9Mh8kCc3m01",
        'buy_2': "https://buy.stripe.com/4gMbIU2Ou2os1fL0Sac3m00"
    },
    'BR': { # Бразилія
        'buy_1': "https://buy.stripe.com/5kQ8wIexcgfi9Mh8kCc3m01",
        'buy_2': "https://buy.stripe.com/4gMbIU2Ou2os1fL0Sac3m00"
    }
}

# --- ТЕКСТИ ---
TEXTS = {
    'EN': {
        'promo': """I know you're dying to see everything I can do 👀, get access to all my photos and videos in my exclusive group 💕.

📸 Explicit videos and photos just the way you like it...
ㅤㅤ🍑 ANAL
ㅤㅤ💦 Multiple orgasms and SQUIRTING
ㅤㅤ👅 Oral
ㅤㅤ😈 Videos and photos with my girlfriends
ㅤㅤ🙇🏻‍♀️And LOTS of penetration
🎥 Exclusive VIP Lives
📲 My WhatsApp
🥇 My full attention just for you

All you need to have fun the way you want is one click and one move, waiting for you in private! 🙈👇🏻""",
        'btn1': "🌟Monthly Premium Access🌟♥",
        'btn2': "🌟Lifetime Premium Access🌟♥♥",
        'link_text': "🔗 OPEN LINK NOW",
        'click_text': "👇 Click below to access:",
        'soft': ["Hey! Don't miss out on this deal.", "Your Christmas gift is waiting!"],
        'hard': ["LAST CHANCE! Offer expires soon.", "Hurry up! Discount ending."]
    },
    'MX': {
        'promo': """Sé que te mueres de curiosidad por ver todo lo que puedo hacer 👀, obtén acceso a todas mis fotos y videos en mi grupo exclusivo 💕.

📸 Videos y fotos explícitas tal como te gusta...
ㅤㅤ🍑 ANAL
ㅤㅤ💦 Múltiples orgasmos y SQUIRTING
ㅤㅤ👅 Oral
ㅤㅤ😈 Videos y fotos con mis amigas
ㅤㅤ🙇🏻‍♀️Y MUCHA penetración
🎥 Lives exclusivos de mi VIP
📲 Mi WhatsApp
🥇 Toda mi atención solo para ti

Lo que necesitas para divertirte como quieres es un clic y una sola actitud, ¡te espero en mi privado! 🙈👇🏻""",
        'btn1': "🌟Acceso Premium Mensual🌟♥",
        'btn2': "🌟Acceso Premium Vitalicio🌟♥♥",
        'link_text': "🔗 ABRIR ENLACE AHORA",
        'click_text': "👇 Haga clic abajo para acceder:",
        'soft': ["¡Hola! No te pierdas esta oferta.", "¡Tu regalo de Navidad te espera!"],
        'hard': ["¡ÚLTIMA OPORTUNIDAD! La oferta expira pronto.", "¡Date prisa! El descuento termina."]
    },
    'BR': {
        'promo': """Eu sei que você está morrendo de curiosidade em ver tudo o que eu posso fazer 👀, tenha acesso a todas as minhas fotos e vídeos no meu grupo exclusivo 💕.

📸 Vídeos e fotos explícitas do jeito que você gosta...
ㅤㅤ🍑 ANAL
ㅤㅤ💦 Múltiples orgasmos e SQUIRTING
ㅤㅤ👅 Oral
ㅤㅤ😈 Videos e fotos com minhas amigas
ㅤㅤ🙇🏻‍♀️E MUITA penetração
🎥 Lives do meu VIP exclusivas
📲 Meu whatsapp
🥇 Minha atenção todinha pra você

O que você precisa para se divertir do jeito que quer é um clique e uma única atitude, te espero no meu privado! 🙈👇🏻""",
        'btn1': "🌟Acesso Premium Mensal🌟♥",
        'btn2': "🌟Acesso Premium Vitalício🌟♥♥",
        'link_text': "🔗 ABRIR LINK AGORA",
        'click_text': "👇 Clique abaixo para acessar:",
        'soft': ["Oi! Não perca essa oferta.", "Seu presente de Natal está esperando!"],
        'hard': ["ÚLTIMA CHANCE! A oferta expira em breve.", "Corra! O desconto está acabando."]
    }
}

# --- ДАНІ ---
def load_data():
    if not os.path.exists(STATS_FILE):
        return {"users": {}, "photos": {}, "langs": {}, "paid": {}, "clicked": {}}
    try:
        with open(STATS_FILE, 'r') as f: return json.load(f)
    except: return {"users": {}, "photos": {}, "langs": {}, "paid": {}, "clicked": {}}

def save_data(data):
    try:
        with open(STATS_FILE, 'w') as f: json.dump(data, f, indent=4)
    except: pass

data = load_data()

# --- ФУНКЦІЇ ---
def get_random_photo_file():
    try:
        files = [f for f in os.listdir(PHOTOS_DIR) if os.path.isfile(os.path.join(PHOTOS_DIR, f))]
        if not files: return None
        return os.path.join(PHOTOS_DIR, random.choice(files))
    except: return None

def get_user_photo(user_id):
    user_id = str(user_id)
    if user_id in data['photos'] and os.path.exists(data['photos'][user_id]):
        return data['photos'][user_id]
    new_photo = get_random_photo_file()
    if new_photo:
        data['photos'][user_id] = new_photo
        save_data(data)
    return new_photo

def update_user_activity(user_id):
    data['users'][str(user_id)] = datetime.now().isoformat()
    save_data(data)

# --- ОБРОБНИКИ ---
@bot.message_handler(commands=['start', 'language'])
def send_welcome(message):
    user_id = str(message.chat.id)
    update_user_activity(user_id)
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_EN"),
        InlineKeyboardButton("🇲🇽 Español MX", callback_data="lang_MX"),
        InlineKeyboardButton("🇧🇷 Português BR", callback_data="lang_BR")
    )
    bot.send_message(message.chat.id, "Please select your language / Por favor seleccione su idioma / Por favor selecione seu idioma:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    user_id = str(call.message.chat.id)
    lang_code = call.data.split('_')[1]
    data['langs'][user_id] = lang_code
    save_data(data)
    
    photo_path = get_user_photo(user_id)
    txt = TEXTS[lang_code] 
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(txt['btn1'], callback_data="buy_1"))
    markup.add(InlineKeyboardButton(txt['btn2'], callback_data="buy_2"))
    
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=txt['promo'], reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, txt['promo'], reply_markup=markup)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data in ['buy_1', 'buy_2'])
def handle_buy_click(call):
    user_id = str(call.message.chat.id)
    lang_code = data['langs'].get(user_id, 'EN')
    txt = TEXTS[lang_code]

    data['clicked'][user_id] = True
    save_data(data)
    update_user_activity(user_id)
    
    try:
        btn_key = call.data 
        url = LINKS[lang_code][btn_key]
    except:
        url = LINKS['EN']['buy_1']
    
    try: bot.answer_callback_query(call.id, text="Processing...")
    except: pass
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(txt['link_text'], url=url))
    bot.send_message(call.message.chat.id, txt['click_text'], reply_markup=markup)

# --- АДМІН СТАТИСТИКА (ОНОВЛЕНО) ---
@bot.message_handler(commands=['stats'])
def admin_stats(message):
    total = len(data['users'])
    
    # Логіка для "Цього місяця"
    now = datetime.now()
    active_this_month = 0
    
    for ts in data['users'].values():
        try:
            last_seen = datetime.fromisoformat(ts)
            # Перевіряємо, чи співпадає місяць і рік з поточним
            if last_seen.month == now.month and last_seen.year == now.year:
                active_this_month += 1
        except:
            pass

    paid = len([k for k, v in data['paid'].items() if v])
    clicked = len([k for k, v in data['clicked'].items() if v])
    
    stats_text = (
        f"📊 **STATISTICS**\n\n"
        f"👥 Total Users: {total}\n"
        f"📅 Active (This Month): {active_this_month}\n"
        f"💰 Paid Users: {paid}\n"
        f"🔗 Clicked Link: {clicked}"
    )
    bot.reply_to(message, stats_text, parse_mode="Markdown")

@bot.message_handler(commands=['paid'])
def set_paid(message):
    try:
        target = message.text.split()[1] if len(message.text.split()) > 1 else str(message.chat.id)
        data['paid'][target] = True
        save_data(data)
        bot.reply_to(message, f"User {target} set to PAID")
    except: pass

@bot.message_handler(commands=['unpaid'])
def set_unpaid(message):
    try:
        target = message.text.split()[1] if len(message.text.split()) > 1 else str(message.chat.id)
        data['paid'][target] = False
        save_data(data)
        bot.reply_to(message, f"User {target} set to UNPAID")
    except: pass

# --- REMINDERS ---
def reminder_worker():
    while True:
        time.sleep(4 * 3600)
        users_to_remind = [u for u in data['users'] if not data['paid'].get(u) and not data['clicked'].get(u)]
        for user_id in users_to_remind:
            try:
                lang = data['langs'].get(user_id, 'EN')
                txt = TEXTS[lang]
                text = random.choice(txt['soft'] + txt['hard'])
                photo = get_user_photo(user_id)
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton(txt['btn1'], callback_data="buy_1"))
                if photo:
                    with open(photo, 'rb') as p: bot.send_photo(user_id, p, caption=text, reply_markup=markup)
                else:
                    bot.send_message(user_id, text, reply_markup=markup)
                time.sleep(0.5)
            except: pass

threading.Thread(target=reminder_worker, daemon=True).start()

# --- СТАРТ ---
if __name__ == "__main__":
    if not os.path.exists(PHOTOS_DIR): os.makedirs(PHOTOS_DIR)
    print("Bot is running...")
    bot.infinity_polling()
