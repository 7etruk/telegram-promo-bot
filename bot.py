import os
import time
import json
import random
from telebot import TeleBot
from openai import OpenAI, RateLimitError, OpenAIError

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Missing BOT_TOKEN or OPENAI_API_KEY")

bot = TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"

LINK_29 = "https://buy.stripe.com/9B6eV63Sy2oscYtgR8c3m05"
LINK_39 = "https://buy.stripe.com/4gM5kw60G0gk6A5bwOc3m04"

MEX_CITIES = ["CDMX", "Guadalajara", "Monterrey", "Cancún", "Puebla"]

# ================== STORAGE ==================
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            return json.load(open(DATA_FILE, "r", encoding="utf-8"))
        except:
            return {}
    return {}

users = load_users()

def save_users():
    json.dump(users, open(DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ================== HUMAN BEHAVIOR ==================
def human_delay(text):
    time.sleep(random.uniform(2.5, 5.5) + min(len(text) / 30, 5))

def silent_read():
    return random.random() < 0.15

def double_msg():
    return random.random() < 0.30

def sexy_ping():
    return random.choice(["😈", "👀", "💦", "😏", "mmm…"])

# ================== AGE CHECK ==================
YES = {"yes", "sí", "si", "ok", "okay", "claro", "simon", "18", "18+"}
NO = {"no", "not", "menor"}

def age_answer(text):
    t = text.lower()
    if any(w in t for w in YES):
        return True
    if any(w in t for w in NO):
        return False
    return None

# ================== BUY INTENT ==================
BUY_WORDS = ["link", "precio", "acceso", "entrar", "ver", "pagar", "pay"]
HOT_WORDS = ["hot", "caliente", "sexy", "rico", "🔥", "💦"]

def buy_score(text, u):
    t = text.lower()
    score = 0
    if any(w in t for w in BUY_WORDS): score += 40
    if any(w in t for w in HOT_WORDS): score += 20
    if u["count"] >= 3: score += 10
    if u["hot"]: score += 10
    return score

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = """
You are Maria — a fictional, confident, flirty woman from Mexico,
chatting privately 1-on-1 with an adult user (18+).

CRITICAL LANGUAGE RULE:
- You MUST reply ONLY in the SAME language the user uses.
- NEVER switch or mix languages.
- NEVER translate.

AGE GATE:
Before any flirting, you MUST confirm the user is 18+.
If not confirmed clearly, stop the conversation politely.

ROLE:
- Fictional persona.
- From Mexico (random city if asked).
- Never mention AI, bot, system, or automation.

STYLE:
- Flirty, teasing, confident.
- Sexy emojis used sparingly 😏 😈 🔥 👀 💦
- Short, natural replies.

SALES STRATEGY:
- Push toward sale within 3–5 messages.
- ABSOLUTE MAXIMUM: 10 messages.
- If user asks price/link → sell immediately.
- Access feels exclusive, not forced.

CONTENT:
- Suggestive, not explicit.
- Build imagination before selling.

GOAL:
Convert chat into paid access quickly and naturally.
"""

# ================== INIT USER ==================
def init_user(uid):
    users[uid] = {
        "age": None,
        "blocked": False,
        "count": 0,
        "hot": False,
        "history": [],
        "city": random.choice(MEX_CITIES),
        "sold": 0
    }
    save_users()

# ================== MAIN HANDLER ==================
@bot.message_handler(func=lambda m: True)
def chat(m):
    uid = str(m.chat.id)
    text = (m.text or "").strip()
    if not text:
        return

    if uid not in users:
        init_user(uid)

    u = users[uid]
    if u["blocked"]:
        return

    # AGE GATE
    if u["age"] is None:
        human_delay("hi")
        bot.send_message(m.chat.id, "Antes de seguir… confirma que eres 18+ 😉")
        u["age"] = "asked"
        save_users()
        return

    if u["age"] == "asked":
        ans = age_answer(text)
        if ans is True:
            u["age"] = True
            save_users()
            human_delay("ok")
            bot.send_message(m.chat.id, "Perfecto 😏 dime… ¿qué te trajo a escribirme?")
            return
        if ans is False:
            u["blocked"] = True
            save_users()
            bot.send_message(m.chat.id, "Lo siento, no puedo continuar.")
            return
        bot.send_message(m.chat.id, "Solo para estar segura… eres 18+?")
        return

    # HUMAN SILENCE
    if silent_read():
        return

    u["count"] += 1
    if any(w in text.lower() for w in HOT_WORDS):
        u["hot"] = True

    score = buy_score(text, u)

    if u["count"] >= 10:
        return

    # DECIDE SELL
    sell_now = score >= 60 or any(w in text.lower() for w in BUY_WORDS) or u["count"] >= 5

    # AI RESPONSE
    try:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        if "donde" in text.lower() or "where" in text.lower():
            msgs.append({"role": "system", "content": f"You live in {u['city']}, Mexico."})
        for h in u["history"][-6:]:
            msgs.append(h)
        msgs.append({"role": "user", "content": text})

        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            temperature=0.95,
            max_tokens=140
        )
        reply = r.choices[0].message.content.strip()
    except (RateLimitError, OpenAIError):
        reply = random.choice(["mmm… 😏", "te leo 👀", "me estás tentando 💦"])

    # ADD SELL LINK
    if sell_now:
        if u["sold"] == 0:
            reply += f"\n\n👉 {LINK_29}"
            u["sold"] = 1
        elif u["sold"] == 1 and random.random() < 0.5:
            reply += f"\n\n👉 {LINK_39}"
            u["sold"] = 2

    human_delay(reply)
    bot.send_message(m.chat.id, reply)

    if double_msg():
        time.sleep(random.uniform(1.5, 3))
        bot.send_message(m.chat.id, sexy_ping())

    u["history"].append({"role": "user", "content": text})
    u["history"].append({"role": "assistant", "content": reply})
    save_users()

# ================== RUN ==================
print("Bot is running…")
bot.polling(non_stop=True)
