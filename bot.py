import telebot
from telebot import types

TOKEN = "8381533144:AAFf6H4FjyEVbs-MSp7B3IBzqMKhLva0f4o"

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_promo(message):

    photo = open("promo.jpg", "rb")

    text = (
        "PROMO DE NATAL DA LARAH🎄❤️🔥\n\n"
        "Oi, tesão 😏 calma que eu te explico... hoje é diferente.\n"
        "Tá tudo borrado aqui porque é só o gostinho do que te espera completo — "
        "e esse mês vai ter PROMOÇÃO de natal com vagas limitadas, "
        "você pode ter tudo por um preço que vai te deixar suando.\n\n"
        "ENTÃO CORRE PRA GARANTIR SUA VAGA e ver eu FANTASIADA DE MAMAE NOEL SÓ PRA VOCÊ🔥😈\n\n"
        "🎥 Vídeos completos, sem cortes, sem censura e cheios de tesão — com desconto exclusivo por tempo LIMITADO!\n\n"
        "Quem deixar passar… vai passar o resto do mês imaginando o que perdeu. 👀\n\n"
        "E se não conseguir pagar me chama no suporte 👉 @laraoficial"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💗 Exclusive WhatsApp Access (ONLY 18+) R$11,97🔥", url="https://www.mariamoments.com/checkouts/cn/hWN6Jvmvt2IlLNqxt7cd0yH3/en-ua?_r=AQABDGmwQ_zl-Ob2_e4B2Q40YUPl7SN2y-Ca6EStQGrfIIk&preview_theme_id=157844832476"))
    kb.add(types.InlineKeyboardButton("💗 HARD Exclusive WhatsApp Access (ONLY 18+) R$14,97🍑", url="https://www.mariamoments.com/checkouts/cn/hWN6JvtmdIWclh1bDPpLhNon/en-ua?_r=AQABS9ZgBxs59yvSWr_gxtKQut1eBtvnApjLyxbq9w3ohTY&preview_theme_id=157844832476"))

    bot.send_photo(
        message.chat.id,
        photo,
        caption=text,
        reply_markup=kb,
        parse_mode="HTML"
    )


bot.polling(none_stop=True)
