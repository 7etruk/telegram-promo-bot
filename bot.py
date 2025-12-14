import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, os, time, random, threading
from datetime import datetime, timedelta
from flask import Flask
from openai import OpenAI

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run_web, daemon=True).start()

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_KEY)

STATS_FILE = "stats.json"
MAX_MEMORY = 6   # скільки повідомлень памʼяті зберігаємо

# ================= DATA =================
def empty_data():
    return {
        "users": {},       # first_seen, last_seen, visits
        "langs": {},       # user language
        "started": {},     # user passed /start
        "paid": {},
        "clicked": {},
        "ai_msgs": {},     # AI message count
        "memory": {}       # dialog memory
    }

def load():
    if not os.path.exists(STATS_FILE):
        return empty_data()
    try:
        return json.load(open(STATS_FILE))
    except:
        return empty_data()

def save():
    json.dump(data, open(STATS_FILE, "w"), indent=2)

data = load()

# ================= USER TRACK =================
def touch(uid):
    uid = str(uid)
    now = datetime.now().isoformat()
    if uid not in data["users"]:
        data["users"][uid] = {
            "first_seen": now,
            "last_seen": now,
            "visits": 1
        }
    else:
        data["users"][uid]["last_seen"] = now
        data["users"][uid]["visits"] += 1
    save()

# ================= START =================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.chat.id)
    touch(uid)

    data["started"][uid] = True
    data["memory"][uid] = []
    data["ai_msgs"][uid] = 0
    save()

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇲🇽 Español", callback_data="lang_MX"),
        InlineKeyboardButton("🇧🇷 Português", callback_data="lang_BR"),
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_EN")
    )

    bot.send_message(
        msg.chat.id,
        "Choose language / Elige idioma / Escolha idioma:",
        reply_markup=kb
    )

# ================= LANGUAGE =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_lang(c):
    uid = str(c.message.chat.id)
    lang = c.data.split("_")[1]

    data["langs"][uid] = lang
    save()

    bot.send_message(
        c.message.chat.id,
        "Hey 😘 write me something…"
    )
    bot.delete_message(c.message.chat.id, c.message.message_id)

# ================= BUY BUTTON =================
@bot.callback_query_handler(func=lambda c: c.data == "buy")
def buy(c):
    uid = str(c.message.chat.id)
    data["clicked"][uid] = data["clicked"].get(uid, 0) + 1
    save()

    bot.send_message(
        c.message.chat.id,
        "Access is private and instant 😈\nPress when ready 👇"
    )

# ================= AI SYSTEM PROMPT =================
SYSTEM_PROMPT = """
You are a flirty, playful, charming woman chatting privately in Telegram.
Rules:
- Be natural, short, friendly
- Ask questions
- Light emojis 😘🔥
- NO explicit sexual content
- NO prices
- NO payment links
- Suggest private access gently after 2–4 messages
"""

# ================= AI CHAT =================
@bot.message_handler(func=lambda m: True)
def ai_chat(msg):
    uid = str(msg.chat.id)
    text = msg.text

    # ❌ AI тільки після /start
    if not data["started"].get(uid):
        bot.send_message(msg.chat.id, "Press /start first 😘")
        return

    # ❌ якщо вже платив — AI мовчить
    if data["paid"].get(uid):
        return

    touch(uid)

    # памʼять
    memory = data["memory"].get(uid, [])
    memory.append({"role": "user", "content": text})
    memory = memory[-MAX_MEMORY:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + memory

    try:
        r = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=120
        )

        reply = r.choices[0].message.content

        # додаємо відповідь AI в памʼять
        memory.append({"role": "assistant", "content": reply})
        memory = memory[-MAX_MEMORY:]

        data["memory"][uid] = memory
        data["ai_msgs"][uid] += 1
        save()

        time.sleep(random.uniform(1, 2))
        bot.send_message(msg.chat.id, reply)

        # кнопка продажу після 3 AI відповідей
        if data["ai_msgs"][uid] == 3:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔥 Private access", callback_data="buy"))
            bot.send_message(msg.chat.id, "Want to see more? 😘", reply_markup=kb)

    except Exception as e:
        print("AI error:", e)

# ================= STATS =================
@bot.message_handler(commands=["stats"])
def stats(msg):
    total = len(data["users"])
    paid = len([u for u, v in data["paid"].items() if v])
    clicks = sum(data["clicked"].values()) if data["clicked"] else 0

    bot.send_message(
        msg.chat.id,
        f"📊 STATS\n\n"
        f"Users: {total}\n"
        f"Paid: {paid}\n"
        f"Clicks: {clicks}"
    )

# ================= RUN =================
print("Bot running...")
bot.infinity_polling()
