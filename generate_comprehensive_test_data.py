#!/usr/bin/env python3
import csv
import random
from datetime import datetime, timedelta
import uuid

# Configuration
NUM_TOTAL_RECORDS = 450  # Total transactions
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 5, 31)

# Train and location data
TRAINS = ["001T", "002P", "003E", "004D", "005B", "006C", "007D", "008F", "009G", "010H"]
CITIES = ["Almaty", "Astana", "Karaganda", "Aktobe", "Atyrau", "Semey", "Pavlodar", "Shymkent", "Uralsk", "Oral"]
CHANNELS = ["Web", "Mobile", "Office", "Call Center"]
AGGREGATORS = ["Booking.com", "Yandex", "KassaKz", "Direct"]
STATUSES = ["Completed", "Cancelled", "Pending", "Returned"]
WAGONS = list(range(1, 11))

def generate_date_range():
    """Generate random date within range"""
    days = (END_DATE - START_DATE).days
    return START_DATE + timedelta(days=random.randint(0, days))

def generate_departure_date(op_date):
    """Generate departure date after operation date"""
    days_ahead = random.randint(1, 30)
    return op_date + timedelta(days=days_ahead)

# ============ NORMAL PASSENGERS (100) ============
normal_passengers = []
for i in range(100):
    fio = f"Пассажир {i:03d}"
    iin = f"{800 + (i % 2):03d}{100 + (i % 100):02d}{10 + (i % 90):02d}{100000 + i:06d}"
    doc = f"ID{1000000 + i}"
    phone = f"+7701{100000 + i:06d}"
    email = f"pass{i}@mail.kz"
    normal_passengers.append((fio, iin, doc, phone, email))

# ============ STRUCTURING CASES (40) ============
structuring_passengers = []
for i in range(40):
    fio = f"Структурирование {i:02d}"
    iin = f"860{100 + i:03d}{100000 + i:06d}"
    doc = f"STRUCT{1000 + i}"
    phone = f"+7702{100000 + i:06d}"
    email = f"struct{i}@mail.kz"
    structuring_passengers.append((fio, iin, doc, phone, email))

# ============ HIGH AMOUNT ANOMALIES (30) ============
high_amount_passengers = []
for i in range(30):
    fio = f"Высокая сумма {i:02d}"
    iin = f"870{100 + i:03d}{100000 + i:06d}"
    doc = f"HIGH{2000 + i}"
    phone = f"+7703{100000 + i:06d}"
    email = f"high{i}@mail.kz"
    high_amount_passengers.append((fio, iin, doc, phone, email))

# ============ SUSPICIOUS REFUND PATTERNS (35) ============
refund_passengers = []
for i in range(35):
    fio = f"Подозрительные возвраты {i:02d}"
    iin = f"880{100 + i:03d}{100000 + i:06d}"
    doc = f"REF{3000 + i}"
    phone = f"+7704{100000 + i:06d}"
    email = f"refund{i}@mail.kz"
    refund_passengers.append((fio, iin, doc, phone, email))

# ============ FAKE DOCUMENTS (25) ============
fake_doc_passengers = []
for i in range(25):
    fio = f"Поддельный документ {i:02d}"
    iin = "999999999999"  # Obviously fake
    doc = f"FAKE{4000 + i}"
    phone = f"+7705{100000 + i:06d}"
    email = f"fake{i}@mail.kz"
    fake_doc_passengers.append((fio, iin, doc, phone, email))

# ============ LOCATION ANOMALIES (20) ============
location_anomaly_passengers = []
for i in range(20):
    fio = f"Геоаномалия {i:02d}"
    iin = f"890{100 + i:03d}{100000 + i:06d}"
    doc = f"LOC{5000 + i}"
    phone = f"+7706{100000 + i:06d}"
    email = f"loc{i}@mail.kz"
    location_anomaly_passengers.append((fio, iin, doc, phone, email))

# ============ COMPROMISED ACCOUNT (15 users, 1 document/phone) ============
compromised_doc = "COMPROMISED001"
compromised_phone = "+77077777777"
compromised_passengers = []
for i in range(15):
    fio = f"Скомпрометированный {i:02d}"
    iin = f"900{100 + i:03d}{100000 + i:06d}"
    email = f"comp{i}@mail.kz"
    compromised_passengers.append((fio, iin, compromised_doc, compromised_phone, email))

# Generate all records
records = []

# 1. Normal transactions
for name, iin, doc, phone, email in normal_passengers:
    num_txs = random.randint(2, 8)
    for _ in range(num_txs):
        op_date = generate_date_range()
        dep_date = generate_departure_date(op_date)
        records.append([
            name, iin, doc, phone, email,
            "PURCHASE",
            op_date.strftime("%Y-%m-%d %H:%M:%S"),
            dep_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            random.randint(25000, 85000),  # Normal range
            round(random.randint(500, 1700) * 2),
            random.choice(CHANNELS),
            random.choice(AGGREGATORS),
            random.choice(STATUSES),
            random.choice(CITIES)
        ])

# 2. Structuring (same passenger, many small amounts in short period)
for name, iin, doc, phone, email in structuring_passengers:
    base_date = generate_date_range()
    for day_offset in range(random.randint(8, 15)):
        op_date = base_date + timedelta(days=day_offset)
        dep_date = generate_departure_date(op_date)
        records.append([
            name, iin, doc, phone, email,
            "PURCHASE",
            op_date.strftime("%Y-%m-%d %H:%M:%S"),
            dep_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            random.randint(1500, 2500),  # Small amounts
            round(random.randint(30, 50) * 2),
            "Web",  # Consistent channel
            "Booking.com",
            "Completed",
            random.choice(CITIES)
        ])

# 3. High amount anomalies (5-10 huge transactions)
for name, iin, doc, phone, email in high_amount_passengers:
    num_txs = random.randint(1, 3)
    for _ in range(num_txs):
        op_date = generate_date_range()
        dep_date = generate_departure_date(op_date)
        records.append([
            name, iin, doc, phone, email,
            "PURCHASE",
            op_date.strftime("%Y-%m-%d %H:%M:%S"),
            dep_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            random.randint(450000, 600000),  # VERY high
            round(random.randint(9000, 12000) * 2),
            random.choice(CHANNELS),
            random.choice(AGGREGATORS),
            random.choice(STATUSES),
            random.choice(CITIES)
        ])

# 4. Suspicious refund patterns (multiple similar refunds same day)
for name, iin, doc, phone, email in refund_passengers:
    base_date = generate_date_range()
    # 2-4 refunds on same day with similar amounts
    num_refunds = random.randint(2, 4)
    amount = random.randint(65000, 85000)
    for _ in range(num_refunds):
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        op_time = base_date.replace(hour=hour, minute=minute)
        records.append([
            name, iin, doc, phone, email,
            "REFUND",
            op_time.strftime("%Y-%m-%d %H:%M:%S"),
            base_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            amount,  # Same/similar amount
            round(amount * 0.02),
            random.choice(CHANNELS),
            random.choice(AGGREGATORS),
            "Completed",
            random.choice(CITIES)
        ])

# 5. Fake documents (multiple weird IIN)
for name, iin, doc, phone, email in fake_doc_passengers:
    num_txs = random.randint(3, 8)
    for _ in range(num_txs):
        op_date = generate_date_range()
        dep_date = generate_departure_date(op_date)
        op_hour = random.randint(0, 5) if random.random() < 0.6 else random.randint(23, 23)  # Night hours
        op_date = op_date.replace(hour=op_hour)
        records.append([
            name, iin, doc, phone, email,
            "PURCHASE",
            op_date.strftime("%Y-%m-%d %H:%M:%S"),
            dep_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            random.randint(15000, 45000),
            round(random.randint(300, 900) * 2),
            random.choice(CHANNELS),
            random.choice(AGGREGATORS),
            random.choice(STATUSES),
            random.choice(CITIES)
        ])

# 6. Location anomalies (impossible travel)
for name, iin, doc, phone, email in location_anomaly_passengers:
    cities_sequence = random.sample(CITIES, 3)
    base_date = generate_date_range()
    for i, city in enumerate(cities_sequence):
        op_date = base_date + timedelta(days=i * 2)
        dep_date = generate_departure_date(op_date)
        records.append([
            name, iin, doc, phone, email,
            "PURCHASE",
            op_date.strftime("%Y-%m-%d %H:%M:%S"),
            dep_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            random.randint(20000, 60000),
            round(random.randint(400, 1200) * 2),
            random.choice(CHANNELS),
            random.choice(AGGREGATORS),
            "Completed",
            city
        ])

# 7. Compromised account (many people using same doc/phone)
for name, iin, doc, phone, email in compromised_passengers:
    num_txs = random.randint(2, 6)
    for _ in range(num_txs):
        op_date = generate_date_range()
        dep_date = generate_departure_date(op_date)
        records.append([
            name, iin, doc, phone, email,
            "PURCHASE",
            op_date.strftime("%Y-%m-%d %H:%M:%S"),
            dep_date.strftime("%Y-%m-%d"),
            random.choice(TRAINS),
            random.choice(WAGONS),
            random.randint(1, 54),
            random.randint(10000, 80000),
            round(random.randint(200, 1600) * 2),
            random.choice(CHANNELS),
            random.choice(AGGREGATORS),
            random.choice(STATUSES),
            random.choice(CITIES)
        ])

# Write CSV
with open("comprehensive_test_data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ФИО", "ИИН", "Документ", "Телефон", "Email", "Тип операции", "Дата операции",
                     "Дата отправления", "Поезд", "Вагон", "Место", "Сумма", "Комиссия", "Канал",
                     "Агрегатор", "Статус", "Назначение"])
    writer.writerows(records)

print(f"✅ Generated {len(records)} transactions for {len(set(r[0] for r in records))} unique passengers")
print(f"   File: comprehensive_test_data.csv")
