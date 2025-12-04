import logging
import os
import asyncio
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
            logger.info(f"📨 Message from {user_id}: {update.message.text}")
            
            # /start команда
            if update.message.text == '/start':
                user_sessions[user_id] = {'step': 'event_type'}
                asyncio.create_task(application.bot.send_message(
                    chat_id=user_id,
                    text="🍾 <b>Добро пожаловать в Алкоголь.Калькулятор!</b>\n\nВыберите тип события:",
                    parse_mode='HTML',
                    reply_markup=get_event_buttons()
                ))
                logger.info(f"✅ Start sent to {user_id}")
            
            # Обработка числовых ответов (количество гостей)
            elif user_id in user_sessions and 'event_type' in user_sessions[user_id]:
                try:
                    num = int(update.message.text)
                    
                    # Первое число - общее количество гостей
                    if 'guests_total' not in user_sessions[user_id]:
                        user_sessions[user_id]['guests_total'] = num
                        asyncio.create_task(application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Гостей: {num}\n\nВведите количество мужчин:"
                        ))
                    # Второе число - количество мужчин
                    else:
                        user_sessions[user_id]['guests_male'] = num
                        user_sessions[user_id]['drinks'] = []
                        asyncio.create_task(application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Мужчин: {num}\n\nВыберите напитки (можно выбрать несколько):",
                            reply_markup=get_drinks_buttons()
                        ))
                except ValueError:
                    asyncio.create_task(application.bot.send_message(
                        chat_id=user_id,
                        text="❌ Пожалуйста, введите число!"
                    ))
        
        # Обработка кнопок (callback_query)
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            data_value = update.callback_query.data
            logger.info(f"🔘 Callback from {user_id}: {data_value}")
            
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            
            # Выбор типа события
            if data_value.startswith('evt_'):
                event_type = data_value.replace('evt_', '')
                user_sessions[user_id]['event_type'] = event_type
                asyncio.create_task(application.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=update.callback_query.message.message_id,
                    text=f"✅ Выбрано: {event_type}\n\nВыберите формат события:",
                    reply_markup=get_format_buttons(),
                    parse_mode='HTML'
                ))
            
            # Выбор формата
            elif data_value.startswith('fmt_'):
                event_format = data_value.replace('fmt_', '')
                user_sessions[user_id]['event_format'] = event_format
                asyncio.create_task(application.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=update.callback_query.message.message_id,
                    text=f"✅ Выбрано: {event_format}\n\nВыберите длительность:",
                    reply_markup=get_duration_buttons(),
                    parse_mode='HTML'
                ))
            
            # Выбор длительности
            elif data_value.startswith('dur_'):
                duration = data_value.replace('dur_', '')
                user_sessions[user_id]['duration'] = duration
                asyncio.create_task(application.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=update.callback_query.message.message_id,
                    text=f"✅ Длительность: {duration}\n\n👥 Введите общее количество гостей:",
                    parse_mode='HTML'
                ))
            
            # Выбор напитков
            elif data_value.startswith('drk_'):
                drink = data_value.replace('drk_', '')
                
                if drink == 'done':
                    if 'drinks' not in user_sessions[user_id] or not user_sessions[user_id]['drinks']:
                        asyncio.create_task(application.bot.answer_callback_query(
                            callback_query_id=update.callback_query.id,
                            text="❌ Выберите хотя бы один напиток!",
                            show_alert=True
                        ))
                        return 'ok', 200
                    
                    asyncio.create_task(application.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=update.callback_query.message.message_id,
                        text="💰 Выберите ценовую категорию:",
                        reply_markup=get_price_buttons(),
                        parse_mode='HTML'
                    ))
                else:
                    if 'drinks' not in user_sessions[user_id]:
                        user_sessions[user_id]['drinks'] = []
                    
                    if drink not in user_sessions[user_id]['drinks']:
                        user_sessions[user_id]['drinks'].append(drink)
                    
                    drinks_list = ", ".join(user_sessions[user_id]['drinks'])
                    asyncio.create_task(application.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=update.callback_query.message.message_id,
                        text=f"✅ Выбранные напитки: {drinks_list}\n\nДобавьте еще или нажмите 'Готово':",
                        reply_markup=get_drinks_buttons(),
                        parse_mode='HTML'
                    ))
            
            # Выбор ценовой категории
            elif data_value.startswith('prc_'):
                price_category = data_value.replace('prc_', '')
                user_sessions[user_id]['price_category'] = price_category
                
                try:
                    result = calculate_alcohol(user_sessions[user_id])
                    message_text = format_result(result)
                    
                    asyncio.create_task(application.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=update.callback_query.message.message_id,
                        text=message_text,
                        parse_mode='HTML'
                    ))
                    
                    asyncio.create_task(application.bot.send_message(
                        chat_id=user_id,
                        text="🔄 Нажмите /start для нового расчета"
                    ))
                    logger.info(f"✅ Result sent to {user_id}")
                except Exception as e:
                    logger.error(f"Error calculating for {user_id}: {e}")
                    asyncio.create_task(application.bot.send_message(
                        chat_id=user_id,
                        text="❌ Ошибка при расчете. Попробуйте еще раз: /start"
                    ))
        
        return 'ok', 200
    
    except Exception as e:
        logger.error(f"🔴 Webhook error: {e}", exc_info=True)
        return 'error', 500

# ========== УСТАНОВКА WEBHOOK ==========

async def set_webhook():
    try:
        webhook_url = f"{TELEGRAM_WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

# ========== MAIN ==========

if __name__ == '__main__':
    try:
        asyncio.run(set_webhook())
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
    
    logger.info("🚀 Bot started!")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, threaded=True)
