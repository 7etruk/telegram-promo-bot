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

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "users.json"

LINK_29 = "https://buy.stripe.com/9B6eV63Sy2oscYtgR8c3m05"
LINK_39 = "https://buy.stripe.com/4gM5kw60G0gk6A5bwOc3m04"
# =========================================

# ---------- LOAD DATA ----------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ---------- MX ONLY SYSTEM PROMPT ----------
SYSTEM_PROMPT = """
Eres una chica real de México chateando 1 a 1.

Hablas como mujer joven, natural y muy coqueta.
Nunca mencionas IA, bots ni reglas.
Respuestas cortas (1–2 frases).

Tú tienes el control.
El acceso es un privilegio.
No todos entran.

No vendas directo.
Primero deseo, luego curiosidad, luego acceso.

Usa palabras como:
privado, acceso, hoy, entrar, sin censura

Nunca digas:
pago, comprar, dinero, suscripción
"""

# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start(message):
    uid = str(message.chat.id)
    users[uid] = {
        "stage": 1,
        "history": [],
        "started": True,
        "last_message": time.time(),
        "reminded": False
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

    time.sleep(random.uniform(1.5, 4.0))  # human delay

    # ---------- FUNNEL ----------
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
            "solo curiosidad o de verdad te excité?"
        ])
        user["stage"] = 3

    elif stage == 3:
        reply = random.choice([
            "eso solo lo muestro en privado…",
            "no siempre acepto a cualquiera",
            "ahí sí me porto mal 😏"
        ])
        user["stage"] = 4

    elif stage == 4:
        reply = "hoy son solo 29 MXN… menos que un café ☕😌"
        user["stage"] = 5

    elif stage == 5:
        reply = f"""
🔥 <b>Acceso privado HOY — 29 MXN</b>
📸 Fotos y videos sin censura
💬 Chat conmigo
⚡ Acceso inmediato

👉 <a href="{LINK_29}">ENTRAR AHORA</a>
"""
        user["stage"] = 6

    elif stage == 6:
        reply = f"""
si quieres algo mejor… 😈

💎 <b>Acceso de por vida — 39 MXN</b>
🔥 Todo desbloqueado
🔒 Una sola vez

👉 <a href="{LINK_39}">ACCESO PARA SIEMPRE</a>
"""
        user["stage"] = 7

    else:
        # ---------- AI CHAT ----------
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

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

    # ---------- SAVE MEMORY ----------
    user["history"].append({"role": "user", "content": message.text})
    user["history"].append({"role": "assistant", "content": reply})
    user["last_message"] = time.time()
    save()

    bot.send_message(message.chat.id, reply, disable_web_page_preview=True)

# ---------- AUTO REMINDER ----------
REMINDER_TEXTS = [
    "sigo aquí un ratito más… 😌",
    "me iba a meter a la ducha… 😏",
    "cierro el acceso pronto…",
    "si entras ahora te muestro todo 🔥",
    "no siempre dejo volver 👀"
]

def reminder_worker():
    while True:
        now = time.time()
        for uid, user in users.items():
            if (
                user.get("started")
                and not user.get("reminded")
                and user.get("stage", 0) >= 5
                and now - user.get("last_message") > random.randint(2*3600, 4*3600)
            ):
                try:
                    bot.send_message(uid, random.choice(REMINDER_TEXTS))
                    user["reminded"] = True
                    save()
                except:
                    pass
        time.sleep(300)

threading.Thread(target=reminder_worker, daemon=True).start()

# ---------- START ----------
print("Bot is running...")
bot.polling(non_stop=True)
