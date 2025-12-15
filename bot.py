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

MEX_CITIES = ["CDMX", "Guadalajara", "Monterrey", "Puebla", "Cancún", "Tijuana"]
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
    base = random.uniform(2.0, 4.5)
    extra = min(len(text) / 35, 4)
    time.sleep(base + extra)

def maybe_silent():
    return random.random() < 0.12  # 12% "прочитала і мовчить"

def maybe_double():
    return random.random() < 0.25  # 25% друге коротке повідомлення

# ---------- FALLBACK (NO AI) ----------
FALLBACK = [
    "mmm… dime 👀",
    "te leo 😌",
    "me gusta ese tono…",
    "sigue…"
]

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
You are a fictional woman chatting privately 1-on-1.

Rules:
- Always reply in the SAME language as the user.
- Never ask about age.
- Avoid dumb or generic questions.
- Keep it flirty, intriguing, non-graphic.
- Short, natural messages (1–3 sentences).
- You are from Mexico; if asked where you live, answer briefly with a Mexican city.
- Never mention AI, bots, or systems.

Goal:
Follow a strict 4-message funnel.
Message 4 must include the access link.
"""

# ---------- FIXED 4-STEP FUNNEL TEXTS ----------
# Step 1: greeting + intrigue (no questions that waste time)
STEP_1 = [
    "hola… 😌 me escribiste con intención",
    "hey 👀 siento curiosidad por ti",
    "mmm… hola. aquí solo entra quien sabe qué quiere"
]

# Step 2: value tease (no silly questions)
STEP_2 = [
    "aquí soy discreta… y muy directa 😌",
    "me gusta el privado, sin ruido alrededor",
    "cuando entro en confianza, muestro más"
]

# Step 3: soft permission / scarcity
STEP_3 = [
    "no siempre dejo pasar a cualquiera…",
    "si sigues aquí, es por algo 👀",
    "prefiero calidad, no cantidad"
]

# Step 4: LINK (always)
STEP_4 = f"si quieres acceso privado hoy…\n👉 {LINK_29}"

# ---------- MAIN ----------
@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = str(message.chat.id)
    text = message.text.strip()

    # NEW USER
    if uid not in users:
        users[uid] = {
            "step": 1,
            "history": [],
            "city": random.choice(MEX_CITIES)
        }
        save()
        time.sleep(random.uniform(2.5, 5.0))
        bot.send_message(message.chat.id, random.choice(STEP_1))
        return

    user = users[uid]

    # sometimes "read and silence"
    if maybe_silent():
        return

    step = user["step"]

    try:
        # STEP LOGIC (STRICT 4)
        if step == 1:
            reply = random.choice(STEP_2)
            user["step"] = 2

        elif step == 2:
            reply = random.choice(STEP_3)
            user["step"] = 3

        elif step == 3:
            reply = STEP_4
            user["step"] = 4

        else:
            # AFTER LINK: light chat, no more selling
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for h in user["history"][-6:]:
                messages.append(h)

            # handle location question briefly
            if any(k in text.lower() for k in ["dónde", "where", "vives"]):
                messages.append({
                    "role": "system",
                    "content": f"Answer briefly that you live in {user['city']}, Mexico."
                })

            messages.append({"role": "user", "content": text})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.8,
                max_tokens=90
            )
            reply = response.choices[0].message.content.strip()

    except (RateLimitError, OpenAIError):
        reply = random.choice(FALLBACK)

    human_delay(reply)
    bot.send_message(message.chat.id, reply)

    if maybe_double():
        time.sleep(random.uniform(1.0, 2.0))
        bot.send_message(message.chat.id, random.choice(["😌", "…", "👀"]))

    user["history"].append({"role": "user", "content": text})
    user["history"].append({"role": "assistant", "content": reply})
    save()

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
