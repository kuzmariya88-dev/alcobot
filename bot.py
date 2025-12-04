import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
from calculator import calculate_alcohol, format_result

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")

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
        [InlineKeyboardButton("🍷 Белое сухое", callback_data="drk_dry_white")],
        [InlineKeyboardButton("🍷 Белое полусладкое", callback_data="drk_semi_sweet_white")],
        [InlineKeyboardButton("🍷 Белое полусухое", callback_data="drk_semi_dry_white")],
        [InlineKeyboardButton("🍷 Красное сухое", callback_data="drk_dry_red")],
        [InlineKeyboardButton("🍷 Красное полусладкое", callback_data="drk_semi_sweet_red")],
        [InlineKeyboardButton("🍷 Красное полусухое", callback_data="drk_semi_dry_red")],
        [InlineKeyboardButton("🥂 Шампанское", callback_data="drk_champagne")],
        [InlineKeyboardButton("🥃 Водка", callback_data="drk_vodka")],
        [InlineKeyboardButton("🥃 Виски", callback_data="drk_whiskey")],
        [InlineKeyboardButton("🥃 Джин", callback_data="drk_gin")],
        [InlineKeyboardButton("🌵 Текила", callback_data="drk_tequila")],
        [InlineKeyboardButton("🥃 Коньяк", callback_data="drk_cognac")],
        [InlineKeyboardButton("✅ Готово", callback_data="drk_done")]
    ])

async def start(update: Update, context):
    user_id = update.message.from_user.id
    user_sessions[user_id] = {'step': 'event_type'}
    await update.message.reply_text(
        "🍾 <b>Добро пожаловать в Алкоголь.Калькулятор!</b>\n\nВыберите тип события:",
        parse_mode='HTML',
        reply_markup=get_event_buttons()
    )
    logger.info(f"✅ Start sent to {user_id}")

async def handle_message(update: Update, context):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if user_id not in user_sessions or 'event_type' not in user_sessions[user_id]:
        return
    
    try:
        num = int(text)
        if 'guests_total' not in user_sessions[user_id]:
            user_sessions[user_id]['guests_total'] = num
            await update.message.reply_text(f"✅ Гостей: {num}\n\nВведите количество мужчин:")
        else:
            user_sessions[user_id]['guests_male'] = num
            user_sessions[user_id]['drinks'] = []
            await update.message.reply_text(
                f"✅ Мужчин: {num}\n\nВыберите напитки (можно выбрать несколько):",
                reply_markup=get_drinks_buttons()
            )
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите число!")

async def handle_callback(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data_value = query.data
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    
    await query.answer()
    
    if data_value.startswith('evt_'):
        event_type = data_value.replace('evt_', '')
        user_sessions[user_id]['event_type'] = event_type
        await query.edit_message_text(
            text=f"✅ Выбрано: {event_type}\n\nВыберите формат события:",
            reply_markup=get_format_buttons(),
            parse_mode='HTML'
        )
    elif data_value.startswith('fmt_'):
        event_format = data_value.replace('fmt_', '')
        user_sessions[user_id]['event_format'] = event_format
        await query.edit_message_text(
            text=f"✅ Выбрано: {event_format}\n\nВыберите длительность:",
            reply_markup=get_duration_buttons(),
            parse_mode='HTML'
        )
    elif data_value.startswith('dur_'):
        duration = data_value.replace('dur_', '')
        user_sessions[user_id]['duration'] = duration
        await query.edit_message_text(
            text=f"✅ Длительность: {duration}\n\n👥 Введите общее количество гостей:",
            parse_mode='HTML'
        )
    elif data_value.startswith('drk_'):
        drink = data_value.replace('drk_', '')
        
        if drink == 'done':
            if 'drinks' not in user_sessions[user_id] or not user_sessions[user_id]['drinks']:
                await query.answer("❌ Выберите хотя бы один напиток!", show_alert=True)
                return
            
            try:
                result = calculate_alcohol(user_sessions[user_id])
                message_text = format_result(result)
                await query.edit_message_text(text=message_text, parse_mode='HTML')
                await query.message.reply_text("🔄 Нажмите /start для нового расчета")
                logger.info(f"✅ Result sent to {user_id}")
            except Exception as e:
                logger.error(f"Error: {e}")
                await query.message.reply_text("❌ Ошибка при расчете. Попробуйте еще раз: /start")
        else:
            if 'drinks' not in user_sessions[user_id]:
                user_sessions[user_id]['drinks'] = []
            if drink not in user_sessions[user_id]['drinks']:
                user_sessions[user_id]['drinks'].append(drink)
            
            drink_names = {
                'dry_white': '🍷 Белое сухое',
                'semi_sweet_white': '🍷 Белое полусладкое',
                'semi_dry_white': '🍷 Белое полусухое',
                'dry_red': '🍷 Красное сухое',
                'semi_sweet_red': '🍷 Красное полусладкое',
                'semi_dry_red': '🍷 Красное полусухое',
                'champagne': '🥂 Шампанское',
                'vodka': '🥃 Водка',
                'whiskey': '🥃 Виски',
                'gin': '🥃 Джин',
                'tequila': '🌵 Текила',
                'cognac': '🥃 Коньяк',
            }
            
            drinks_list = ", ".join([drink_names.get(d, d) for d in user_sessions[user_id]['drinks']])
            await query.edit_message_text(
                text=f"✅ Выбранные напитки:\n{drinks_list}\n\nДобавьте еще или нажмите 'Готово':",
                reply_markup=get_drinks_buttons(),
                parse_mode='HTML'
            )

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("🚀 Bot started with polling!")
    app.run_polling()
