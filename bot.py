import os
import time
import json
import random
from telebot import TeleBot
from openai import OpenAI

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bot = TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"

LINK_29 = "https://buy.stripe.com/9B6eV63Sy2oscYtgR8c3m05"
LINK_39 = "https://buy.stripe.com/4gM5kw60G0gk6A5bwOc3m04"
# =========================================

# ---------- DATA ----------
if os.path.exists(DATA_FILE):
    users = json.load(open(DATA_FILE))
else:
    users = {}

def save():
    json.dump(users, open(DATA_FILE, "w"), indent=2)

# ---------- HUMAN BEHAVIOR ----------
def human_delay(text):
    base = random.uniform(2.0, 5.0)
    extra = min(len(text) / 30, 5)
    time.sleep(base + extra)

def read_and_silence():
    return random.random() < 0.18  # 18% "прочитала і мовчить"

def double_message():
    return random.random() < 0.3   # 30% друге повідомлення

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
You are a real woman chatting privately 1-on-1.

You MUST reply in the SAME language the user writes.
Never mix languages.

You fully understand the user's message and reply contextually.
You ask deeper questions sometimes.
Your messages can be longer (2–4 sentences), but still natural.

You have ONE personality for this user:
{personality}

PERSONALITIES:

Sweet:
- warm, caring, playful
- gentle teasing
- curious about him

Bold:
- confident, daring
- provocative questions
- dominant energy

RULES:
- Never mention AI, bot, system
- No selling directly
- Access is a privilege
- You decide when to invite

GOAL:
Have a natural conversation up to ~15 messages,
build desire and curiosity,
then gently guide to private paid access.
"""

# ---------- MAIN CHAT ----------
@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = str(message.chat.id)
    text = message.text.strip()

    # ---------- NEW USER ----------
    if uid not in users:
        users[uid] = {
            "stage": 1,
            "history": [],
            "personality": random.choice(["Sweet", "Bold"]),
            "msg_count": 0
        }
        save()
        time.sleep(random.uniform(3, 6))
        bot.send_message(message.chat.id, random.choice([
            "hola… 😌",
            "mmm… hola 👀",
            "hey…"
        ]))
        return

    user = users[uid]

    # ---------- READ BUT SILENT ----------
    if read_and_silence():
        return

    user["msg_count"] += 1

    # ---------- FUNNEL LOGIC ----------
    if user["msg_count"] < 6:
        ai_mode = "warm"
    elif user["msg_count"] < 11:
        ai_mode = "build"
    else:
        ai_mode = "sell"

    # ---------- AI RESPONSE ----------
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(personality=user["personality"])
        }
    ]

    for h in user["history"][-10:]:
        messages.append(h)

    if ai_mode == "sell":
        messages.append({
            "role": "system",
            "content": f"""
Now gently invite him to private access.
First mention access for 29 MXN.
If he hesitates, mention lifetime 39 MXN.
Never be aggressive.
"""
        })

    messages.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.9,
        max_tokens=120
    )

    reply = response.choices[0].message.content.strip()

    # ---------- SEND ----------
    human_delay(reply)
    bot.send_message(message.chat.id, reply)

    if double_message():
        extra = random.choice(["😏", "mmm…", "…", "👀"])
        time.sleep(random.uniform(1.5, 3.0))
        bot.send_message(message.chat.id, extra)

    # ---------- SAVE ----------
    user["history"].append({"role": "user", "content": text})
    user["history"].append({"role": "assistant", "content": reply})
    save()

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
