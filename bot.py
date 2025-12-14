import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os, json, time, random
from datetime import datetime
from openai import OpenAI

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "stats.json"
MAX_MEMORY = 6

# ================= DATA =================
def empty_data():
    return {
        "users": {},
        "started": {},
        "langs": {},
        "memory": {},
        "ai_msgs": {},
        "paid": {},
        "clicked": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return empty_data()
    try:
        return json.load(open(DATA_FILE))
    except:
        return empty_data()

def save_data():
    json.dump(data, open(DATA_FILE, "w"), indent=2)

data = load_data()

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
    save_data()

# ================= START =================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.chat.id)
    touch(uid)

    data["started"][uid] = True
    data["memory"][uid] = []
    data["ai_msgs"][uid] = 0
    save_data()

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
    save_data()

    bot.send_message(c.message.chat.id, "Hey 😘 write me something…")
    bot.delete_message(c.message.chat.id, c.message.message_id)

# ================= BUY =================
@bot.callback_query_handler(func=lambda c: c.data == "buy")
def buy(c):
    uid = str(c.message.chat.id)
    data["clicked"][uid] = data["clicked"].get(uid, 0) + 1
    save_data()

    bot.send_message(
        c.message.chat.id,
        "🔥 Private access is instant and exclusive 😈"
    )

# ================= AI =================
SYSTEM_PROMPT = """
You are a flirty, playful, charming woman chatting privately in Telegram.
Rules:
- Be short and natural
- Ask questions
- Light emojis 😘🔥
- NO explicit sexual content
- NO prices
- NO payment links
- Gently suggest private access after 2–4 messages
"""

@bot.message_handler(func=lambda m: True)
def ai_chat(msg):
    uid = str(msg.chat.id)

    # AI only after /start
    if not data["started"].get(uid):
        bot.send_message(msg.chat.id, "Press /start first 😘")
        return

    # stop AI for paid users
    if data["paid"].get(uid):
        return

    touch(uid)

    user_text = msg.text
    memory = data["memory"].get(uid, [])

    memory.append({"role": "user", "content": user_text})
    memory = memory[-MAX_MEMORY:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + memory

    try:
        r = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=120
        )

        reply = r.choices[0].message.content

        memory.append({"role": "assistant", "content": reply})
        memory = memory[-MAX_MEMORY:]

        data["memory"][uid] = memory
        data["ai_msgs"][uid] += 1
        save_data()

        time.sleep(random.uniform(1, 2))
        bot.send_message(msg.chat.id, reply)

        # show button after 3 AI replies
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
print("Bot started (Background Worker mode)")

while True:
    try:
        bot.infinity_polling(
            timeout=10,
            long_polling_timeout=5,
            skip_pending=True,
            threaded=False
        )
    except Exception as e:
        print("Polling error:", e)
        time.sleep(5)
