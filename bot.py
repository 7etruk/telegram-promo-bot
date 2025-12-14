import os
import time
import json
import random
import threading
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
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ---------- HUMAN BEHAVIOR ----------
def human_delay(text):
    base = random.uniform(1.5, 4.0)
    extra = min(len(text) / 35, 4)
    time.sleep(base + extra)

def maybe_silent():
    return random.random() < 0.12  # 12% шанс мовчати

def maybe_double_message():
    return random.random() < 0.25  # 25% шанс другого повідомлення

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
You are a real woman chatting privately 1-on-1.

You ALWAYS reply in the SAME language the user uses.
If the user writes Spanish — reply Spanish.
If Portuguese — Portuguese.
If English — English.

Style:
- very natural
- short messages (1 sentence usually)
- flirty, calm, confident
- sometimes only 1–2 words
- sometimes just emoji
- NEVER mention AI, bot, system

Behavior:
- you don't reply instantly
- sometimes you ignore a message
- sometimes you send two short messages
- you tease before giving access

Goal:
Make the chat feel real and slowly lead to private paid access.
"""

# ---------- MAIN CHAT ----------
@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = str(message.chat.id)
    text = message.text.strip()

    # --- new user ---
    if uid not in users:
        users[uid] = {
            "stage": 1,
            "history": [],
            "last_message": time.time(),
            "reminded": False
        }
        save()
        time.sleep(random.uniform(2.5, 5.0))
        bot.send_message(message.chat.id, "hola 😏")
        return

    user = users[uid]

    # sometimes ignore
    if maybe_silent():
        return

    # ---------- FUNNEL LOGIC ----------
    stage = user["stage"]

    if stage == 1:
        reply = random.choice([
            "te gustó lo que viste? 👀",
            "mmm… qué te trajo aquí?",
            "solo miras o quieres algo más?"
        ])
        user["stage"] = 2

    elif stage == 2:
        reply = random.choice([
            "te gusta lo suave… o lo sucio? 😈",
            "prefieres fotos o videos?",
            "te calienta más imaginar o ver?"
        ])
        user["stage"] = 3

    elif stage == 3:
        reply = random.choice([
            "eso solo lo muestro en privado…",
            "no todos entran ahí 😌",
            "ahí sí me porto mal"
        ])
        user["stage"] = 4

    elif stage == 4:
        reply = "hoy son solo 29 MXN… menos que un café ☕"
        user["stage"] = 5

    elif stage == 5:
        reply = f"entra aquí si quieres verme sin censura 😈\n{LINK_29}"
        user["stage"] = 6

    elif stage == 6:
        reply = f"si quieres quedarte para siempre…\n{LINK_39}"
        user["stage"] = 7

    else:
        # ---------- AI RESPONSE ----------
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for h in user["history"][-8:]:
            messages.append(h)

        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.9,
            max_tokens=80
        )

        reply = response.choices[0].message.content.strip()

    # ---------- SEND ----------
    human_delay(reply)
    bot.send_message(message.chat.id, reply)

    # sometimes send second short message
    if maybe_double_message():
        extra = random.choice(["😏", "mmm…", "👀", "…"])
        time.sleep(random.uniform(1.2, 2.5))
        bot.send_message(message.chat.id, extra)

    # ---------- SAVE MEMORY ----------
    user["history"].append({"role": "user", "content": text})
    user["history"].append({"role": "assistant", "content": reply})
    user["last_message"] = time.time()
    save()

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
