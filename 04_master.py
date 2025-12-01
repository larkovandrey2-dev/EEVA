import pandas as pd
import numpy as np

# НАСТРОЙКИ
CLEAN_DIR = "clean_data"
INPUT_PAY = f"{CLEAN_DIR}/payments_ready.csv"     # Файл из Шага 2 (или 3)
INPUT_USERS = f"{CLEAN_DIR}/train_users_10k.csv"  # Список юзеров (если есть)
OUTPUT_FILE = f"{CLEAN_DIR}/master_features_final.csv"

print("Сборка финальных фичей")

# 1. Загрузка
pay = pd.read_csv(INPUT_PAY)

# Проверка, есть ли файл юзеров, если нет - берем уникальных из транзакций
try:
    users = pd.read_csv(INPUT_USERS)
except:
    users = pd.DataFrame({'user_id': pay['user_id'].unique()})


print("Обработка времени.")

# Парсим timedelta
pay['td'] = pd.to_timedelta(pay['timestamp'], errors='coerce')

# Вытаскиваем час и день
pay['hour'] = pay['td'].dt.components.hours
pay['day_idx'] = pay['td'].dt.days % 7

pay['is_night'] = pay['hour'].apply(lambda x: 1 if 0 <= x < 6 else 0)
pay['is_weekend'] = pay['day_idx'].apply(lambda x: 1 if x >= 5 else 0)

print("Флаги времени созданы.")


print("Считаем деньги.")

# Разделяем расходы и доходы
expenses = pay[pay['price'] < 0].copy()
incomes = pay[pay['price'] > 0].copy()

# 3.1 Статистика расходов
spend_stats = expenses.groupby('user_id').agg({
    'price': ['sum', 'count', 'mean', 'min']
}).reset_index()
spend_stats.columns = ['user_id', 'total_spend', 'tx_count', 'avg_check', 'max_spend']

spend_stats['total_spend'] = spend_stats['total_spend'].abs()
spend_stats['avg_check'] = spend_stats['avg_check'].abs()
spend_stats['max_spend'] = spend_stats['max_spend'].abs()

income_stats = incomes.groupby('user_id')['price'].sum().reset_index(name='total_income')

print("Считаем привычки (Ночь/Выходные).")

# Мы просто берем среднее от флагов по всем транзакциям юзера
time_stats = pay.groupby('user_id').agg({
    'is_night': 'mean',
    'is_weekend': 'mean'
}).reset_index()

time_stats.columns = ['user_id', 'night_share', 'weekend_share']

print("Cчитаем категории.")

# Pivot: строки=юзеры, столбцы=категории
cats_pivot = expenses.pivot_table(
    index='user_id',
    columns='category_final',
    values='price',
    aggfunc='sum',
    fill_value=0
).abs()

cats_share = cats_pivot.div(cats_pivot.sum(axis=1), axis=0).fillna(0)
cats_share.columns = [f"share_{c}" for c in cats_share.columns]
cats_share = cats_share.reset_index()


master = users[['user_id']].drop_duplicates().copy()

# Приклеиваем всё по очереди
master = master.merge(spend_stats, on='user_id', how='left')
master = master.merge(income_stats, on='user_id', how='left')
master = master.merge(time_stats, on='user_id', how='left')
master = master.merge(cats_share, on='user_id', how='left')

# Заполняем пропуски нулями
master = master.fillna(0)

# Доп. фича: % Сбережений
master['saving_rate'] = np.where(
    master['total_income'] > 0,
    (master['total_income'] - master['total_spend']) / master['total_income'],
    0
)

master.to_csv(OUTPUT_FILE, index=False)
