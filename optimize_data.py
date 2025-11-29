# optimize_data.py
import pandas as pd
import pickle
import os

print("🚀 Оптимизация данных для ускорения загрузки...")

# 1. Конвертируем Users CSV -> Parquet
# Parquet читается в 10-50 раз быстрее CSV и занимает меньше места
if os.path.exists("clean_data/users_clustered.csv"):
    print("   -> Конвертация users_clustered.csv...")
    users = pd.read_csv("clean_data/users_clustered.csv")
    users['user_id'] = users['user_id'].astype('int32')  # Оптимизация памяти
    # Сохраняем только нужные колонки
    cols = ['user_id', 'cluster_id', 'total_spend']
    # Добавляем другие, если они есть
    for c in ['region_name', 'soc_dem_cluster']:
        if c in users.columns: cols.append(c)

    users[cols].to_parquet("clean_data/users_fast.parquet", index=False)

# 2. Конвертируем Transactions CSV -> Parquet
if os.path.exists("clean_data/payments_ready_markov.zip"):
    print("   -> Конвертация payments_ready_markov.zip...")
    # Читаем из zip
    trans = pd.read_csv("clean_data/payments_ready_markov.zip", compression='zip',
                        usecols=['user_id', 'category_final', 'brand_id'])
    trans['user_id'] = trans['user_id'].astype('int32')
    trans.to_parquet("clean_data/trans_fast.parquet", index=False)

print("✅ Готово! Теперь обновим пути в first_run.py")