import math
from config import VOLUME_PER_PERSON, EVENT_COEFFICIENTS, PRICE_CATEGORIES, DRINKS_DISTRIBUTION, BOTTLE_VOLUME

def calculate_alcohol(event_data):
    event_type = event_data.get('event_type')
    event_format = event_data.get('event_format')
    duration = event_data.get('duration')
    total_guests = int(event_data.get('guests_total', 0))
    male_guests = int(event_data.get('guests_male', 0))
    female_guests = total_guests - male_guests
    selected_drinks = event_data.get('drinks', [])
    price_category = event_data.get('price_category', 'стандарт')
    
    volume_per_person = VOLUME_PER_PERSON.get(event_format, {}).get(duration, 0.4)
    event_coefficient = EVENT_COEFFICIENTS.get(event_type, 1.0)
    total_volume = total_guests * volume_per_person * event_coefficient * 1.15
    
    has_champagne = 'champagne' in selected_drinks
    distribution = DRINKS_DISTRIBUTION['with_champagne'] if has_champagne else DRINKS_DISTRIBUTION['without_champagne']
    
    volumes = {}
    bottles = {}
    
    if 'champagne' in selected_drinks:
        volumes['champagne'] = total_volume * distribution['champagne']
        bottles['champagne'] = math.ceil(volumes['champagne'] / BOTTLE_VOLUME['champagne'])
    else:
        bottles['champagne'] = 0
    
    if 'wine_white' in selected_drinks:
        volumes['wine_white'] = total_volume * distribution['wine_white']
        bottles['wine_white'] = math.ceil(volumes['wine_white'] / BOTTLE_VOLUME['wine_white'])
    else:
        bottles['wine_white'] = 0
    
    if 'wine_red' in selected_drinks:
        volumes['wine_red'] = total_volume * distribution['wine_red']
        bottles['wine_red'] = math.ceil(volumes['wine_red'] / BOTTLE_VOLUME['wine_red'])
    else:
        bottles['wine_red'] = 0
    
    if 'whiskey' in selected_drinks or 'cognac' in selected_drinks:
        volumes['strong'] = total_volume * distribution['strong']
        bottles['whiskey'] = math.ceil((volumes['strong'] * 0.6) / BOTTLE_VOLUME['strong']) if 'whiskey' in selected_drinks else 0
        bottles['cognac'] = math.ceil((volumes['strong'] * 0.4) / BOTTLE_VOLUME['strong']) if 'cognac' in selected_drinks else 0
    else:
        bottles['whiskey'] = 0
        bottles['cognac'] = 0
    
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

def format_result(result):
    bottles = result['bottles']
    budget = result['estimated_budget']
    event_info = result['event_info']
    
    text = (
        f"📊 <b>РЕЗУЛЬТАТЫ РАСЧЕТА</b>\n"
        f"{'─' * 40}\n"
        f"📌 <b>Событие:</b> {event_info['type']}\n"
        f"🎭 <b>Формат:</b> {event_info['format']} {event_info['duration']}ч\n"
        f"👥 <b>Гостей:</b> {event_info['guests_total']} "
        f"({event_info['guests_male']}М, {event_info['guests_female']}Ж)\n"
        f"{'─' * 40}\n\n"
        f"🍾 <b>РЕКОМЕНДУЕМОЕ КОЛ-ВО БУТЫЛОК:</b>\n"
    )
    
    if bottles['champagne'] > 0:
        text += f"🥂 Шампанское: <b>{bottles['champagne']} бут.</b>\n"
    if bottles['wine_white'] > 0:
        text += f"🍷 Вино белое: <b>{bottles['wine_white']} бут.</b>\n"
    if bottles['wine_red'] > 0:
        text += f"🍷 Вино красное: <b>{bottles['wine_red']} бут.</b>\n"
    if bottles['whiskey'] > 0:
        text += f"🥃 Виски: <b>{bottles['whiskey']} бут.</b>\n"
    if bottles['cognac'] > 0:
        text += f"🥃 Коньяк: <b>{bottles['cognac']} бут.</b>\n"
    
    text += (
        f"\n{'─' * 40}\n"
        f"💰 <b>Ориентировочный бюджет:</b> {budget:,} ₽\n"
        f"{'─' * 40}\n"
    )
    
    return text
