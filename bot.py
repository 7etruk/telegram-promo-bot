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

MEX_CITIES = [
    "CDMX", "Guadalajara", "Monterrey",
    "Puebla", "Cancún", "Tijuana"
]
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
    base = random.uniform(2.5, 6.0)
    extra = min(len(text) / 28, 6)
    time.sleep(base + extra)

def read_and_silence():
    return random.random() < 0.18

def double_message():
    return random.random() < 0.35

# ---------- BUY INTENT ----------
BUY_WORDS = [
    "link", "acceso", "entrar", "precio", "cuánto", "cómo",
    "quiero", "ver", "mándame", "envíame", "pay"
]

HORNY_WORDS = [
    "caliente", "mojada", "rico", "sexo", "coger",
    "hot", "sexy", "fuck", "wet"
]

def buy_score(text, user):
    t = text.lower()
    score = 0
    if any(w in t for w in BUY_WORDS): score += 40
    if any(w in t for w in HORNY_WORDS): score += 20
    if user["count"] >= 5: score += 10
    if user.get("hot"): score += 10
    if user["count"] >= 8: score += 10
    return score

# ---------- FALLBACK ----------
FALLBACK = [
    "mmm… dime 😈",
    "te leo 💦",
    "me estás provocando 👀",
    "no me escriben así todos…",
    "y qué harías si estuviera contigo ahora? 😏"
]

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
You are a fictional woman chatting privately 1-on-1.

You are from Mexico.
If asked where you live, you answer with a random Mexican city.
You are playful, seductive, confident.

Rules:
- Always reply in the SAME language as the user.
- Never mention AI, bots or systems.
- Sometimes lie lightly to keep fantasy (age, city, mood).
- Use sexy emojis 😈💦🔥👀
- Ask engaging, provocative questions.

Sales logic:
- Try to sell by message 3–5.
- If user is very interested, tease up to 15 messages.
- Access is a privilege, not a product.

Prices:
29 MXN today
39 MXN lifetime

Goal:
Arouse, engage, and guide naturally to paid private access.
"""

# ---------- MAIN ----------
@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = str(message.chat.id)
    text = message.text.strip()

    # ---------- NEW USER ----------
    if uid not in users:
        users[uid] = {
            "history": [],
            "count": 0,
            "hot": False,
            "city": random.choice(MEX_CITIES)
        }
        save()
        time.sleep(random.uniform(3, 6))
        bot.send_message(
            message.chat.id,
            random.choice([
                "hola… 😌 qué te hizo escribirme?",
                "hey 👀 estabas mirando o querías algo más?",
                "mmm hola 😈 dime qué se te antoja"
            ])
        )
        return

    user = users[uid]

    if read_and_silence():
        return

    user["count"] += 1
    if any(w in text.lower() for w in HORNY_WORDS):
        user["hot"] = True

    score = buy_score(text, user)

    if score >= 70:
        mode = "sell_now"
    elif score >= 45:
        mode = "almost"
    else:
        mode = "tease"

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in user["history"][-10:]:
            messages.append(h)

        if "dónde" in text.lower() or "where" in text.lower():
            messages.append({
                "role": "system",
                "content": f"You live in {user['city']}, Mexico."
            })

        if mode == "sell_now":
            messages.append({
                "role": "system",
                "content": "He is ready. Invite to access now."
            })
        elif mode == "almost":
            messages.append({
                "role": "system",
                "content": "Tease once more, then invite softly."
            })

        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.95,
            max_tokens=160
        )

        reply = response.choices[0].message.content.strip()

    except (RateLimitError, OpenAIError):
        reply = random.choice(FALLBACK)

    if mode == "sell_now":
        reply += f"\n\n👉 {LINK_29}"
        if random.random() < 0.4:
            reply += f"\n\nsi quieres quedarte conmigo siempre… 😈\n👉 {LINK_39}"

    human_delay(reply)
    bot.send_message(message.chat.id, reply)

    if double_message():
        time.sleep(random.uniform(1.5, 3.5))
        bot.send_message(message.chat.id, random.choice(["😈", "mmm…", "💦", "👀"]))

    user["history"].append({"role": "user", "content": text})
    user["history"].append({"role": "assistant", "content": reply})
    save()

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
