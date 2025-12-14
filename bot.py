import os
import time
import json
import random
from telebot import TeleBot
from openai import OpenAI, RateLimitError, OpenAIError

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
    base = random.uniform(2.5, 5.0)
    extra = min(len(text) / 35, 5)
    time.sleep(base + extra)

def read_and_silence():
    return random.random() < 0.15  # 15% "прочитала і мовчить"

def double_message():
    return random.random() < 0.25

# ---------- FALLBACK PHRASES (NO AI) ----------
FALLBACK_REPLIES = [
    "mmm… dime 😌",
    "te leo 👀",
    "qué te provoca ahora?",
    "no me escriben así todos…",
    "y eso por qué? 😏"
]

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
You are a real woman chatting privately 1-on-1.

Always reply in the SAME language as the user.
Never mention AI, bots or systems.

Messages can be 2–4 sentences sometimes.
You ask natural questions.
You tease before inviting to private access.

Personalities:
Sweet – warm, playful, curious.
Bold – confident, provocative, dominant.

Goal:
Up to ~15 messages of natural chat,
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
            "history": [],
            "msg_count": 0,
            "personality": random.choice(["Sweet", "Bold"]),
            "started": True
        }
        save()

        # AUTO GREETING + QUESTION
        time.sleep(random.uniform(3, 6))
        greeting = random.choice([
            "hola… 😌 qué te trajo por aquí?",
            "hey… 👀 estabas mirando o buscando algo?",
            "mmm… hola 😏 qué te provocó escribirme?"
        ])
        bot.send_message(message.chat.id, greeting)
        return

    user = users[uid]

    # ---------- READ BUT SILENT ----------
    if read_and_silence():
        return

    user["msg_count"] += 1

    # ---------- AI RESPONSE ----------
    try:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + f"\nPersonality: {user['personality']}"
            }
        ]

        for h in user["history"][-10:]:
            messages.append(h)

        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.9,
            max_tokens=120
        )

        reply = response.choices[0].message.content.strip()

    except RateLimitError:
        # 🔥 FALLBACK WHEN QUOTA EXCEEDED
        reply = random.choice(FALLBACK_REPLIES)

    except OpenAIError:
        reply = random.choice(FALLBACK_REPLIES)

    # ---------- SEND ----------
    human_delay(reply)
    bot.send_message(message.chat.id, reply)

    if double_message():
        time.sleep(random.uniform(1.5, 3.0))
        bot.send_message(message.chat.id, random.choice(["😏", "mmm…", "👀"]))

    # ---------- SAVE ----------
    user["history"].append({"role": "user", "content": text})
    user["history"].append({"role": "assistant", "content": reply})
    save()

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
