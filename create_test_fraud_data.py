#!/usr/bin/env python3
"""
Генератор тестовых данных для системы обнаружения мошенничества.
Создает Excel файл с характеристиками разных типов фрода.
"""

import pandas as pd
from datetime import datetime, timedelta
import random
import string

OUTPUT_FILE = "test_fraud_scenarios.xlsx"
PERIOD_FROM = datetime(2026, 1, 21, 0, 0)

# Справочники
PAYMENT_TYPES = ["Наличный", "Безналичный"]
TARIFFS = ["полный", "детский", "студент", "пенсионер", "инвалид"]
SERVICE_CLASSES = ["2С", "2Д", "3П", "3Л", "1Л", "1П"]
CARRIERS = ["АО ПАССАЖИРСКИЕ ПЕР-КИ", "ТОО АРЛАН-ТРАНС-АСТАНА"]
TERMINALS = ["010ЦА", "086ТА", "086РА", "329ЖА", "021ЦА", "140*ЦА", "075*ЦА"]
CHANNELS = ["Собственные кассы", "Туристические агентства", "Мобильное приложение", "Веб-сайт"]
STATIONS = ["АЛМАТЫ", "АСТАНА", "КАРАГАНДА", "АКТОБЕ", "ШЫМКЕНТ", "АТЫРАУ", "КОСТАНАЙ"]
GENDERS = ["М", "Ж"]
AGGREGATORS = ["АО ПП", "Booking.com", "Agoda", "Onlinetravel", "Expedia"]

def generate_iin():
    return "".join(random.choices(string.digits, k=12))

def generate_fio():
    surnames = ["ПЕТРОВ", "ИВАНОВ", "СИДОРОВ", "КОЗЛОВ", "НОВИКОВ"]
    names = ["ИВАН", "ПЕТР", "СЕРГЕЙ", "МАРИЯ", "АННА"]
    return f"{random.choice(surnames)} {random.choice(names)}"

def create_transaction(order_num, op_type="Оформление", order_date=None,
                       fio=None, refund_ratio=0.0, is_night=False,
                       is_bot=False, has_fraud_fio=False, iin=None):
    """Создает транзакцию со всеми требуемыми полями"""

    if order_date is None:
        order_date = PERIOD_FROM + timedelta(hours=random.randint(0, 48))

    if is_night:
        order_date = order_date.replace(hour=random.randint(0, 5))

    dep_station = random.choice(STATIONS)
    arr_station = random.choice(STATIONS)
    while arr_station == dep_station:
        arr_station = random.choice(STATIONS)

    dep_time = order_date + timedelta(days=random.randint(1, 30))
    price = random.randint(3000, 35000)

    if op_type == "Возврат" or random.random() < refund_ratio:
        op_type = "Возврат"
        price = 0

    if fio is None:
        if has_fraud_fio:
            fio = random.choice(["AAAAA BBBBB", "TESTUSER TEST", "X X", "NONAME NOFAMILY"])
        else:
            fio = generate_fio()

    if iin is None:
        iin = generate_iin()

    return {
        'Номер заказа': f"ZAK{order_num:08d}",
        'Операция': op_type,
        'Номер билета': f"{random.choice(string.ascii_uppercase)}{random.randint(100000000, 999999999)}",
        '': None,  # пусто
        'Тариф и льгота': random.choice(TARIFFS),
        'Цена': price,
        '  ': None,  # пусто
        'Разные сборы': 0,
        'Тип расчета': random.choice(PAYMENT_TYPES),
        'Дата операции': order_date.strftime("%d.%m.%Y %H:%M:%S"),
        '   ': None,  # пусто
        'Перевозчик': random.choice(CARRIERS),
        'Номер поезда': random.choice(TERMINALS),
        'Класс обслуживания': random.choice(SERVICE_CLASSES),
        'Станция отправления': dep_station,
        'Дата/время отправки': dep_time.strftime("%d.%m.%Y %H:%M:%S"),
        '    ': None,  # пусто
        'Станция назначения': arr_station,
        'Канал продаж': random.choice(CHANNELS),
        'Данные пассажира': fio,
        'Пол': random.choice(GENDERS),
        'Агрегатор': random.choice(AGGREGATORS),
        'Терминал': random.choice(TERMINALS),
        '     ': None,  # пусто
        'Канальный адрес': f"CH{random.randint(1000, 9999)}",
        'Пункт продажи': f"POS{random.randint(100, 999)}",
        'Номер УБ': f"UB{random.randint(1000000, 9999999)}",
        'Номер телефона, ИИН': iin,
    }

def create_scenario(scenario_name, num_passengers=1):
    """Создает сценарий фрода со специфическими признаками"""
    transactions = []
    order_counter = 1000

    if scenario_name == "clean_users":
        # Чистые пользователи: 1-3 покупки, редкие возвраты (0-5%)
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for _ in range(random.randint(1, 3)):
                op_date = PERIOD_FROM + timedelta(days=random.randint(0, 1), hours=random.randint(8, 20))
                tx = create_transaction(order_counter, "Оформление", op_date, fio, refund_ratio=0.02, iin=iin)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "scalpers":
        # Скальперы: 50-150 билетов в день, 5-10% возвратов
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            num_tickets = random.randint(50, 150)
            for i in range(num_tickets):
                op_date = PERIOD_FROM + timedelta(minutes=random.randint(0, 1440))
                tx = create_transaction(order_counter, "Оформление", op_date, fio, refund_ratio=0.08, iin=iin)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "refund_abusers":
        # Абузеры возвратов: 70-90% возвратов
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for i in range(30):
                op_date = PERIOD_FROM + timedelta(hours=i*2)
                # 30% - возвраты, 70% - покупки
                op_type = "Возврат" if random.random() < 0.7 else "Оформление"
                tx = create_transaction(order_counter, op_type, op_date, fio, refund_ratio=0.0, iin=iin)
                if op_type == "Возврат":
                    tx['Цена'] = 0
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "quick_refunders":
        # Быстрые возвраты: 30-60 минут после покупки
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for i in range(20):
                op_date = PERIOD_FROM + timedelta(hours=i)
                dep_time = op_date + timedelta(days=random.randint(1, 30))
                # Покупка
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                tx['Дата/время отправки'] = dep_time.strftime("%d.%m.%Y %H:%M:%S")
                transactions.append(tx)
                order_counter += 1
                # Возврат через 30-60 минут
                refund_date = op_date + timedelta(minutes=random.randint(30, 60))
                tx_refund = create_transaction(order_counter, "Возврат", refund_date, fio, iin=iin)
                tx_refund['Дата/время отправки'] = dep_time.strftime("%d.%m.%Y %H:%M:%S")
                tx_refund['Цена'] = 0
                transactions.append(tx_refund)
                order_counter += 1

    elif scenario_name == "late_refunders":
        # Поздние возвраты: за 6-24 часа до вылета
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for i in range(20):
                op_date = PERIOD_FROM + timedelta(hours=i)
                dep_date = op_date + timedelta(days=1, hours=random.randint(0, 12))
                # Покупка
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                tx['Дата/время отправки'] = dep_date.strftime("%d.%m.%Y %H:%M:%S")
                transactions.append(tx)
                order_counter += 1
                # Возврат за 6-24 часа до вылета
                refund_date = dep_date - timedelta(hours=random.randint(6, 24))
                tx_refund = create_transaction(order_counter, "Возврат", refund_date, fio, iin=iin)
                tx_refund['Дата/время отправки'] = dep_date.strftime("%d.%m.%Y %H:%M:%S")
                tx_refund['Цена'] = 0
                transactions.append(tx_refund)
                order_counter += 1

    elif scenario_name == "night_bots":
        # Ночные боты: ТОЛЬКО операции с 00:00 до 06:00
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for i in range(100):
                op_date = PERIOD_FROM + timedelta(days=i // 10)
                tx = create_transaction(order_counter, "Оформление", op_date, fio, is_night=True, iin=iin)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "fake_identity":
        # Поддельные личности: странные/некорректные ФИО
        fake_fios = ["AAAAA BBBBB", "123456 XXXXXX", "TESTUSER TEST", "X X", "NONAME NOFAMILY"]
        for fake_fio in fake_fios:
            iin = generate_iin()
            for i in range(30):
                op_date = PERIOD_FROM + timedelta(hours=i)
                tx = create_transaction(order_counter, "Оформление", op_date, fio=fake_fio, iin=iin)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "organized_ring":
        # Организованное кольцо: похожие ФИО, одинаковые маршруты
        base_fios = ["КОЛЬЦО ГРУППА", "КОЛЬЦО ГРУПП", "КОЛЬЦВ ГРУПП", "КОЛЬЦГ ГРУПП", "КОЛЬЦД ГРУПП"]
        for fio in base_fios:
            iin = generate_iin()
            for i in range(20):
                op_date = PERIOD_FROM + timedelta(hours=i)
                tx = create_transaction(order_counter, "Оформление", op_date, fio=fio, iin=iin)
                # Все с одного маршрута
                tx['Станция отправления'] = "АЛМАТЫ"
                tx['Станция назначения'] = "АСТАНА"
                tx['Цена'] = 9999  # Одинаковая сумма - подозрительно
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "concentrated_activity":
        # Сконцентрированная активность: много операций за короткое время
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for i in range(100):
                hour = i % 24
                op_date = PERIOD_FROM.replace(hour=hour, minute=i*10 % 60)
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "mixed_channels":
        # Операции через разные каналы с разными характеристиками
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            for i in range(50):
                op_date = PERIOD_FROM + timedelta(hours=random.randint(0, 48))
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                # Специфический канал
                tx['Канал продаж'] = random.choice(CHANNELS)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "seat_blocking":
        # Seat blocking: много билетов на один поезд в один день отправления
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            # Выбираем фиксированный поезд и дату отправления
            target_train = random.choice(TERMINALS)
            target_dep_date = PERIOD_FROM + timedelta(days=random.randint(5, 30))

            for i in range(40):  # Много билетов
                op_date = PERIOD_FROM + timedelta(hours=random.randint(0, 72))
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                tx['Номер поезда'] = target_train
                tx['Дата/время отправки'] = target_dep_date.strftime("%d.%m.%Y %H:%M:%S")
                tx['Цена'] = random.randint(8000, 15000)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "terminal_hopping":
        # Terminal hopping: прыгание между разными терминалами/кассами
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            terminals_list = list(TERMINALS)
            random.shuffle(terminals_list)

            for i in range(50):
                op_date = PERIOD_FROM + timedelta(hours=i)
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                # Каждая операция с разного терминала
                tx['Терминал'] = terminals_list[i % len(terminals_list)]
                tx['Пункт продажи'] = f"POS{i % 20}"
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "channel_anomaly":
        # Channel anomaly: большинство операций через один аномальный канал
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            # Все через туристические агентства + редко через другие
            for i in range(60):
                op_date = PERIOD_FROM + timedelta(hours=random.randint(0, 48))
                if i < 50:  # 83% через один канал
                    channel = "Туристические агентства"
                else:
                    channel = random.choice(CHANNELS)
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                tx['Канал продаж'] = channel
                tx['Цена'] = random.randint(2000, 5000)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "amount_pattern":
        # Amount pattern: очень подозрительный паттерн сумм (все одинаковые или очень близкие)
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            base_amount = random.choice([9999, 12500, 19999])  # Подозрительные суммы

            for i in range(45):
                op_date = PERIOD_FROM + timedelta(hours=i)
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                # Все суммы одинаковые или отличаются на 1-2%
                tx['Цена'] = base_amount + random.randint(-100, 100)
                transactions.append(tx)
                order_counter += 1

    elif scenario_name == "same_route_abuse":
        # Same route abuse: всегда один маршрут (признак распределённого скальпирования)
        for p_idx in range(num_passengers):
            fio = generate_fio()
            iin = generate_iin()
            dep_station = random.choice(STATIONS)
            arr_station = random.choice([s for s in STATIONS if s != dep_station])

            for i in range(35):
                op_date = PERIOD_FROM + timedelta(hours=random.randint(0, 168))
                tx = create_transaction(order_counter, "Оформление", op_date, fio, iin=iin)
                # Всегда один маршрут
                tx['Станция отправления'] = dep_station
                tx['Станция назначения'] = arr_station
                # Разные поезда но один маршрут
                tx['Номер поезда'] = random.choice(TERMINALS)
                transactions.append(tx)
                order_counter += 1

    return transactions

# Генерирование всех сценариев
all_transactions = []

scenarios = {
    "clean_users": 15,  # Чистые пользователи - low risk
    "scalpers": 5,  # Скальперы - medium/high risk
    "refund_abusers": 5,  # Абузеры возвратов - high risk
    "quick_refunders": 3,  # Быстрые возвраты - high risk
    "late_refunders": 3,  # Поздние возвраты - medium risk
    "night_bots": 3,  # Ночные боты - high risk
    "fake_identity": 2,  # Поддельные личности - high risk
    "organized_ring": 2,  # Организованное кольцо - high risk
    "concentrated_activity": 3,  # Сконцентрированная активность - medium risk
    "mixed_channels": 5,  # Смешанные каналы - low/medium risk
    "seat_blocking": 4,  # Seat blocking - высокий риск
    "terminal_hopping": 3,  # Прыжки между терминалами - medium risk
    "channel_anomaly": 3,  # Аномалии по каналам - medium risk
    "amount_pattern": 2,  # Подозрительные паттерны сумм - medium risk
    "same_route_abuse": 3,  # Всегда один маршрут - medium risk
}

print("🔄 Генерирую тестовые данные со всеми сценариями фрода...")
for scenario_name, num_passengers in scenarios.items():
    transactions = create_scenario(scenario_name, num_passengers)
    all_transactions.extend(transactions)
    print(f"  ✓ {scenario_name}: {len(transactions)} транзакций")

if not all_transactions:
    print("❌ ОШИБКА: Нет данных!")
    exit(1)

# Создание DataFrame
df = pd.DataFrame(all_transactions)

print(f"\n📊 DataFrame создан: {len(df)} строк, {len(df.columns)} колонок")
print(f"Колонки: {list(df.columns)}")

# Сохранение в Excel
df.to_excel(OUTPUT_FILE, index=False, sheet_name='transactions', engine='openpyxl')

print(f"\n✅ Файл создан: {OUTPUT_FILE}")
print(f"📊 Всего транзакций: {len(df)}")
print(f"\n📈 Статистика по типам операций:")
print(df['Операция'].value_counts())
print(f"\n💼 Все 10 сценариев фрода созданы:")
for scenario_name in scenarios.keys():
    print(f"  - {scenario_name}")
print(f"\n📋 Всего колонок: {len(df.columns)}")
