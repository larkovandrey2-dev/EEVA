import streamlit as st
import pandas as pd
import numpy as np

st.markdown("""
<style>
    .main .block-container { 
        padding-top: 2rem; 
        max-width: 100% !important;
        text-align: left;  /* Общий выравнивание — лево, кроме заголовка */
    }
    h1 { 
        text-align: center !important;  /* Только заголовок по центру */
        color: #1E3A8A !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        white-space: normal !important;
        word-wrap: break-word !important; 
        line-height: 1.3;
        font-size: 2em;
        margin-bottom: 1rem;
    }
    .logo-container { 
        text-align: center; 
        margin: 1rem auto; 
        display: block; 
        width: 100%; 
    }
    .st-emotion-cache-1rk4zq {
        text-align: center !important; 
    }
    .stButton > button { 
        background-color: #FF6200; 
        color: white; 
        border-radius: 10px; 
        width: 100%; 
        max-width: 300px; 
        margin: 0 auto; 
        display: block; 
    }
</style>
""", unsafe_allow_html=True)

# Mock: Загрузка профиля с заглушкой
@st.cache_data
def load_user_profile(user_id):
    # Просто маппинг user_id -> кластер
    cluster_mapping = {
        'user123': 'Универсальные продукты',
        'user456': 'Для военнослужащих и ОПК',
        'user789': 'Пенсионные программы',
        'user999': 'Инвестиции и накопления',
        'user007': 'Премиум-банкинг',
    }

    cluster = cluster_mapping.get(user_id, 'Универсальные продукты')  # fallback

    if user_id in cluster_mapping:
        st.info(f"Загружен профиль пользователя **{user_id}**, кластер: **{cluster}**")
    else:
        st.warning(f"Пользователь **{user_id}** не найден в базе, используем универсальный кластер: **{cluster}**")

    return {'cluster': cluster}


# Загрузка продуктов (полный список из 49 продуктов)
@st.cache_data
def load_products():
    data = [
        # Универсальные продукты
        (1, "Кредит на любые цели", "Универсальные продукты", "https://www.psbank.ru/personal/loans/specialpurpose"),
        (2, "Дебетовая карта «Твой кешбэк»", "Универсальные продукты", "https://psbank-certifikat.ru/"),
        (3, "Зарплатная карта «Твой Плюс»", "Универсальные продукты", "https://www.psbank.ru/personal/salary/plus"),
        (4, "Вклад «Моя копилка»", "Универсальные продукты", "https://www.psbank.ru/personal/saving/mymoneybox"),
        (5, "Вклад «Стабильный доход»", "Универсальные продукты", "https://www.psbank.ru/personal/saving/stabilnyi-dokhod"),
        (6, "Накопительный счет «Акцент на процент»", "Универсальные продукты",
         "https://www.psbank.ru/personal/savingsaccount/accentpercent"),
        (7, "ПСБ Инвестиции", "Универсальные продукты", "https://www.psbank.ru/personal/wealth/app"),
        (8, "Робот-советник", "Универсальные продукты", "https://www.psbank.ru/personal/wealth/robot-adviser"),
        (9, "Брокерский счет", "Универсальные продукты", "https://www.psbank.ru/personal/wealth/brokerskiy-schet"),
        # Специальные предложения
        (10, "Вклад «Мои возможности»", "Специальные предложения", "https://www.psbank.ru/personal/saving/mypossiblities"),
        (11, "Платежный стикер к карте «Твой кешбэк»", "Специальные предложения",
         "https://www.psbank.ru/personal/cards/stiker"),
        (12, "Зарплатная карта «Зарплата PRO»", "Специальные предложения", "https://www.psbank.ru/personal/salary/salarypro"),
        (13, "Индивидуальная зарплатная карта", "Специальные предложения", "https://www.psbank.ru/personal/salary/izp"),
        (14, "Накопительный счет «Про запас»", "Специальные предложения",
         "https://www.psbank.ru/personal/savingsaccount/in_store"),
        (15, "Накопительный счет «Хранитель»", "Специальные предложения",
         "https://www.psbank.ru/personal/savingsaccount/hranitel"),
        # Региональные программы
        (16, "Госпрограмма. Военная ипотека. Новые субъекты", "Региональные программы",
         "https://www.psbank.ru/personal/mortgage/military-new-territories"),
        (17, "Карта жителя - Питер", "Региональные программы", "https://www.psbank.ru/personal/debetcards/residentcard"),
        (18, "Дальневосточная и арктическая ипотека", "Региональные программы",
         "https://www.psbank.ru/personal/mortgage/east"),
        (19, "Вклад «В юанях»", "Региональные программы", "https://www.psbank.ru/personal/saving/yuan"),
        # Для военнослужащих и ОПК
        (20, "Кредит для работников предприятий ОПК и военнослужащих", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/loans/creditaction"),
        (21, "«СВОи»", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/salary/svoi"),
        (22, "Зарплатная карта «Сильные люди. Тариф особого назначения»", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/salary/strongpeople"),
        (23, "Военная ипотека", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/mortgage/military"),
        (24, "Военная ипотека. Рефинансирование", "Для военнослужащих и ОПК",
         "https://www.psbank.ru/personal/mortgage/refinancing-military"),
        (25, "Семейная военная ипотека", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/mortgage/family-military-mortgage"),
        (26, "Госпрограмма. Военная ипотека. Новые субъекты", "Для военнослужащих и ОПК",
         "https://www.psbank.ru/personal/mortgage/military-new-territories"),
        (27, "Военная ипотека.", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/mortgage/military"),
        (28, "Новые субъекты", "Для военнослужащих и ОПК", "https://www.psbank.ru/personal/mortgage/family-military-mortgage"),
        # Пенсионные программы
        (29, "Дебетовая пенсионная карта ПСБ", "Пенсионные программы", "https://www.psbank.ru/personal/pensioncards/pensioncard"),
        (30, "Карта для пенсионеров силовых структур и ветеранов боевых действий", "Пенсионные программы",
         "https://www.psbank.ru/personal/pensioncards/militarypension"),
        (31, "Вклад «Социальный вклад»", "Пенсионные программы", "https://www.psbank.ru/personal/saving/social"),
        (32, "Вклад «Мой доход»", "Пенсионные программы", "https://www.psbank.ru/personal/saving/myincome"),
        # Партнёрские карты (спорт)
        (33, "Дебетовая Клубная карта ПФК ЦСКА", "Партнёрские карты (спорт)", "https://www.psbank.ru/personal/debetcards/cska"),
        (34, "Дебетовая карта «Только вперед»", "Партнёрские карты (спорт)", "https://www.psbank.ru/personal/debetcards/tolko-vpered"),
        # Быстрые кредиты
        (35, "Экспресс-кредит «Турбоденьги»", "Быстрые кредиты", "https://www.psbank.ru/personal/loans/turbomoney"),
        (36, "Рефинансирование кредитов", "Быстрые кредиты", "https://www.psbank.ru/personal/loans/refinancing"),
        (37, "Кредит под залог квартиры", "Быстрые кредиты", "https://www.psbank.ru/personal/mortgage/alternative"),
        # Инвестиции и накопления
        (38, "Вклад «Сильная ставка»", "Инвестиции и накопления", "https://www.psbank.ru/personal/saving/strong_bid"),
        (39, "Вклад «Драгоценный»", "Инвестиции и накопления", "https://www.psbank.ru/personal/saving/dragotsennyj"),
        (40, "Вклад «Ставка на будущее»", "Инвестиции и накопления", "https://www.psbank.ru/personal/saving/stavka-na-budushchee"),
        (41, "Открытые паевые инвестиционные фонды", "Инвестиции и накопления", "https://www.psbank.ru/personal/wealth/mutualfonds"),
        (42, "Персональный брокер", "Инвестиции и накопления", "https://www.psbank.ru/personal/wealth/personal-broker"),
        (43, "Индивидуальный инвестиционный счет", "Инвестиции и накопления",
         "https://www.psbank.ru/personal/wealth/individualaccounts"),
        (44, "Биржевые паевые фонды", "Инвестиции и накопления", "https://www.psbank.ru/personal/wealth/bpif"),
        (45, "Вторичное жилье", "Инвестиции и накопления", "https://www.psbank.ru/personal/mortgage/secondary"),
        # Семейное
        (46, "Семейная ипотека", "Семейная ипотека", "https://www.psbank.ru/personal/mortgage/familymortgage"),
        (47, "Семейная военная ипотека", "Семейная ипотека",
         "https://www.psbank.ru/personal/mortgage/family-military-mortgage"),
        # Премиум-банкинг
        (48, "Orange Premium Club", "Премиум-банкинг", "https://www.psbank.ru/personal/orangeclub"),
        (49, "Private Banking", "Премиум-банкинг", "https://www.psbank.ru/private")
    ]
    df = pd.DataFrame(data, columns=['id', 'product', 'category', 'url'])
    np.random.seed(42)
    df['score'] = np.random.uniform(0.7, 1.0, len(df))
    return df


# Рекомендации с заглушкой для пустого кластера
def recommend_products(profile):
    df = load_products()
    cluster = profile['cluster']
    filtered = df[df['category'] == cluster].copy()
    if filtered.empty:
        st.warning("Нет продуктов в кластере - показываем универсальные топ-рекомендации.")
        filtered = df.copy()  # Fallback: все продукты
    # Sort по score descending, head(3)
    filtered = filtered.sort_values('score', ascending=False).head(3)
    filtered = filtered.reset_index(drop=True)
    filtered['rank'] = range(1, len(filtered) + 1)
    return filtered[['rank', 'product', 'url']]


# LLM-ответ (как раньше, с fallback)
def generate_llm_response(profile, recs, user_id):
    cluster = profile['cluster']
    products_list = ", ".join(recs['product'].tolist())

    if cluster == 'Универсальные продукты':
        return f"""
        **Привет, {user_id}!** Мы проанализировали твой профиль и подобрали идеальные базовые продукты из кластера 'Универсальные продукты'. 

        Вот топ-3 по актуальности:

        1. **{recs.iloc[0]['product']}** - гибкий заём без лишней бюрократии, чтобы воплотить планы прямо сейчас. 

        2. **{recs.iloc[1]['product']}** - возвращай до 30% на покупки.

        3. **{recs.iloc[2]['product']}** - бонусы и кэшбэк на зарплату, плюс бесплатные переводы.

        Эти опции помогут оптимизировать твои финансы без риска. Готов оформить? Нажми на ссылки ниже или свяжись с менеджером - консультация бесплатно!
        """
    # Добавь для других...
    else:
        return f"**Рекомендации для {user_id}:** Подходят продукты {products_list}. Оформи сегодня!"


# UI



# Центрированный логотип
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("Логотип_ПСБ.png", width=540,)

st.title("Рекомендательная система банковских продуктов")


user_id = st.text_input("User ID:", placeholder="Например: user123")

if st.button("Получить рекомендации"):
    if not user_id:
        st.warning("Введи user_id!")
    else:
        profile = load_user_profile(user_id)
        recs = recommend_products(profile)
        if not recs.empty:
            st.success(f"Рекомендации для {user_id}:")

            # LLM-ответ с fallback
            llm_response = generate_llm_response(profile, recs, user_id)
            st.markdown(llm_response)

            # Таблица
            st.dataframe(
                recs,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "rank": st.column_config.NumberColumn("Ранг", format="%d"),
                    "product": st.column_config.TextColumn("Продукт"),
                    "url": st.column_config.LinkColumn("Оформить")
                }
            )

        else:
            st.error("Датасет продуктов пуст - заглушка недоступна. Проверь load_products().")

