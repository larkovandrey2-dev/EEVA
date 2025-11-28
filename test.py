import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==========================================
# 1. ЗАГРУЗКА ДАННЫХ
# ==========================================
st.set_page_config(page_title="EEVA Demo", layout="wide")


@st.cache_data
def load_data():
    # Данные о юзерах и кластерах
    users = pd.read_csv("clean_data/users_clustered.csv")
    users.set_index('user_id', inplace=True)



    return users


try:
    users_df, actions_df, matrix_df = load_data()
except Exception as e:
    st.error(f"Ошибка загрузки данных! Проверь, что шаги 01-06 выполнены. {e}")
    st.stop()

# ==========================================
# 2. БАЗА ЗНАНИЙ (Продукты банка)
# ==========================================
# В реальности это берется из БД, здесь хардкодим под ПСБ
PRODUCT_CATALOG = {
    'Путешествия': [
        {'name': 'Кредитка "ПСБ Travel"', 'desc': 'Страховка в подарок + 5% милями', 'type': 'credit'},
        {'name': 'Валютный счет', 'desc': 'Льготный курс обмена', 'type': 'debit'}
    ],
    'Дом и Ремонт': [
        {'name': 'Потреб. кредит "Уютный"', 'desc': 'До 5 млн на ремонт под 12%', 'type': 'loan'},
        {'name': 'Страхование квартиры', 'desc': 'Защита от залива соседями', 'type': 'insure'}
    ],
    'Детские товары': [
        {'name': 'Карта "ПСБ Детская"', 'desc': 'Лимиты для ребенка + контроль в приложении', 'type': 'debit'},
        {'name': 'Накопительный "На вырост"', 'desc': 'Высокий % с капитализацией', 'type': 'invest'}
    ],
    'Аптеки': [
        {'name': 'Пакет "Здоровье"', 'desc': 'Кешбэк 10% в аптеках + Телемедицина', 'type': 'service'}
    ],
    'Фастфуд': [
        {'name': 'Молодежная карта', 'desc': 'Повышенный кешбэк на бургеры и кино', 'type': 'debit'}
    ],
    'Супермаркеты': [
        {'name': 'Кредитка "Двойной кешбэк"', 'desc': '10% на продукты и ЖКХ', 'type': 'credit'}
    ],
    'Прочее': [
        {'name': 'Вклад "Сильный процент"', 'desc': 'Максимальная ставка на остаток', 'type': 'invest'}
    ]
}

# Описания кластеров (чтобы жюри понимало)
CLUSTER_NAMES = {
    0: "🛍 Шопоголик",
    1: "🦉 Ночная жизнь (Студент)",
    2: "👶 Семьянин",
    3: "🍔 Фастфуд-ловец",
    4: "💼 Карьерист",
    5: "🏠 Домосед",
    6: "💰 Инвестор"
    # Можешь подправить названия, глянув на output из step 5
}

# ==========================================
# 3. ИНТЕРФЕЙС
# ==========================================

# Сайдбар
st.sidebar.title("EEVA Control Panel")
input_user_id = st.sidebar.text_input("Введите User ID", value=str(users_df.index[0]))

try:
    user_id = int(input_user_id)
except:
    st.sidebar.error("ID должен быть числом")
    st.stop()

if user_id not in users_df.index:
    st.error("Пользователь не найден в базе!")
    st.stop()

# Данные текущего юзера
user_data = users_df.loc[user_id]
user_last_action = actions_df.loc[user_id] if user_id in actions_df.index else None

# === ЗАГОЛОВОК ===
st.title(f"👤 Профиль клиента #{user_id}")
st.markdown("---")

col1, col2, col3 = st.columns(3)

# БЛОК 1: КТО ОН? (Static Profile)
cluster_id = int(user_data['cluster_id'])
cluster_name = CLUSTER_NAMES.get(cluster_id, f"Кластер {cluster_id}")

with col1:
    st.header("1. Архетип (Кто?)")
    st.info(f"🏷 **{cluster_name}**")
    st.write(f"💰 Средний чек: **{user_data['avg_check']:.0f} ₽**")
    st.write(f"🌙 Активность ночью: **{user_data['night_share'] * 100:.1f}%**")
    st.write(f"💳 Всего транзакций: **{user_data['tx_count']}**")

    # График трат
    cats = [c for c in user_data.index if c.startswith('share_') and user_data[c] > 0]
    vals = [user_data[c] for c in cats]
    clean_cats = [c.replace('share_', '') for c in cats]

    if vals:
        fig = px.pie(values=vals, names=clean_cats, title="Структура трат")
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)


# Debug инфа внизу
with st.expander("🔧 Посмотреть сырые данные JSON"):
    st.json(user_data.to_dict())