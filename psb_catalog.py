# 1. МАППИНГ ТРЕНДОВ (Связка с Марковым)
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
    'Электроника': 'Электроника'
}

# Если Марков предсказал Х, мы ищем продукты с этими тегами
PREDICTION_TAGS = {
    'Путешествия': ['travel', 'insurance', 'currency'],
    'Фастфуд': ['food', 'shopping', 'cashback'],
    'Супермаркеты': ['groceries', 'shopping', 'family'],
    'АЗС': ['car', 'fuel', 'cashback'],
    'Дом и Ремонт': ['repair', 'home', 'credit', 'big_spend'],
    'Аптеки': ['pharmacy', 'health', 'social'],
    'Развлечения': ['entertainment', 'food', 'youth'],
    'Детские товары': ['family', 'kids', 'shopping'],
    'Одежда и Спорт': ['shopping', 'sport', 'lifestyle'],
    'Красота': ['lifestyle', 'shopping', 'beauty'],
    'Транспорт': ['transfer', 'city', 'transport'],
    'Электроника': ['tech', 'credit', 'shopping']
}

# 3. ПОЛНЫЙ КАТАЛОГ ПРОДУКТОВ
CATALOG = {
    "debit": [
        {
            "name": "Дебетовая карта «Твой кешбэк»",
            "desc": "Хит банка: 1.5% на всё или до 5% в 3-х категориях на выбор.",
            "segment": ["MASS", "YOUTH", "SAVER"],
            "tags": ["shopping", "food", "lifestyle", "cashback"]
        },
        {
            "name": "Зарплатная карта «Твой Плюс»",
            "desc": "Бесплатное обслуживание и переводы для зарплатных клиентов.",
            "segment": ["MASS"],
            "tags": ["salary", "transfer", "cash"]
        },
        {
            "name": "Зарплатная карта «Сильные люди»",
            "desc": "Тариф особого назначения для работников ОПК и силовых структур.",
            "segment": ["DEFENSE", "MASS"],
            "tags": ["salary", "gov", "transfer", "defense"]
        },
        {
            "name": "Карта «СВОи»",
            "desc": "Электронное удостоверение ветерана боевых действий + карта.",
            "segment": ["DEFENSE"],
            "tags": ["gov", "social", "defense"]
        },
        {
            "name": "Orange Premium Club",
            "desc": "Премиальный сервис, проходы в бизнес-залы, страховка, консьерж.",
            "segment": ["VIP"],
            "tags": ["travel", "luxury", "service", "currency"]
        },
        {
            "name": "Пенсионная карта ПСБ",
            "desc": "Процент на остаток, защита от мошенников, бесплатное SMS.",
            "segment": ["SAVER"],
            "tags": ["social", "pharmacy", "groceries"]
        },
        {
            "name": "Карта для пенсионеров силовых структур",
            "desc": "Особые условия для ветеранов службы.",
            "segment": ["SAVER", "DEFENSE"],
            "tags": ["social", "gov", "defense"]
        },
        {
            "name": "Клубная карта ПФК ЦСКА",
            "desc": "Уникальный дизайн и привилегии для болельщиков.",
            "segment": ["YOUTH", "MASS"],
            "tags": ["sport", "entertainment", "fan"]
        },
        {
            "name": "Карта «Только вперед»",
            "desc": "Для активных людей: спорт, здоровье и движение.",
            "segment": ["YOUTH"],
            "tags": ["sport", "lifestyle"]
        },
        {
            "name": "Единая карта петербуржца",
            "desc": "Банковская карта, проездной и полис ОМС в одном пластике.",
            "segment": ["MASS", "SAVER"],
            "tags": ["city", "transport", "social"]
        },
        {
            "name": "Платежный стикер",
            "desc": "Клейте на смартфон и платите как раньше.",
            "segment": ["YOUTH", "MASS", "VIP"],
            "tags": ["tech", "shopping"]
        }
    ],
    "credit": [
        {
            "name": "Кредитная карта «100+»",
            "desc": "Честные 101 день без % на всё, включая снятие наличных.",
            "segment": ["MASS", "DEFENSE", "YOUTH", "CREDIT_RISK"],
            "tags": ["big_spend", "cash", "repair", "tech", "debt"]
        },
        {
            "name": "Кредитка «Двойной кешбэк»",
            "desc": "10% кешбэк за погашение задолженности. Зарабатывайте тратя.",
            "segment": ["MASS", "YOUTH"],
            "tags": ["shopping", "tech", "entertainment", "food"]
        },
        {
            "name": "Премиальная кредитная карта",
            "desc": "Лимит до 1.5 млн ₽, индивидуальная ставка.",
            "segment": ["VIP"],
            "tags": ["luxury", "travel", "big_spend"]
        },
        {
            "name": "Кредит для работников ОПК",
            "desc": "Сниженная ставка для сотрудников оборонных предприятий.",
            "segment": ["DEFENSE"],
            "tags": ["gov", "repair", "car", "defense"]
        },
        {
            "name": "Экспресс-кредит «Турбоденьги»",
            "desc": "Деньги на карту за 5 минут без визита в офис.",
            "segment": ["MASS", "YOUTH", "CREDIT_RISK"],
            "tags": ["fast_cash", "online", "urgent"]
        },
        {
            "name": "Рефинансирование кредитов",
            "desc": "Объедините кредиты других банков и платите меньше.",
            "segment": ["MASS", "CREDIT_RISK", "SAVER"],
            "tags": ["debt", "optimization"]
        },
        {
            "name": "Кредит под залог квартиры",
            "desc": "Крупная сумма на долгий срок под низкий процент.",
            "segment": ["MASS", "SAVER"],
            "tags": ["big_spend", "repair", "construction"]
        }
    ],
    "invest": [
        {
            "name": "Накопительный счет «Акцент»",
            "desc": "Ставка растет вместе с вашими тратами по карте.",
            "segment": ["YOUTH", "MASS"],
            "tags": ["saving", "salary", "shopping"]
        },
        {
            "name": "Вклад «Сильная ставка»",
            "desc": "Максимальная доходность для зарплатных клиентов ОПК.",
            "segment": ["DEFENSE"],
            "tags": ["saving", "gov", "defense", "conservative"]
        },
        {
            "name": "Вклад «Мой доход»",
            "desc": "Фиксированная высокая ставка. Надежность и доход.",
            "segment": ["SAVER", "MASS"],
            "tags": ["saving", "conservative"]
        },
        {
            "name": "Вклад «Социальный»",
            "desc": "Специальные условия для получения пенсий и пособий.",
            "segment": ["SAVER"],
            "tags": ["social", "saving"]
        },
        {
            "name": "Вклад «В юанях»",
            "desc": "Диверсификация портфеля в дружественной валюте.",
            "segment": ["VIP", "MASS"],
            "tags": ["currency", "risk"]
        },
        {
            "name": "Робот-советник",
            "desc": "Искусственный интеллект соберет портфель за вас.",
            "segment": ["YOUTH", "MASS"],
            "tags": ["tech", "stocks", "beginner"]
        },
        {
            "name": "ПСБ Инвестиции",
            "desc": "Приложение для торговли акциями и облигациями.",
            "segment": ["VIP", "YOUTH", "MASS"],
            "tags": ["tech", "stocks", "risk"]
        },
        {
            "name": "Вклад «Драгоценный»",
            "desc": "Инвестиции в драгметаллы для сохранения капитала.",
            "segment": ["VIP", "SAVER"],
            "tags": ["luxury", "conservative"]
        },
        {
            "name": "Брокерское обслуживание",
            "desc": "Доступ к биржевым инструментам для опытных инвесторов.",
            "segment": ["VIP", "MASS"],
            "tags": ["stocks", "risk"]
        }
    ],
    "mortgage": [
        {
            "name": "Военная ипотека",
            "desc": "Госпрограмма для военнослужащих. Квартира за счет государства.",
            "segment": ["DEFENSE"],
            "tags": ["home", "family", "gov", "defense"]
        },
        {
            "name": "Семейная ипотека",
            "desc": "Льготная ставка для семей с детьми.",
            "segment": ["MASS", "YOUTH", "DEFENSE"],
            "tags": ["family", "kids", "home"]
        },
        {
            "name": "Дальневосточная ипотека",
            "desc": "Минимальная ставка для жителей ДФО и Арктики.",
            "segment": ["MASS", "YOUTH"],
            "tags": ["home", "geo"]
        },
        {
            "name": "Ипотека на вторичное жилье",
            "desc": "Покупка готовой квартиры. Быстрое решение.",
            "segment": ["MASS", "VIP"],
            "tags": ["home", "big_spend"]
        }
    ],

    # === ЭКОСИСТЕМА (Services) ===
    "service": [
        {
            "name": "СБП Плюс",
            "desc": "Переводы без комиссии сверх стандартных лимитов.",
            "segment": ["ALL", "MASS", "VIP"],
            "tags": ["transfer", "tech"]
        },
        {
            "name": "Страховка путешественника",
            "desc": "Покрытие медицины и рисков в поездках по России и миру.",
            "segment": ["VIP", "YOUTH", "MASS"],
            "tags": ["travel", "health"]
        },
        {
            "name": "Private Banking",
            "desc": "Управление крупным частным капиталом.",
            "segment": ["VIP"],
            "tags": ["luxury", "service", "invest"]
        }
    ]
}