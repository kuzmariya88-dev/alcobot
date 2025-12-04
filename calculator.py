import math
from config import VOLUME_PER_PERSON, EVENT_COEFFICIENTS, PRICE_CATEGORIES, DRINKS_DISTRIBUTION, BOTTLE_VOLUME

def calculate_alcohol(event_data):
    try:
        # Получи данные с нормализацией
        event_type = str(event_data.get('event_type', '')).strip().lower()
        event_format = str(event_data.get('event_format', '')).strip().lower()
        duration = str(event_data.get('duration', '')).strip()
        total_guests = int(event_data.get('guests_total', 0))
        male_guests = int(event_data.get('guests_male', 0))
        female_guests = total_guests - male_guests
        selected_drinks = event_data.get('drinks', [])
        price_category = str(event_data.get('price_category', 'стандарт')).strip().lower()
        
        # Дефолт значения если данные плохие
        if not event_format or event_format not in VOLUME_PER_PERSON:
            event_format = 'банкет'
        if not duration or duration not in VOLUME_PER_PERSON.get(event_format, {}):
            duration = '2-3'
        
        # Рассчитай объем
        volume_per_person = VOLUME_PER_PERSON.get(event_format, {}).get(duration, 0.4)
        event_coefficient = EVENT_COEFFICIENTS.get(event_type, 1.0)
        total_volume = total_guests * volume_per_person * event_coefficient * 1.15
        
        # Определи есть ли шампанское
        has_champagne = 'champagne' in selected_drinks
        distribution = DRINKS_DISTRIBUTION['with_champagne'] if has_champagne else DRINKS_DISTRIBUTION['without_champagne']
        
        volumes = {}
        bottles = {}
        
        # Шампанское
        if 'champagne' in selected_drinks:
            volumes['champagne'] = total_volume * distribution.get('champagne', 0)
            bottles['champagne'] = math.ceil(volumes['champagne'] / BOTTLE_VOLUME.get('champagne', 0.75))
        else:
            bottles['champagne'] = 0
        
        # Вино белое
        if 'wine_white' in selected_drinks:
            volumes['wine_white'] = total_volume * distribution.get('wine_white', 0)
            bottles['wine_white'] = math.ceil(volumes['wine_white'] / BOTTLE_VOLUME.get('wine_white', 0.75))
        else:
            bottles['wine_white'] = 0
        
        # Вино красное
        if 'wine_red' in selected_drinks:
            volumes['wine_red'] = total_volume * distribution.get('wine_red', 0)
            bottles['wine_red'] = math.ceil(volumes['wine_red'] / BOTTLE_VOLUME.get('wine_red', 0.75))
        else:
            bottles['wine_red'] = 0
        
        # Крепкие
        strong_volume = total_volume * distribution.get('strong', 0)
        
        if 'whiskey' in selected_drinks:
            whiskey_volume = strong_volume * 0.6
            bottles['whiskey'] = math.ceil(whiskey_volume / BOTTLE_VOLUME.get('strong', 0.7))
        else:
            bottles['whiskey'] = 0
        
        if 'cognac' in selected_drinks:
            cognac_volume = strong_volume * 0.4
            bottles['cognac'] = math.ceil(cognac_volume / BOTTLE_VOLUME.get('strong', 0.7))
        else:
            bottles['cognac'] = 0
        
        # Итоговый расчет
        total_bottles = sum(bottles.values())
        price_per_bottle = PRICE_CATEGORIES.get(price_category, 500)
        estimated_budget = total_bottles * price_per_bottle
        
        return {
            'total_volume': round(total_volume, 2),
            'bottles': bottles,
            'total_bottles': total_bottles,
            'estimated_budget': int(estimated_budget),
            'event_info': {
                'type': event_type,
                'format': event_format,
                'duration': duration,
                'guests_total': total_guests,
                'guests_male': male_guests,
                'guests_female': female_guests
            }
        }
    except Exception as e:
        return {
            'error': str(e),
            'total_volume': 0,
            'bottles': {},
            'total_bottles': 0,
            'estimated_budget': 0,
            'event_info': {}
        }

def format_result(result):
    if 'error' in result and result['error']:
        return f"❌ <b>Ошибка расчета:</b> {result['error']}"
    
    bottles = result.get('bottles', {})
    budget = result.get('estimated_budget', 0)
    event_info = result.get('event_info', {})
    
    text = (
        f"📊 <b>РЕЗУЛЬТАТЫ РАСЧЕТА</b>\n"
        f"{'─' * 40}\n"
        f"📌 <b>Событие:</b> {event_info.get('type', 'N/A')}\n"
        f"🎭 <b>Формат:</b> {event_info.get('format', 'N/A')} {event_info.get('duration', 'N/A')}ч\n"
        f"👥 <b>Гостей:</b> {event_info.get('guests_total', 0)} "
        f"({event_info.get('guests_male', 0)}М, {event_info.get('guests_female', 0)}Ж)\n"
        f"{'─' * 40}\n\n"
        f"🍾 <b>РЕКОМЕНДУЕМОЕ КОЛ-ВО БУТЫЛОК:</b>\n"
    )
    
    if bottles.get('champagne', 0) > 0:
        text += f"🥂 Шампанское: <b>{bottles['champagne']} бут.</b>\n"
    if bottles.get('wine_white', 0) > 0:
        text += f"🍷 Вино белое: <b>{bottles['wine_white']} бут.</b>\n"
    if bottles.get('wine_red', 0) > 0:
        text += f"🍷 Вино красное: <b>{bottles['wine_red']} бут.</b>\n"
    if bottles.get('whiskey', 0) > 0:
        text += f"🥃 Виски: <b>{bottles['whiskey']} бут.</b>\n"
    if bottles.get('cognac', 0) > 0:
        text += f"🥃 Коньяк: <b>{bottles['cognac']} бут.</b>\n"
    
    text += (
        f"\n{'─' * 40}\n"
        f"💰 <b>Ориентировочный бюджет:</b> {budget:,} ₽\n"
        f"{'─' * 40}\n"
    )
    
    return text
