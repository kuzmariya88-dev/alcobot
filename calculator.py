def calculate_alcohol(session_data):
    """
    Расчет количества алкоголя по типам напитков
    """
    guests_total = session_data.get('guests_total', 0)
    guests_male = session_data.get('guests_male', 0)
    guests_female = guests_total - guests_male
    duration = session_data.get('duration', '3-4')
    drinks = session_data.get('drinks', [])
    
    # Стандартное потребление (мл на человека за час)
    consumption_per_hour = {
        'male': 60,
        'female': 40
    }
    
    # Длительность события в часах (берем среднее)
    duration_map = {
        '2-3': 2.5,
        '3-4': 3.5,
        '4-5': 4.5,
        '5+': 6
    }
    hours = duration_map.get(duration, 3.5)
    
    # Крепость напитков (% алкоголя) и объём бутылки (мл)
    drink_specs = {
        'dry_white': {'name': 'Белое сухое', 'abv': 12, 'bottle_ml': 750},
        'semi_sweet_white': {'name': 'Белое полусладкое', 'abv': 12, 'bottle_ml': 750},
        'semi_dry_white': {'name': 'Белое полусухое', 'abv': 12, 'bottle_ml': 750},
        'dry_red': {'name': 'Красное сухое', 'abv': 13, 'bottle_ml': 750},
        'semi_sweet_red': {'name': 'Красное полусладкое', 'abv': 13, 'bottle_ml': 750},
        'semi_dry_red': {'name': 'Красное полусухое', 'abv': 12, 'bottle_ml': 750},
        'champagne': {'name': 'Шампанское', 'abv': 12, 'bottle_ml': 750},
        'vodka': {'name': 'Водка', 'abv': 40, 'bottle_ml': 750},
        'whiskey': {'name': 'Виски', 'abv': 40, 'bottle_ml': 750},
        'gin': {'name': 'Джин', 'abv': 40, 'bottle_ml': 750},
        'tequila': {'name': 'Текила', 'abv': 38, 'bottle_ml': 750},
        'cognac': {'name': 'Коньяк', 'abv': 40, 'bottle_ml': 750},
    }
    
    # Расчет общего потребления алкоголя (в мл чистого спирта)
    male_consumption_ml = guests_male * consumption_per_hour['male'] * hours
    female_consumption_ml = guests_female * consumption_per_hour['female'] * hours
    total_alcohol_ml = male_consumption_ml + female_consumption_ml
    
    # Распределение по типам напитков поровну
    num_drink_types = len(drinks)
    if num_drink_types == 0:
        return {'error': 'Не выбраны напитки'}
    
    alcohol_per_drink = total_alcohol_ml / num_drink_types
    
    result = {
        'guests_total': guests_total,
        'guests_male': guests_male,
        'guests_female': guests_female,
        'duration': duration,
        'total_alcohol_ml': total_alcohol_ml,
        'drinks_breakdown': []
    }
    
    total_bottles = 0
    
    for drink_code in drinks:
        if drink_code not in drink_specs:
            continue
        
        spec = drink_specs[drink_code]
        # Сколько мл чистого спирта нужно этого напитка
        alcohol_needed = alcohol_per_drink
        # Сколько мл напитка нужно (учитываем крепость)
        volume_needed_ml = (alcohol_needed / spec['abv']) * 100
        # Сколько бутылок
        bottles_needed = volume_needed_ml / spec['bottle_ml']
        
        result['drinks_breakdown'].append({
            'name': spec['name'],
            'bottles': round(bottles_needed, 1),
            'bottles_int': int(bottles_needed) + (1 if bottles_needed % 1 > 0 else 0)
        })
        
        total_bottles += bottles_needed
    
    result['total_bottles'] = total_bottles
    result['total_bottles_int'] = int(total_bottles) + (1 if total_bottles % 1 > 0 else 0)
    
    return result

def format_result(result):
    """
    Форматирование результата для Telegram
    """
    if 'error' in result:
        return f"❌ {result['error']}"
    
    message = "🍾 <b>РЕЗУЛЬТАТ РАСЧЕТА</b> 🍾\n\n"
    
    message += "📊 <b>Параметры события:</b>\n"
    message += f"• Всего гостей: {result['guests_total']}\n"
    message += f"  └ Мужчин: {result['guests_male']}, Женщин: {result['guests_female']}\n"
    message += f"• Длительность: {result['duration']}\n\n"
    
    message += "📦 <b>Необходимо алкоголя:</b>\n"
    for drink in result['drinks_breakdown']:
        message += f"• <b>{drink['name']}</b>: {drink['bottles_int']} бутылок ({drink['bottles']:.1f})\n"
    
    message += f"\n<b>ИТОГО: {result['total_bottles_int']} бутылок</b> ({result['total_bottles']:.1f})\n\n"
    message += "✅ Расчет готов!"
    
    return message
