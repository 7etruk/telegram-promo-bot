import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta

# --- КОНФІГУРАЦІЯ ---
# Цей рядок автоматично знайде токен, як би ви його не назвали в Render (BOT_TOKEN або TOKEN)
TOKEN = os.environ.get('BOT_TOKEN', os.environ.get('TOKEN', 'ВСТАВ_СВІЙ_ТОКЕН_ТУТ'))

bot = telebot.TeleBot(TOKEN)

STATS_FILE = 'stats.json'
PHOTOS_DIR = 'photos'

# ВАШІ ПОСИЛАННЯ
BUY_LINK_1 = "https://www.mariamoments.com/checkouts/cn/hWN6Jvmvt2IlLNqxt7cd0yH3/en-ua?_r=AQABDGmwQ_zl-Ob2_e4B2Q40YUPl7SN2y-Ca6EStQGrfIIk&preview_theme_id=157844832476"
BUY_LINK_2 = "https://www.mariamoments.com/checkouts/cn/hWN6JvtmdIWclh1bDPpLhNon/en-ua?_r=AQABS9ZgBxs59yvSWr_gxtKQut1eBtvnApjLyxbq9w3ohTY&preview_theme_id=157844832476"

# --- ТЕКСТИ ТА ПЕРЕКЛАДИ КНОПОК ---
TEXTS = {
    'EN': {
        'promo': "EXCLUSIVE CHRISTMAS PROMO: Get your special gift now!",
        # Кнопки англійською
        'btn1': "💗 Exclusive WhatsApp Access (ONLY 18+)",
        'btn2': "💗 HARD Exclusive WhatsApp Access (ONLY 18+)",
        'link_text': "🔗 OPEN LINK NOW",
        'click_text': "👇 Click below to access:",
        'soft': ["Hey! Don't miss out on this deal.", "Your Christmas gift is waiting!"],
        'hard': ["LAST CHANCE! Offer expires soon.", "Hurry up! Discount ending."]
    },
    'MX': {
        'promo': "PROMO DE NAVIDAD: ¡Obtén tu regalo especial ahora!",
        # Кнопки іспанською (Мексика)
        'btn1': "💗 Acceso Exclusivo WhatsApp (SOLO 18+)",
        'btn2': "💗 Acceso HARD WhatsApp (SOLO 18+)",
        'link_text': "🔗 ABRIR ENLACE AHORA",
        'click_text': "👇 Haga clic abajo para acceder:",
        'soft': ["¡Hola! No te pierdas esta oferta.", "¡Tu regalo de Navidad te espera!"],
        'hard': ["¡ÚLTIMA OPORTUNIDAD! La oferta expira pronto.", "¡Date prisa! El descuento termina."]
    },
    'BR': {
        'promo': "PROMO DE NATAL DA LARAH: Pegue seu presente especial agora!",
        # Кнопки португальською (Бразилія)
        'btn1': "💗 Acesso Exclusivo WhatsApp (APENAS 18+)",
        'btn2': "💗 Acesso HARD WhatsApp (APENAS 18+)",
        'link_text': "🔗 ABRIR LINK AGORA",
        'click_text': "👇 Clique abaixo para acessar:",
        'soft': ["Oi! Não perca essa oferta.", "Seu presente de Natal está esperando!"],
        'hard': ["ÚLTIMA CHANCE! A oferta expira em breve.", "Corra! O desconto está acabando."]
    }
}

# --- РОБОТА З ДАНИМИ ---

def load_data():
    if not os.path.exists(STATS_FILE):
        return {"users": {}, "photos": {}, "langs": {}, "paid": {}, "clicked": {}}
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": {}, "photos": {}, "langs": {}, "paid": {}, "clicked": {}}

def save_data(data):
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

data = load_data()

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

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

# --- ОБРОБНИКИ (HANDLERS) ---

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
    
    # Зберігаємо вибрану мову
    data['langs'][user_id] = lang_code
    save_data(data)
    
    # Отримуємо фото і тексти для цієї мови
    photo_path = get_user_photo(user_id)
    txt = TEXTS[lang_code] 
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    # ОСЬ ТУТ КНОПКИ ТЕПЕР ПЕРЕКЛАДЕНІ
    markup.add(InlineKeyboardButton(txt['btn1'], callback_data="buy_1"))
    markup.add(InlineKeyboardButton(txt['btn2'], callback_data="buy_2"))
    
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=txt['promo'], reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, txt['promo'], reply_markup=markup)
        
        # Видаляємо меню вибору мови
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        print(f"Error sending promo: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ['buy_1', 'buy_2'])
def handle_buy_click(call):
    user_id = str(call.message.chat.id)
    
    # Визначаємо мову юзера, щоб відповісти йому правильною мовою
    lang_code = data['langs'].get(user_id, 'EN')
    txt = TEXTS[lang_code]

    data['clicked'][user_id] = True
    save_data(data)
    update_user_activity(user_id)
    
    url = BUY_LINK_1 if call.data == 'buy_1' else BUY_LINK_2
    
    # Відповідаємо телеграму, щоб кнопка не "крутилася"
    try:
        bot.answer_callback_query(call.id, text="Processing...")
    except: pass
    
    # Створюємо кнопку з посиланням
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(txt['link_text'], url=url))
    
    bot.send_message(call.message.chat.id, txt['click_text'], reply_markup=markup)

# --- АДМІН КОМАНДИ ---

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    total = len(data['users'])
    paid = len([k for k, v in data['paid'].items() if v])
    clicked = len([k for k, v in data['clicked'].items() if v])
    bot.reply_to(message, f"📊 STATS:\nTotal: {total}\nPaid: {paid}\nClicked: {clicked}")

@bot.message_handler(commands=['paid'])
def set_paid(message):
    try:
        target = message.text.split()[1] if len(message.text.split()) > 1 else str(message.chat.id)
        data['paid'][target] = True
        save_data(data)
        bot.reply_to(message, f"User {target} set to PAID")
    except: bot.reply_to(message, "Error")

@bot.message_handler(commands=['unpaid'])
def set_unpaid(message):
    try:
        target = message.text.split()[1] if len(message.text.split()) > 1 else str(message.chat.id)
        data['paid'][target] = False
        save_data(data)
        bot.reply_to(message, f"User {target} set to UNPAID")
    except: bot.reply_to(message, "Error")

# --- REMINDER WORKER (Розсилка кожні 4 години) ---

def reminder_worker():
    while True:
        time.sleep(4 * 3600) # Пауза 4 години
        
        users_to_remind = [u for u in data['users'] if not data['paid'].get(u) and not data['clicked'].get(u)]
        
        for user_id in users_to_remind:
            try:
                lang = data['langs'].get(user_id, 'EN')
                txt = TEXTS[lang]
                text = random.choice(txt['soft'] + txt['hard'])
                photo = get_user_photo(user_id)
                
                markup = InlineKeyboardMarkup()
                # Кнопка в нагадуванні теж перекладена
                markup.add(InlineKeyboardButton(txt['btn1'], callback_data="buy_1"))
                
                if photo:
                    with open(photo, 'rb') as p: bot.send_photo(user_id, p, caption=text, reply_markup=markup)
                else:
                    bot.send_message(user_id, text, reply_markup=markup)
                time.sleep(0.5)
            except: pass

# Запуск фонового процесу нагадувань
threading.Thread(target=reminder_worker, daemon=True).start()

# --- СТАРТ БОТА ---
if __name__ == "__main__":
    if not os.path.exists(PHOTOS_DIR): os.makedirs(PHOTOS_DIR)
    print("Bot is running...")
    bot.infinity_polling()
