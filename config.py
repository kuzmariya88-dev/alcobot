import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
WEBHOOK_PATH = f'{TELEGRAM_WEBHOOK_URL}/webhook'
FLASK_PORT = int(os.getenv('PORT', 5000))
FLASK_HOST = '0.0.0.0'

VOLUME_PER_PERSON = {
    'банкет': {'2-3': 0.3, '3-4': 0.4, '4-5': 0.5, '5+': 0.6},
    'фуршет': {'1-2': 0.15, '2-3': 0.25, '3-4': 0.35, '4+': 0.45}
}

EVENT_COEFFICIENTS = {
    'день_рождения': 0.9,
    'свадьба': 1.0,
    'корпоратив': 0.8,
    'вечеринка': 1.2,
    'юбилей': 1.0,
    'семейное': 0.7,
    'другое': 1.0
}

PRICE_CATEGORIES = {
    'стандарт': 500,
    'премиум': 1100,
    'люкс': 2250,
    'супер_люкс': 4000
}

DRINKS_DISTRIBUTION = {
    'with_champagne': {
        'champagne': 0.50,
        'wine_white': 0.25,
        'wine_red': 0.20,
        'strong': 0.05
    },
    'without_champagne': {
        'wine_white': 0.45,
        'wine_red': 0.40,
        'strong': 0.15
    }
}

BOTTLE_VOLUME = {
    'champagne': 0.75,
    'wine_white': 0.75,
    'wine_red': 0.75,
    'strong': 0.7
}
