import logging
import os
import json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
FLASK_PORT = int(os.getenv('PORT', 5000))

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")

app = Flask(__name__)
application = None

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

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    try:
        data = request.get_json()
        update = Update.de_json(data, application.bot)
        
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
            logger.info(f"Message from {user_id}: {update.message.text}")
            
            if update.message.text == '/start':
                user_sessions[user_id] = {}
                application.bot.send_message(
                    chat_id=user_id,
                    text="🍾 <b>Добро пожаловать в Алкоголь.Калькулятор!</b>\n\nВыберите тип события:",
                    parse_mode='HTML',
                    reply_markup=get_event_buttons()
                )
                logger.info(f"Sent start message to {user_id}")
        
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            logger.info(f"Callback from {user_id}: {update.callback_query.data}")
        
        return 'ok', 200
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return 'error', 500

async def set_webhook():
    try:
        webhook_url = f"{TELEGRAM_WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

if __name__ == '__main__':
    global application
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    import asyncio
    try:
        asyncio.run(set_webhook())
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    logger.info("🚀 Bot started!")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
