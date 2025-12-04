def calculate_alcohol(session):
    """Расчет алкоголя для события"""
    
    guests_total = session.get('guests_total', 0)
    guests_male = session.get('guests_male', 0)
    guests_female = guests_total - guests_male
    
    duration = session.get('duration', '2-3')
    drinks = session.get('drinks', [])
    price_category = session.get('price_category', 'стандарт')
    
    # Норма напитков в мл на человека в час
    drink_norms = {
        'drk_champagne': 100,
        'drk_wine_white': 100,
        'drk_wine_red': 100,
        'drk_whiskey': 40,
        'drk_cognac': 40
    }
    
    # Средняя длительность
    duration_map = {
        '2-3': 2.5,
        '3-4': 3.5,
        '4-5': 4.5,
        '5+': 5.5
    }
    
    hours = duration_map.get(duration, 3)
    
    # Расчет общего количества
    total_ml = 0
    for drink in drinks:
        norm = drink_norms.get(drink, 80)
        # Мужчины пьют больше женщин
        male_consumption = guests_male * norm * hours * 1.2
        female_consumption = guests_female * norm * hours * 0.8
        total_ml += male_consumption + female_consumption
    
    # Стоимость
    price_per_liter = {
        'стандарт': 500,
        'премиум': 1100,
        'люкс': 2250,
        'супер_люкс': 4000
    }
    
    price = price_per_liter.get(price_category, 500)
    total_cost = (total_ml / 1000) * price
    
    # Количество бутылок (стандартная 750мл)
    bottles = total_ml / 750
    
    return {
        'total_ml': int(total_ml),
        'liters': round(total_ml / 1000, 2),
        'bottles': round(bottles, 1),
        'total_cost': int(total_cost),
        'price_per_bottle': price,
        'drinks': drinks,
        'guests_total': guests_total,
        'duration': duration
    }

def format_result(result):
    """Форматирование результата для Telegram"""
    
    drinks_names = {
        'drk_champagne': '🥂 Шампанское',
        'drk_wine_white': '🍷 Вино белое',
        'drk_wine_red': '🍷 Вино красное',
        'drk_whiskey': '🥃 Виски',
        'drk_cognac': '🥃 Коньяк'
    }
    
    drinks_str = "\n".join([drinks_names.get(d, d) for d in result['drinks']])
    
    message = f"""
🍾 <b>РЕЗУЛЬТАТ РАСЧЕТА</b> 🍾

📊 <b>Параметры события:</b>
• Гостей: {result['guests_total']}
• Напитки: {drinks_str}
• Длительность: {result['duration']}

📦 <b>Необходимо алкоголя:</b>
• Всего: <b>{result['liters']} литров</b>
• Бутылок: <b>{result['bottles']} шт</b>
• Мл на человека: <b>{result['total_ml'] // max(result['guests_total'], 1)} мл</b>

💰 <b>Стоимость:</b>
• Цена за литр: <b>{result['price_per_bottle']}₽</b>
• Итого: <b>{result['total_cost']:,}₽</b>

✅ Расчет готов!
"""
    return message
