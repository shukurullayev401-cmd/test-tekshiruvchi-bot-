
import os
import re
import json
import telebot

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

bot = telebot.TeleBot(TOKEN)

# Hozircha kalitlar xotirada saqlanadi
answer_keys = {}

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Test tekshiruvchi bot!\n\n"
        "/kalit - javob kalitini yaratish\n"
        "/test - testni tekshirish"
    )

@bot.message_handler(commands=["kalit"])
def kalit(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "Faqat o'qituvchi foydalana oladi.")
        return

    msg = bot.reply_to(
        message,
        "Test kodini yuboring (masalan: MAT1):"
    )
    bot.register_next_step_handler(msg, kalit_kod)

def kalit_kod(message):
    code = message.text.strip().upper()
    msg = bot.reply_to(
        message,
        "1–35 yopiq savol kalitlarini yuboring.\n"
        "Masalan: 1A2B3C...35D"
    )
    bot.register_next_step_handler(msg, yopiq_kalit, code)

def yopiq_kalit(message, code):
    pairs = re.findall(r"(\d+)([A-D])", message.text.upper())
    keys = {int(n): a for n, a in pairs if 1 <= int(n) <= 35}

    if len(keys) != 35:
        bot.reply_to(message, "35 ta yopiq javobni to'liq kiriting.")
        return

    msg = bot.reply_to(
        message,
        "36–45 ochiq savollar uchun 20 ta javobni kiriting.\n"
        "Format: 36a=javob,36b=javob;37a=javob,37b=javob;...\n"
        "Har bir savolda ikkita javob bo'ladi."
    )
    bot.register_next_step_handler(msg, ochiq_kalit, code, keys)

def ochiq_kalit(message, code, keys):
    text = message.text.lower()
    pairs = re.findall(r"(\d+)([ab])\s*=\s*([^,;\n]+)", text)
    open_keys = {
        (int(n), part): ans.strip()
        for n, part, ans in pairs
        if 36 <= int(n) <= 45
    }

    if len(open_keys) != 20:
        bot.reply_to(
            message,
            "20 ta javobni to'liq kiriting. "
            "Har savol uchun a va b javoblari kerak."
        )
        return

    answer_keys[code] = {"closed": keys, "open": open_keys}
    bot.reply_to(message, f"{code} test kaliti saqlandi!")

@bot.message_handler(commands=["test"])
def test(message):
    msg = bot.reply_to(message, "Test kodini yuboring:")
    bot.register_next_step_handler(msg, test_kod)

def test_kod(message):
    code = message.text.strip().upper()
    if code not in answer_keys:
        bot.reply_to(message, "Test kodi topilmadi.")
        return

    msg = bot.reply_to(
        message,
        "Yopiq javoblar: 1A2B3C...35D ko'rinishida yuboring."
    )
    bot.register_next_step_handler(msg, yopiq_javob, code)

def yopiq_javob(message, code):
    pairs = re.findall(r"(\d+)([A-D])", message.text.upper())
    answers = {int(n): a for n, a in pairs if 1 <= int(n) <= 35}

    if len(answers) != 35:
        bot.reply_to(message, "35 ta yopiq javobni to'liq yuboring.")
        return

    closed_score = sum(
        1 for n, a in answers.items()
        if answer_keys[code]["closed"].get(n) == a
    )

    msg = bot.reply_to(
        message,
        "Endi 10 ta ochiq savolning 20 ta javobini yuboring.\n"
        "Format: 36a=javob,36b=javob;37a=javob,37b=javob;..."
    )
    bot.register_next_step_handler(msg, ochiq_javob, code, closed_score)

def ochiq_javob(message, code, closed_score):
    pairs = re.findall(r"(\d+)([ab])\s*=\s*([^,;\n]+)", message.text.lower())
    answers = {
        (int(n), part): ans.strip()
        for n, part, ans in pairs
        if 36 <= int(n) <= 45
    }

    keys = answer_keys[code]["open"]
    open_score = sum(
        2 for k, ans in answers.items()
        if keys.get(k) == ans
    )

    total = closed_score + open_score
    percent = total / 75 * 100

    bot.reply_to(
        message,
        f"Yopiq testlar: {closed_score}/35\n"
        f"Ochiq savollar: {open_score}/40\n"
        f"Jami: {total}/75 ball\n"
        f"Natija: {percent:.2f}%"
    )

bot.infinity_polling()
