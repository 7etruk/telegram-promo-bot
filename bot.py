import os
import time
import json
import random
from telebot import TeleBot
from openai import OpenAI

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"
PRICE_TEXT = "🔥 Acceso privado HOY: 29 MXN"
BUY_LINK = "https://buy.stripe.com/XXXXXXXX"  # <-- ВСТАВ СВІЙ ЛІНК
# ============================================

# ---------- DATA ----------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
You are a real girl chatting 1-on-1.
Language: Spanish (Mexico).
Style rules:
- short messages (1–2 sentences)
- flirty, natural, human
- no AI mentions
- no explanations
- tease before selling
- sometimes delay answers
Goal:
Warm the user and lead to paid private access in 4–10 messages.
"""

# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.chat.id)
    users[uid] = {
        "stage": 1,
        "history": [],
        "started": True
    }
    save()
    bot.send_message(message.chat.id, "hola 😏")

# ---------- MAIN CHAT ----------
@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = str(message.chat.id)

    if uid not in users or not users[uid].get("started"):
        return

    user = users[uid]
    stage = user["stage"]

    # delay to look human
    time.sleep(random.uniform(1.5, 4.0))

    # ---------- STAGES ----------
    if stage == 1:
        reply = random.choice([
            "te gustó lo que viste? 👀",
            "mmm… qué te trajo aquí?",
            "no todos llegan hasta aquí 😌"
        ])
        user["stage"] = 2

    elif stage == 2:
        reply = random.choice([
            "te gusta más lo suave… o lo sucio? 😈",
            "prefieres fotos o videos?",
            "solo curiosidad o de verdad te excito?"
        ])
        user["stage"] = 3

    elif stage == 3:
        reply = random.choice([
            "eso solo lo muestro en privado…",
            "no es gratis, pero vale la pena",
            "no siempre acepto a cualquiera"
        ])
        user["stage"] = 4

    elif stage == 4:
        reply = f"{PRICE_TEXT}\nmenos que un café ☕"
        user["stage"] = 5

    elif stage == 5:
        reply = f"""
📸 Fotos y videos sin censura
🔥 Chat conmigo
⚡ Acceso inmediato

👉 <a href="{BUY_LINK}">ENTRAR AHORA</a>
"""
        user["stage"] = 6

    else:
        # ---------- AI FREE CHAT ----------
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        for h in user["history"][-6:]:
            messages.append(h)

        messages.append({"role": "user", "content": message.text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=60,
            temperature=0.9
        )

        reply = response.choices[0].message.content

    # save memory
    user["history"].append({"role": "user", "content": message.text})
    user["history"].append({"role": "assistant", "content": reply})
    save()

    bot.send_message(message.chat.id, reply, disable_web_page_preview=True)

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
