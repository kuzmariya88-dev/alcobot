import logging
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from dotenv import load_dotenv
from calculator import calculate_alcohol, format_result

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
FLASK_PORT = int(os.getenv('PORT', 5000))

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")

app = Flask(__name__)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

user_sessions = {}

# ========== КНОПКИ ==========

def get_event_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 День рождения", callback_data="evt_день_рождения")],
        [InlineKeyboardButton("💒 Свадьба", callback_data="evt_свадьба")],
        [InlineKeyboardButton("🎉 Корпоратив", callback_data="evt_корпоратив")],
        [InlineKeyboardButton("🍾 Вечеринка", callback_data="evt_вечеринка")],
        [InlineKeyboardButton("🎊 Юбилей", callback_data="evt_юбилей")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 Семейное", callback_data="evt_семейное")],
        [InlineKeyboardButton("📌 Другое", callback_data="evt_другое")]
    ])

def get_format_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍽️ Банкет", callback_data="fmt_банкет")],
        [InlineKeyboardButton("🥂 Фуршет", callback_data="fmt_фуршет")],
        [InlineKeyboardButton("🎪 Комбинированный", callback_data="fmt_комбинированный")]
    ])

def get_duration_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("2-3 часа", callback_data="dur_2-3"),
         InlineKeyboardButton("3-4 часа", callback_data="dur_3-4")],
        [InlineKeyboardButton("4-5 часов", callback_data="dur_4-5"),
         InlineKeyboardButton("5+ часов", callback_data="dur_5+")]
    ])

def get_drinks_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥂 Шампанское", callback_data="drk_champagne")],
        [InlineKeyboardButton("🍷 Вино белое", callback_data="drk_wine_white")],
        [InlineKeyboardButton("🍷 Вино красное", callback_data="drk_wine_red")],
        [InlineKeyboardButton("🥃 Виски", callback_data="drk_whiskey")],
        [InlineKeyboardButton("🥃 Коньяк", callback_data="drk_cognac")],
        [InlineKeyboardButton("✅ Готово", callback_data="drk_done")]
    ])

def get_price_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Стандарт (500₽)", callback_data="prc_стандарт")],
        [InlineKeyboardButton("⭐ Премиум (1100₽)", callback_data="prc_премиум")],
        [InlineKeyboardButton("👑 Люкс (2250₽)", callback_data="prc_люкс")],
        [InlineKeyboardButton("💎 Супер Люкс (4000₽)", callback_data="prc_супер_люкс")]
    ])

# ========== WEBHOOK ОБРАБОТЧИК ==========

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    try:
        data = request.get_json()
        update = Update.de_json(data, application.bot)

        user_id = None

        # Обработка текстовых сообщений
        if update.message:
            user_id = update.message.from_user.id
            text = update.message.text or ""
            logger.info(f"📨 Message from {user_id}: {text}")

            # /start команда
            if text == '/start':
                user_sessions[user_id] = {}
                application.bot.send_message(
                    chat_id=user_id,
                    text="🍾 <b>Добро пожаловать в Алкоголь.Калькулятор!</b>\n\nВыберите тип события:",
                    parse_mode='HTML',
                    reply_markup=get_event_buttons()
                )
                logger.info(f"✅ Start sent to {user_id}")
                return 'ok', 200

            # Обработка числовых ответов (количество гостей)
            if user_id in user_sessions:
                try:
                    num = int(text)

                    # Первое число - общее количество гостей
                    if 'guests_total' not in user_sessions[user_id]:
                        user_sessions[user_id]['guests_total'] = num
                        application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Гостей: {num}\n\nВведите количество мужчин:"
                        )
                    # Второе число - количество мужчин
                    else:
                        user_sessions[user_id]['guests_male'] = num
                        user_sessions[user_id]['drinks'] = []
                        application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Мужчин: {num}\n\nВыберите напитки (можно выбрать несколько):",
                            reply_markup=get_drinks_buttons()
                        )
                except ValueError:
