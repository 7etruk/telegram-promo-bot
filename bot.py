import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta

# --- КОНФІГУРАЦІЯ ---
# Отримання токена зі змінних середовища (для Render) або вставте вручну нижче
TOKEN = os.environ.get('BOT_TOKEN', 'ВСТАВ_СВІЙ_ТОКЕН_ТУТ')

bot = telebot.TeleBot(TOKEN)

STATS_FILE = 'stats.json'
PHOTOS_DIR = 'photos'

# URLS
BUY_LINK_1 = "https://www.mariamoments.com/checkouts/cn/hWN6Jvmvt2IlLNqxt7cd0yH3/en-ua?_r=AQABDGmwQ_zl-Ob2_e4B2Q40YUPl7SN2y-Ca6EStQGrfIIk&preview_theme_id=157844832476"
BUY_LINK_2 = "https://www.mariamoments.com/checkouts/cn/hWN6JvtmdIWclh1bDPpLhNon/en-ua?_r=AQABS9ZgBxs59yvSWr_gxtKQut1eBtvnApjLyxbq9w3ohTY&preview_theme_id=157844832476"

# ТЕКСТИ
TEXTS = {
    'EN': {
        'promo': "EXCLUSIVE CHRISTMAS PROMO: Get your special gift now!",
        'btn1': "Buy Package 1",
        'btn2': "Buy Package 2",
        'soft': ["Hey! Don't miss out on this deal.", "Your Christmas gift is waiting!"],
        'hard': ["LAST CHANCE! Offer expires soon.", "Hurry up! Discount ending."]
    },
    'MX': {
        'promo': "PROMO DE NAVIDAD: ¡Obtén tu regalo especial ahora!",
        'btn1': "Comprar Paquete 1",
        'btn2': "Comprar Paquete 2",
        'soft': ["¡Hola! No te pierdas esta oferta.", "¡Tu regalo de Navidad te espera!"],
        'hard': ["¡ÚLTIMA OPORTUNIDAD! La oferta expira pronto.", "¡Date prisa! El descuento termina."]
    },
    'BR': {
        'promo': "PROMO DE NATAL DA LARAH: Pegue seu presente especial agora!",
        'btn1': "Comprar Pacote 1",
        'btn2': "Comprar Pacote 2",
        'soft': ["Oi! Não perca essa oferta.", "Seu presente de Natal está esperando!"],
        'hard': ["ÚLTIMA CHANCE! A oferta expira em breve.", "Corra! O desconto está acabando."]
    }
}

# --- РОБОТА З ДАНИМИ ---

def load_data():
    if not os.path.exists(STATS_FILE):
        return {
            "users": {},      # user_id: timestamp (last seen)
            "photos": {},     # user_id: filename
            "langs": {},      # user_id: lang_code
            "paid": {},       # user_id: bool
            "clicked": {}     # user_id: bool
        }
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": {}, "photos": {}, "langs": {}, "paid": {}, "clicked": {}}

def save_data(data):
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Ініціалізація даних
data = load_data()

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def get_random_photo_file():
    try:
        files = [f for f in os.listdir(PHOTOS_DIR) if os.path.isfile(os.path.join(PHOTOS_DIR, f))]
        if not files:
            return None
        return os.path.join(PHOTOS_DIR, random.choice(files))
    except FileNotFoundError:
        print(f"Помилка: Папка {PHOTOS_DIR} не знайдена!")
        return None

def get_user_photo(user_id):
    user_id = str(user_id)
    # Якщо у юзера вже є фото, повертаємо його
    if user_id in data['photos']:
        photo_path = data['photos'][user_id]
        if os.path.exists(photo_path):
            return photo_path
    
    # Якщо немає або файл зник - призначаємо нове
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
    
    # Зберігаємо мову
    data['langs'][user_id] = lang_code
    save_data(data)
    
    # Отримуємо фото (закріплене за юзером)
    photo_path = get_user_photo(user_id)
    
    # Тексти
    txt = TEXTS[lang_code]
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(txt['btn1'], callback_data="buy_1"))
    markup.add(InlineKeyboardButton(txt['btn2'], callback_data="buy_2"))
    
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=txt['promo'], reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, txt['promo'], reply_markup=markup)
            
        # Видаляємо повідомлення з вибором мови, щоб не засмічувати чат
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
    except Exception as e:
        print(f"Error sending promo: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ['buy_1', 'buy_2'])
def handle_buy_click(call):
    user_id = str(call.message.chat.id)
    
    # Зберігаємо факт кліку
    data['clicked'][user_id] = True
    save_data(data)
    update_user_activity(user_id)
    
    # Визначаємо URL
    url = BUY_LINK_1 if call.data == 'buy_1' else BUY_LINK_2
    
    # Редірект через answer_callback_query
    bot.answer_callback_query(call.id, text="Redirecting...", url=url)

# --- АДМІН КОМАНДИ ---

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    total_users = len(data['users'])
    
    # Рахуємо активних за останні 30 днів
    active_30_days = 0
    now = datetime.now()
    for ts in data['users'].values():
        try:
            last_seen = datetime.fromisoformat(ts)
            if now - last_seen <= timedelta(days=30):
                active_30_days += 1
        except:
            pass
            
    stats_text = (
        f"📊 **STATISTICS**\n"
        f"Total Users: {total_users}\n"
        f"Active (last 30 days): {active_30_days}\n"
        f"Paid Users: {len([k for k, v in data['paid'].items() if v])}\n"
        f"Clicked Users: {len([k for k, v in data['clicked'].items() if v])}"
    )
    bot.reply_to(message, stats_text, parse_mode="Markdown")

@bot.message_handler(commands=['paid'])
def set_paid(message):
    # Використання: /paid (у відповідь на повідомлення юзера або просто для себе, тут ставимо поточного для тесту)
    # В реальності краще передавати ID: /paid 123456789
    try:
        args = message.text.split()
        if len(args) > 1:
            target_id = args[1]
        else:
            target_id = str(message.chat.id) # Самі собі
            
        data['paid'][target_id] = True
        save_data(data)
        bot.reply_to(message, f"User {target_id} marked as PAID.")
    except Exception as e:
        bot.reply_to(message, "Error. Use: /paid user_id")

@bot.message_handler(commands=['unpaid'])
def set_unpaid(message):
    try:
        args = message.text.split()
        if len(args) > 1:
            target_id = args[1]
        else:
            target_id = str(message.chat.id)
            
        data['paid'][target_id] = False
        save_data(data)
        bot.reply_to(message, f"User {target_id} marked as UNPAID.")
    except Exception as e:
        bot.reply_to(message, "Error. Use: /unpaid user_id")

# --- ФОНОВИЙ ПОТІК РЕМАЙНДЕРІВ ---

def reminder_worker():
    while True:
        # Чекаємо 4 години (4 * 60 * 60)
        time.sleep(4 * 3600)
        # Для тестів можна поставити time.sleep(60) - 1 хвилина
        
        print("Running reminder check...")
        users_to_remind = []
        
        # Перевіряємо умови
        # NOT paid AND NOT clicked
        for user_id in list(data['users'].keys()):
            is_paid = data.get('paid', {}).get(user_id, False)
            is_clicked = data.get('clicked', {}).get(user_id, False)
            
            if not is_paid and not is_clicked:
                users_to_remind.append(user_id)
        
        for user_id in users_to_remind:
            try:
                lang = data.get('langs', {}).get(user_id, 'EN') # Default EN
                
                # Об'єднуємо soft і hard
                options = TEXTS[lang]['soft'] + TEXTS[lang]['hard']
                text = random.choice(options)
                
                photo_path = get_user_photo(user_id)
                
                # Кнопки додаємо теж, щоб міг купити
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton(TEXTS[lang]['btn1'], callback_data="buy_1"))
                
                if photo_path:
                    with open(photo_path, 'rb') as p:
                        bot.send_photo(user_id, p, caption=text, reply_markup=markup)
                else:
                    bot.send_message(user_id, text, reply_markup=markup)
                
                # Невелика пауза, щоб не заблокував телеграм за спам
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"Failed to remind user {user_id}: {e}")

# Запуск потоку
reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
reminder_thread.start()

# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    print("Bot started...")
    # Створюємо папку photos якщо немає
    if not os.path.exists(PHOTOS_DIR):
        os.makedirs(PHOTOS_DIR)
        
    bot.infinity_polling()
