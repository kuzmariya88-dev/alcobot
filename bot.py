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

def get_event_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 День рождения", callback_data="evt_day_birth")],
        [InlineKeyboardButton("💒 Свадьба", callback_data="evt_wedding")],
        [InlineKeyboardButton("🎉 Корпоратив", callback_data="evt_corp")],
        [InlineKeyboardButton("🍾 Вечеринка", callback_data="evt_party")],
        [InlineKeyboardButton("🎊 Юбилей", callback_data="evt_jubilee")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 Семейное", callback_data="evt_family")],
        [InlineKeyboardButton("📌 Другое", callback_data="evt_other")]
    ])

def get_format_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍽️ Банкет", callback_data="fmt_banquet")],
        [InlineKeyboardButton("🥂 Фуршет", callback_data="fmt_buffet")],
        [InlineKeyboardButton("🎪 Комбинированный", callback_data="fmt_combined")]
    ])

def get_duration_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("2-3ч", callback_data="dur_2-3"), InlineKeyboardButton("3-4ч", callback_data="dur_3-4")],
        [InlineKeyboardButton("4-5ч", callback_data="dur_4-5"), InlineKeyboardButton("5+ч", callback_data="dur_5+")]
    ])

def get_drinks_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥂 Шампанское", callback_data="drk_champagne")],
        [InlineKeyboardButton("🍷 Вино", callback_data="drk_wine")],
        [InlineKeyboardButton("🥃 Крепкое", callback_data="drk_strong")],
        [InlineKeyboardButton("✅ Готово", callback_data="drk_done")]
    ])

def get_price_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Стандарт (500₽)", callback_data="prc_std")],
        [InlineKeyboardButton("⭐ Премиум (1100₽)", callback_data="prc_prem")],
        [InlineKeyboardButton("👑 Люкс (2250₽)", callback_data="prc_lux")],
        [InlineKeyboardButton("💎 Супер Люкс (4000₽)", callback_data="prc_super")]
    ])

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    try:
        data = request.get_json()
        update = Update.de_json(data, application.bot)
        
        if update.message and update.message.text:
            user_id = update.message.from_user.id
            text = update.message.text
            logger.info(f"📨 Message from {user_id}: {text}")
            
            if text == '/start':
                user_sessions[user_id] = {}
                application.bot.send_message(
                    chat_id=user_id,
                    text="🍾 <b>Добро пожаловать!</b>\n\nВыберите тип события:",
                    parse_mode='HTML',
                    reply_markup=get_event_buttons()
                )
                logger.info(f"✅ Start sent to {user_id}")
            elif user_id in user_sessions:
                try:
                    num = int(text)
                    if 'guests_total' not in user_sessions[user_id]:
                        user_sessions[user_id]['guests_total'] = num
                        application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Гостей: {num}\n\nКол-во мужчин:"
                        )
                    else:
                        user_sessions[user_id]['guests_male'] = num
                        user_sessions[user_id]['drinks'] = []
                        application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ Мужчин: {num}\n\nВыберите напитки:",
                            reply_markup=get_drinks_buttons()
                        )
                except ValueError:
                    application.bot.send_message(
                        chat_id=user_id,
                        text="❌ Введите число!"
                    )
        
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            data_val = update.callback_query.data
            logger.info(f"🔘 Callback from {user_id}: {data_val}")
            
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            
            if data_val.startswith('evt_'):
                user_sessions[user_id]['event_type'] = data_val.replace('evt_', '')
                application.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=update.callback_query.message.message_id,
                    text="✅ Выбрано!\n\nВыберите формат:",
                    reply_markup=get_format_buttons(),
                    parse_mode='HTML'
                )
            
            elif data_val.startswith('fmt_'):
                user_sessions[user_id]['event_format'] = data_val.replace('fmt_', '')
                application.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=update.callback_query.message.message_id,
                    text="✅ Выбрано!\n\nДлительность:",
                    reply_markup=get_duration_buttons(),
                    parse_mode='HTML'
                )
            
            elif data_val.startswith('dur_'):
                user_sessions[user_id]['duration'] = data_val.replace('dur_', '')
                application.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=update.callback_query.message.message_id,
                    text="✅ Выбрано!\n\n👥 Введите кол-во гостей:",
                    parse_mode='HTML'
                )
            
            elif data_val.startswith('drk_'):
                drink = data_val.replace('drk_', '')
                
                if drink == 'done':
                    if 'drinks' not in user_sessions[user_id] or not user_sessions[user_id]['drinks']:
                        application.bot.answer_callback_query(
                            callback_query_id=update.callback_query.id,
                            text="❌ Выберите напиток!",
                            show_alert=True
                        )
                    else:
                        application.bot.edit_message_text(
                            chat_id=user_id,
                            message_id=update.callback_query.message.message_id,
                            text="💰 Выберите категорию:",
                            reply_markup=get_price_buttons(),
                            parse_mode='HTML'
                        )
                else:
                    if 'drinks' not in user_sessions[user_id]:
                        user_sessions[user_id]['drinks'] = []
                    if drink not in user_sessions[user_id]['drinks']:
                        user_sessions[user_id]['drinks'].append(drink)
                    
                    drinks_str = ", ".join(user_sessions[user_id]['drinks'])
                    application.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=update.callback_query.message.message_id,
                        text=f"✅ Выбрано: {drinks_str}\n\nЕще или готово:",
                        reply_markup=get_drinks_buttons(),
                        parse_mode='HTML'
                    )
            
            elif data_val.startswith('prc_'):
                user_sessions[user_id]['price'] = data_val.replace('prc_', '')
                
                try:
                    result = calculate_alcohol(user_sessions[user_id])
                    message_text = format_result(result)
                    
                    application.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=update.callback_query.message.message_id,
                        text=message_text,
                        parse_mode='HTML'
                    )
                    
                    application.bot.send_message(
                        chat_id=user_id,
                        text="🔄 /start для нового расчета"
                    )
                    logger.info(f"✅ Result sent to {user_id}")
                except Exception as e:
                    logger.error(f"Calc error: {e}")
                    application.bot.send_message(
                        chat_id=user_id,
                        text="❌ Ошибка. /start"
                    )
        
        return 'ok', 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return 'error', 500

async def set_webhook():
    try:
        webhook_url = f"{TELEGRAM_WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")

if __name__ == '__main__':
    import asyncio
    
    try:
        asyncio.run(set_webhook())
    except Exception as e:
        logger.error(f"Error: {e}")
    
    logger.info("🚀 Bot started!")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
