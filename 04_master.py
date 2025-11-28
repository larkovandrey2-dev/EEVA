import pandas as pd
import numpy as np


# НАСТРОЙКИ
CLEAN_DIR = "clean_data"
INPUT_PAY = f"{CLEAN_DIR}/payments_ready_for_ai.csv"
INPUT_USERS = f"{CLEAN_DIR}/train_users_10k.csv"
OUTPUT_FILE = f"{CLEAN_DIR}/master_features_final.csv"


pay = pd.read_csv(INPUT_PAY)
users = pd.read_csv(INPUT_USERS)

# Преобразуем дату (если она еще не datetime)
if 'timestamp' in pay.columns:
    # errors='coerce' превратит битые даты в NaT, чтобы не падал скрипт
    pay['dt'] = pd.to_datetime(pay['timestamp'], errors='coerce')



# Разделяем транзакции на две кучи
# Расходы - это всё, что меньше нуля
expenses = pay[pay['price'] < 0].copy()
# Доходы - это всё, что больше нуля
incomes = pay[pay['price'] > 0].copy()

# 1.1 Считаем РАСХОДЫ (Spending)
# Группируем расходы по юзерам
spend_stats = expenses.groupby('user_id').agg({
    'price': ['sum', 'min', 'count', 'mean']
}).reset_index()

# Переименовываем колонки (убираем мульти-индекс)
spend_stats.columns = ['user_id', 'total_spend_raw', 'max_spend_raw', 'tx_count', 'avg_spend_raw']

# sum: сумма всех трат (было -1000, станет 1000)
spend_stats['total_spend'] = spend_stats['total_spend_raw'].abs()
# min: минимальное число (-50000) - это и есть МАКСИМАЛЬНАЯ трата. Берем модуль.
spend_stats['max_spend'] = spend_stats['max_spend_raw'].abs()
# mean: средний чек
spend_stats['avg_check'] = spend_stats['avg_spend_raw'].abs()

# 1.2 Считаем ДОХОДЫ (Income)
income_stats = incomes.groupby('user_id')['price'].sum().reset_index(name='total_income')



if 'dt' in pay.columns:
    # Вытаскиваем час и день недели
    expenses['hour'] = expenses['dt'].dt.hour
    expenses['day_of_week'] = expenses['dt'].dt.dayofweek  # 0=Пн, 6=Вс

    # Создаем флаги
    # Ночь: с 00:00 до 06:00
    expenses['is_night'] = expenses['hour'].apply(lambda h: 1 if 0 <= h < 6 else 0)
    # Выходные: Суббота (5) и Воскресенье (6)
    expenses['is_weekend'] = expenses['day_of_week'].apply(lambda d: 1 if d >= 5 else 0)

    # Считаем среднее (это и будет доля: 0.2 = 20% покупок ночью)
    time_stats = expenses.groupby('user_id').agg({
        'is_night': 'mean',
        'is_weekend': 'mean'
    }).reset_index()

    time_stats.columns = ['user_id', 'night_share', 'weekend_share']
else:
    print("⚠️ Нет колонки timestamp, пропускаем анализ времени.")
    time_stats = pd.DataFrame(columns=['user_id'])



# Pivot Table: Строки=Юзеры, Столбцы=Категории, Значения=Сумма трат
# Берем только расходы (expenses), доходы нам тут не нужны
cats_pivot = expenses.pivot_table(
    index='user_id',
    columns='category_final',
    values='price',
    aggfunc='sum',
    fill_value=0
).abs()  # Сразу берем модуль

# Переводим в ПРОЦЕНТЫ (Доли)
# Делим сумму в категории на общую сумму трат юзера
cats_share = cats_pivot.div(cats_pivot.sum(axis=1), axis=0)

# Добавляем префикс share_, чтобы не путаться
cats_share.columns = [f"share_{c}" for c in cats_share.columns]
cats_share = cats_share.reset_index()



# Берем за основу список юзеров из файла train_users
master = users[['user_id']].copy()

# Приклеиваем расходы
master = master.merge(spend_stats[['user_id', 'total_spend', 'max_spend', 'tx_count', 'avg_check']], on='user_id',
                      how='left')

# Приклеиваем доходы
master = master.merge(income_stats, on='user_id', how='left')

# Приклеиваем время
master = master.merge(time_stats, on='user_id', how='left')

# Приклеиваем категории
master = master.merge(cats_share, on='user_id', how='left')

# Заполняем пропуски нулями (если человек ничего не тратил или не получал доход)
master = master.fillna(0)

master['net_saving'] = master['total_income'] - master['total_spend']
# % Сбережений (какую часть дохода откладывает)
# Защита от деления на ноль:
master['saving_rate'] = np.where(master['total_income'] > 0,
                                 master['net_saving'] / master['total_income'],
                                 0)

