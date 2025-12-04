import logging
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv
from calculator import calculate_alcohol, format_result
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL, FLASK_HOST, FLASK_PORT

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

START, EVENT_TYPE, FORMAT_DURATION, GUESTS, DRINKS, PRICE = range(6)

user_sessions = {}

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
        [InlineKeyboardButton("2-3 часа", callback_data="dur_2-3"), InlineKeyboardButton("3-4 часа", callback_data="dur_3-4")],
        [InlineKeyboardButton("4-5 часов", callback_data="dur_4-5"), InlineKeyboardButton("5+ часов", callback_data="dur_5+")]
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {'step': 'event_type'}
    
    await update.message.reply_text(
        "🍾 <b>Добро пожаловать в Алкоголь.Калькулятор!</b>\n\n"
        "Выберите тип события:",
        parse_mode='HTML',
        reply_markup=get_event_buttons()
    )
    return EVENT_TYPE

async def handle_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    event_type = query.data.replace("evt_", "")
    
    user_sessions[user_id]['event_type'] = event_type
    
    await query.edit_message_text(
        f"✅ Выбрано: {event_type}\n\n"
        "Выберите формат события:",
        parse_mode='HTML',
        reply_markup=get_format_buttons()
    )
    return FORMAT_DURATION

async def handle_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data.startswith("fmt_"):
        event_format = query.data.replace("fmt_", "")
        user_sessions[user_id]['event_format'] = event_format
        
        await query.edit_message_text(
            f"✅ Выбрано: {event_format}\n\n"
            "Выберите длительность:",
            parse_mode='HTML',
            reply_markup=get_duration_buttons()
        )
    elif query.data.startswith("dur_"):
        duration = query.data.replace("dur_", "")
        user_sessions[user_id]['duration'] = duration
        
        await query.edit_message_text(
            "👥 Введите общее количество гостей:",
            parse_mode='HTML'
        )
        return GUESTS

async def handle_guests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    try:
        total_guests = int(update.message.text)
        user_sessions[user_id]['guests_total'] = total_guests
        
        await update.message.reply_text(
            f"✅ Гостей: {total_guests}\n\n"
            "Введите количество мужчин:"
        )
        return GUESTS
    except ValueError:
        await update.message.reply_text("❌ Введите число!")
        return GUESTS

async def handle_male_guests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    try:
        male_guests = int(update.message.text)
        user_sessions[user_id]['guests_male'] = male_guests
        
        await update.message.reply_text(
            f"✅ Мужчин: {male_guests}\n\n"
            "Выберите напитки (можно выбрать несколько):",
            reply_markup=get_drinks_buttons()
        )
        user_sessions[user_id]['drinks'] = []
        return DRINKS
    except ValueError:
        await update.message.reply_text("❌ Введите число!")
        return GUESTS

async def handle_drinks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data.startswith("drk_"):
        drink = query.data.replace("drk_", "")
        
        if drink == "done":
            await query.edit_message_text(
                "💰 Выберите ценовую категорию:",
                reply_markup=get_price_buttons()
            )
            return PRICE
        else:
            if drink not in user_sessions[user_id]['drinks']:
                user_sessions[user_id]['drinks'].append(drink)
            
            drinks_list = ", ".join(user_sessions[user_id]['drinks'])
            await query.edit_message_text(
                f"✅ Выбранные напитки: {drinks_list}\n\n"
                "Добавьте еще или нажмите 'Готово':",
                reply_markup=get_drinks_buttons()
            )

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    price_category = query.data.replace("prc_", "")
    
    user_sessions[user_id]['price_category'] = price_category
    
    # Получить результат
    result = calculate_alcohol(user_sessions[user_id])
    message_text = format_result(result)
    
    await query.edit_message_text(
        message_text,
        parse_mode='HTML'
    )
    
    await query.message.reply_text(
        "Нажмите /start для нового расчета"
    )
    
    return ConversationHandler.END

async def webhook(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response(text="ok")

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update_data = request.get_json()
    update = Update.de_json(update_data, application.bot)
    import asyncio
    asyncio.run(application.process_update(update))
    return 'ok', 200

async def main():
    global application
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.COMMAND, start)],
        states={
            EVENT_TYPE: [CallbackQueryHandler(handle_event_type)],
            FORMAT_DURATION: [
                CallbackQueryHandler(handle_format, pattern="^fmt_"),
                CallbackQueryHandler(handle_format, pattern="^dur_")
            ],
            GUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_male_guests)],
            DRINKS: [CallbackQueryHandler(handle_drinks)],
            PRICE: [CallbackQueryHandler(handle_price)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, start)],
    )
    
    application.add_handler(conv_handler)
    
    webhook_url = f"{TELEGRAM_WEBHOOK_URL}/webhook"
    await application.bot.set_webhook(webhook_url)
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
