import os
import time
import json
import random
from telebot import TeleBot
from openai import OpenAI, RateLimitError, OpenAIError

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is missing")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY env var is missing")

bot = TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"

LINK_29 = "https://buy.stripe.com/9B6eV63Sy2oscYtgR8c3m05"  # 29 MXN
LINK_39 = "https://buy.stripe.com/4gM5kw60G0gk6A5bwOc3m04"  # 39 MXN lifetime

MEX_CITIES = ["CDMX", "Guadalajara", "Monterrey", "Puebla", "Cancún", "Tijuana"]

# ================= STORAGE =================
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

users = load_users()

def save_users():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ================= HUMAN-LIKE =================
def human_delay(text: str):
    base = random.uniform(2.5, 6.0)
    extra = min(len(text) / 28, 6)
    time.sleep(base + extra)

def maybe_read_and_silence():
    # "прочитала, але мовчить"
    return random.random() < 0.16

def maybe_double_message():
    return random.random() < 0.32

def sexy_extra():
    return random.choice(["😈", "👀", "💦", "🔥", "mmm…", "😏", "…"])

# ================= AGE GATE =================
YES_WORDS = {
    "yes", "y", "yeah", "yep", "si", "sí", "simon", "claro", "ok", "okay",
    "да", "так", "ага", "звісно", "okey"
}
NO_WORDS = {"no", "nop", "не", "ні"}

def normalize(s: str) -> str:
    return "".join(ch.lower() for ch in s.strip())

def detect_age_confirm(text: str):
    t = normalize(text)
    # basic: "18", "18+", "tengo 18", "soy mayor", "i'm 18"
    if "18" in t or "18+" in t:
        return True
    tokens = set(t.replace("¿", "").replace("?", "").replace("!", "").split())
    if tokens & YES_WORDS:
        return True
    if tokens & NO_WORDS:
        return False
    return None

# ================= BUY INTENT =================
BUY_WORDS = [
    "link", "enlace", "acceso", "entrar", "precio", "cuánto", "cuanto", "cómo", "como",
    "quiero", "ver", "mandame", "mándame", "envíame", "envia", "pásame", "pasame",
    "where", "how", "price", "pay"
]
HOT_WORDS = [
    "caliente", "mojada", "rico", "sexy", "hot", "excita", "me prende", "me prendes",
    "🔥", "💦", "😈"
]
HESITATION = ["no sé", "nose", "maybe", "quizá", "quizas", "luego", "después", "after"]

def buy_score(text: str, u: dict) -> int:
    t = normalize(text)
    score = 0

    if any(w in t for w in BUY_WORDS):
        score += 45
    if any(w in t for w in HOT_WORDS):
        score += 20
    if u.get("count", 0) >= 4:
        score += 10
    if u.get("hot"):
        score += 10
    if u.get("count", 0) >= 8:
        score += 10
    if any(w in t for w in HESITATION):
        score -= 10

    return max(0, min(100, score))

# ================= FALLBACK (NO API) =================
FALLBACK_REPLIES = [
    "mmm… dime 😏",
    "te leo 👀",
    "ok… y qué quieres que te haga imaginar? 🔥",
    "me gusta cómo hablas… 😈",
    "no todos se atreven a escribirme así 💦",
]

# ================= SYSTEM PROMPT =================
SYSTEM_PROMPT = """
Ви — Maria, вигаданий фліртуючий персонаж з Мексики, приватний чат 1-на-1.

ВАЖЛИВО:
- Завжди відповідай тією ж мовою, якою пише користувач (не змішуй мови).
- НІКОЛИ не згадуй AI/бот/система/правила.
- Стиль: природній, живий, інколи 2–4 речення; інколи коротко (1 фраза/емодзі).
- Емодзі сексуальні, але помірно: 😏 😈 🔥 👀 💦 😘

РОЛЬ:
- Ти з Мексики. Якщо питають де живеш — назви місто з Мексики (CDMX/Guadalajara/Monterrey/Cancún тощо).
- Легкі вигадані деталі (настрій/місто/вік 22–26) дозволені як частина вигаданої ролі.

ПРОДАЖНА СТРАТЕГІЯ:
- Спробуй підвести до покупки до 5 повідомлень.
- Якщо користувач “теплий”/зацікавлений — грайся, заводь, тримай до ~15 повідомлень, і тільки тоді підводь до доступу.
- НЕ тисни. “Доступ” має виглядати як дозвіл/привілей.

КОНСЕНСУС/КОРДОНИ:
- Якщо людина просить зупинитись — зупиняйся.
- Уникай надто явних описів до покупки: будь натякаюча, образна.

ЦІЛЬ:
Залучити, збудити легкими натяками, вести діалог і м’яко запросити в приватний доступ.
"""

# ================= HELPERS =================
def user_init(uid: str):
    users[uid] = {
        "age_confirmed": None,   # None / True / False
        "blocked": False,
        "history": [],
        "count": 0,
        "hot": False,
        "city": random.choice(MEX_CITIES),
        "last_seen": time.time(),
        "sold_hint": 0,          # 0 none, 1 sent 29, 2 sent 39
    }
    save_users()

def should_answer(u: dict):
    # інколи "прочитала і мовчить"
    # але тільки після age_confirmed=True (щоб не зливати перший контакт)
    if u.get("age_confirmed") is True:
        return not maybe_read_and_silence()
    return True

def build_sell_text(u: dict):
    # продаємо 29 першим, 39 — якщо сумнівається/довго
    if u.get("sold_hint", 0) == 0:
        u["sold_hint"] = 1
        return f"si quieres entrar al privado hoy… 😈\n👉 {LINK_29}"
    else:
        u["sold_hint"] = 2
        return f"y si prefieres quedarte para siempre… 💦\n👉 {LINK_39}"

# ================= MAIN HANDLER =================
@bot.message_handler(func=lambda m: True)
def chat(message):
    uid = str(message.chat.id)
    text = (message.text or "").strip()
    if not text:
        return

    if uid not in users:
        user_init(uid)

    u = users[uid]
    u["last_seen"] = time.time()

    if u.get("blocked"):
        return

    # 1) AGE CHECK
    if u.get("age_confirmed") is None:
        # перший контакт: привіт + питання + 18+
        human_delay("hi")
        bot.send_message(
            message.chat.id,
            "hola 😏\nAntes de seguir… confirma que eres 18+ 😉"
        )
        u["age_confirmed"] = "asked"
        save_users()
        return

    if u.get("age_confirmed") == "asked":
        ans = detect_age_confirm(text)
        if ans is True:
            u["age_confirmed"] = True
            save_users()
            human_delay("ok")
            bot.send_message(
                message.chat.id,
                random.choice([
                    "bien… entonces dime 😈 ¿qué te gusta más… fotos o videos? 👀",
                    "perfecto 😏 ¿vienes curioso o vienes con ganas? 💦",
                    "ok… ahora sí 😈 ¿qué te trajo a escribirme?"
                ])
            )
            return
        if ans is False:
            u["age_confirmed"] = False
            u["blocked"] = True
            save_users()
            bot.send_message(message.chat.id, "Lo siento, no puedo continuar. Cuídate.")
            return

        # не зрозуміло — ще раз
        bot.send_message(message.chat.id, "Solo para estar segura… eres 18+? 😉")
        return

    if u.get("age_confirmed") is not True:
        return

    # 2) HUMAN-LIKE SILENCE
    if not should_answer(u):
        save_users()
        return

    # 3) Update counters / hotness
    u["count"] += 1
    tnorm = normalize(text)
    if any(w in tnorm for w in HOT_WORDS):
        u["hot"] = True
    score = buy_score(text, u)

    # 4) Decide mode: sell fast by msg<=5, but keep hot user to 15
    if score >= 75:
        mode = "sell_now"
    elif score >= 50:
        mode = "almost"
    else:
        mode = "tease"

    # If user is hot, delay selling until ~15 unless they ask link/price
    asked_buy = any(w in tnorm for w in BUY_WORDS)
    if u["hot"] and u["count"] < 15 and not asked_buy and score < 75:
        mode = "tease"

    # If cold and we are within first 5 messages, push faster
    if (not u["hot"]) and u["count"] <= 5 and not asked_buy:
        mode = "almost"

    # 5) Build AI response
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # pin city if asked
        if "donde" in tnorm or "dónde" in tnorm or "where" in tnorm:
            messages.append({"role": "system", "content": f"Tu ciudad: {u['city']} (México)."})
        # add steering
        if mode == "sell_now":
            messages.append({"role": "system", "content": "He is ready. Invite to access now, short and seductive."})
        elif mode == "almost":
            messages.append({"role": "system", "content": "Tease + 1 question. If he agrees, invite to access."})
        else:
            messages.append({"role": "system", "content": "Keep it flirty and engaging. Ask a good question."})

        for h in u["history"][-10:]:
            messages.append(h)

        messages.append({"role": "user", "content": text})

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.95,
            max_tokens=180
        )
        reply = (resp.choices[0].message.content or "").strip()
        if not reply:
            reply = random.choice(FALLBACK_REPLIES)

    except (RateLimitError, OpenAIError):
        reply = random.choice(FALLBACK_REPLIES)

    # 6) When to drop link (smart)
    # - immediate if sell_now or user asked
    # - otherwise by message 3–5 unless hot and we decided to tease
    add_link = False
    if mode == "sell_now" or asked_buy:
        add_link = True
    elif (not u["hot"]) and (3 <= u["count"] <= 5):
        add_link = True
    elif u["hot"] and u["count"] >= 12:
        add_link = True

    if add_link:
        # send 29 first; if already sent, sometimes upsell 39
        sell_text = build_sell_text(u)
        reply = f"{reply}\n\n{sell_text}"

        # upsell lifetime if hesitates or already talked a lot
        if (u["count"] >= 8 or "luego" in tnorm or "después" in tnorm) and u.get("sold_hint", 0) == 1:
            if random.random() < 0.55:
                reply += f"\n\n{build_sell_text(u)}"

    # 7) Send message with human delay
    human_delay(reply)
    bot.send_message(message.chat.id, reply)

    # 8) sometimes second short message
    if maybe_double_message():
        time.sleep(random.uniform(1.6, 3.6))
        bot.send_message(message.chat.id, sexy_extra())

    # 9) Save history
    u["history"].append({"role": "user", "content": text})
    u["history"].append({"role": "assistant", "content": reply})
    save_users()

# ================= RUN =================
print("Bot is running...")
bot.polling(non_stop=True)
