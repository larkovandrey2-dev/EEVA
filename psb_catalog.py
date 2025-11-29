# psb_catalog.py - Единая база знаний продуктов

# 1. СЛОВАРЬ МАППИНГА (Техническая связка Маркова с Тегами)
# Исправляет ошибку "TREND_MAPPING is not defined"
TREND_MAPPING = {
    'Фастфуд': 'Фастфуд',
    'Супермаркеты': 'Супермаркеты',
    'Аптеки': 'Аптеки',
    'Путешествия': 'Путешествия',
    'Одежда и Спорт': 'Одежда и Спорт',
    'Развлечения': 'Развлечения',
    'Дом и Ремонт': 'Дом и Ремонт',
    'Детские товары': 'Детские товары',
    'АЗС': 'АЗС',
    'Красота': 'Красота',
    'Транспорт': 'Транспорт',
    'Электроника': 'Дом и Ремонт'
}

# 2. ТЕГИ ПРЕДСКАЗАНИЙ
PREDICTION_TAGS = {
    'Путешествия': ['travel', 'insurance'],
    'Фастфуд': ['food', 'shopping'],
    'Супермаркеты': ['groceries', 'shopping'],
    'АЗС': ['car'],
    'Дом и Ремонт': ['repair', 'home', 'credit'],
    'Аптеки': ['pharmacy', 'health'],
    'Развлечения': ['entertainment', 'food'],
    'Детские товары': ['family', 'shopping'],
    'Одежда и Спорт': ['shopping', 'sport'],
    'Красота': ['lifestyle', 'shopping'],
    'Транспорт': ['transfer', 'city'],
    'Электроника': ['tech', 'credit']
}

# 3. КАТАЛОГ ПРОДУКТОВ
CATALOG = {
    "debit": [
        {
            "name": "Карта «Твой кешбэк»",
            "desc": "Конструктор выгоды: 1.5% на всё или повышенный кешбэк в 3 категориях.",
            "segment": ["MASS", "YOUTH", "SAVER"],
            "tags": ["shopping", "food", "lifestyle"]
        },
        {
            "name": "Дебетовая карта «ПСБ — ЦСКА»",
            "desc": "Эксклюзивная карта для болельщиков ПФК ЦСКА.",
            "segment": ["MASS", "YOUTH"],
            "tags": ["sport", "entertainment"]
        },
        {
            "name": "Зарплатная карта «Сильные люди»",
            "desc": "Особые условия для работников ОПК и силовых структур.",
            "segment": ["DEFENSE", "MASS"],
            "tags": ["salary", "gov", "transfer"]
        },
        {
            "name": "Orange Premium Club",
            "desc": "Премиальное обслуживание, бизнес-залы, трансферы.",
            "segment": ["VIP"],
            "tags": ["travel", "luxury", "service"]
        },
        {
            "name": "Пенсионная карта",
            "desc": "Бесплатное обслуживание, % на остаток, защита.",
            "segment": ["SAVER"],
            "tags": ["social", "pharmacy", "groceries"]
        }
    ],

    "credit": [
        {
            "name": "Кредитная карта «100+»",
            "desc": "Честные 101 день без процентов. Снятие наличных без комиссии.",
            "segment": ["MASS", "DEFENSE", "SAVER", "YOUTH"],
            "tags": ["big_spend", "cash", "repair", "tech", "shopping"]
        },
        {
            "name": "Кредитка «Двойной кешбэк»",
            "desc": "10% кешбэк за погашение задолженности.",
            "segment": ["MASS", "YOUTH"],
            "tags": ["shopping", "tech", "entertainment"]
        },
        {
            "name": "Премиальная кредитная карта",
            "desc": "Лимит до 1.5 млн руб, индивидуальная ставка.",
            "segment": ["VIP"],
            "tags": ["luxury", "travel"]
        }
    ],

     "invest": [
        {
            "name": "Накопительный счет «Акцент»",
            "desc": "До 14% годовых при тратах по карте.",
            "segment": ["YOUTH", "MASS"],
            "tags": ["saving", "salary"]
        },
        {
            "name": "Вклад «Сильная ставка»",
            "desc": "Максимальная доходность для клиентов ОПК.",
            "segment": ["DEFENSE"],
            "tags": ["saving", "gov"]
        }
    ],
}