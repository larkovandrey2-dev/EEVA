import pandas as pd
import pickle
import os
import glob
import numpy as np

print("Генерация Индекса с объединением таблиц...")

# --- ПУТИ К ФАЙЛАМ ---
# 1. Твои активные юзеры (с поведенческими кластерами)
ACTIVE_FILE = "clean_data/users_clustered.csv"

# 2. Файл с метаданными (SocDem + Region)
# Сначала ищем нарезанные куски (это быстрее)
CHUNKS_DIR = "clean_data/users_meta_chunks"
# Если кусков нет, берем исходный файл (проверь название!)
FULL_META_FILE = "raw_data/all_users_meta.csv"
# Если и этого нет, пробуем тот, про который ты говорил (train_users_10k)
FALLBACK_META = "clean_data/train_users_10k.csv"

OUTPUT_FILE = "clean_data/twin_index.pkl"

# --- 1. ЗАГРУЗКА АКТИВНЫХ (BEHAVIOR) ---
try:
    print(f"   -> Читаем активных (поведение): {ACTIVE_FILE}")
    df_active = pd.read_csv(ACTIVE_FILE)

    # Нам нужны отсюда только ID и Траты (чтобы выбрать медиану)
    # Кластеры поведения (0-6) здесь не нужны для индекса, они и так в движке
    df_active = df_active[['user_id', 'total_spend']]

    # Приводим к int
    df_active['user_id'] = df_active['user_id'].astype(int)

except Exception as e:
    print(f"❌ Ошибка чтения active file: {e}")
    exit()

# --- 2. ЗАГРУЗКА МЕТАДАННЫХ (SOCDEM) ---
print("   -> Читаем метаданные (SocDem + Region)...")
df_meta = None

# Вариант А: Куски Parquet (самый быстрый)
if os.path.exists(CHUNKS_DIR):
    files = glob.glob(f"{CHUNKS_DIR}/part_*.parquet")
    if files:
        print(f"      Найдено {len(files)} кусков Parquet.")
        df_list = [pd.read_parquet(f) for f in files]
        df_meta = pd.concat(df_list, ignore_index=True)

# Вариант Б: Полный CSV
if df_meta is None and os.path.exists(FULL_META_FILE):
    print(f"      Читаем полный CSV: {FULL_META_FILE}")
    df_meta = pd.read_csv(FULL_META_FILE, usecols=['user_id', 'socdem_cluster', 'region'])

# Вариант В: Твой файл train_users
if df_meta is None and os.path.exists(FALLBACK_META):
    print(f"      Читаем fallback CSV: {FALLBACK_META}")
    df_meta = pd.read_csv(FALLBACK_META)
    # Оставляем только нужное, чтобы не было конфликтов
    df_meta = df_meta[['user_id', 'socdem_cluster', 'region']]

if df_meta is None:
    print("❌ Не найден ни один файл с метаданными (socdem)!")
    exit()

# Чистка типов
print("   -> Очистка типов данных...")
df_meta['user_id'] = df_meta['user_id'].astype(int)


def clean_int(x):
    try:
        return int(x) if pd.notna(x) else -1
    except:
        return -1


df_meta['socdem_cluster'] = df_meta['socdem_cluster'].apply(clean_int)
df_meta['region'] = df_meta['region'].apply(clean_int)

# --- 3. MERGE: СОЕДИНЯЕМ АКТИВНЫХ С ИХ СОЦДЕМОМ ---
print("   -> Объединяем Активных с Метаданными (Inner Join)...")

# Оставляем в метаданных только тех, кто есть в активных (для скорости)
# (Но полный df_meta нам еще понадобится для сохранения индекса всех юзеров!)
active_ids_set = set(df_active['user_id'])
relevant_meta = df_meta[df_meta['user_id'].isin(active_ids_set)]

# Склеиваем
# Теперь у df_joined есть: user_id, total_spend, socdem_cluster, region
df_joined = df_active.merge(relevant_meta, on='user_id', how='inner')

print(f"   -> Итог: {len(df_joined)} активных пользователей с полными данными.")

# --- 4. СТРОИМ КАРТУ ЭТАЛОНОВ (MEDIAN) ---
twin_map = {}
grouped = df_joined.groupby(['socdem_cluster', 'region'])

print("   -> Вычисляем медианных двойников...")
for (soc, reg), group in grouped:
    # Сортируем по тратам
    sorted_group = group.sort_values('total_spend')
    # Берем серединку
    mid_idx = len(sorted_group) // 2
    best_twin = sorted_group.iloc[mid_idx]['user_id']

    twin_map[(int(soc), int(reg))] = int(best_twin)

print(f"   -> Найдено {len(twin_map)} уникальных групп (комбинаций).")

# --- 5. СОХРАНЯЕМ ИНДЕКС ---
print("   -> Индексируем базу всех пользователей...")
# Словарь для быстрого поиска: ID -> {soc, reg}
user_meta_dict = df_meta.set_index('user_id')[['socdem_cluster', 'region']].to_dict('index')

data = {
    "twin_map": twin_map,  # Словарь: (soc, reg) -> Active_ID
    "user_meta": user_meta_dict  # Словарь: Any_ID -> {soc, reg}
}

with open(OUTPUT_FILE, "wb") as f:
    pickle.dump(data, f)

print(f"Индекс готов: {OUTPUT_FILE}")