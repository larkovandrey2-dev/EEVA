import pandas as pd
import glob
import os

print("🚀 [ПЕРЕЗАГРУЗКА] Сбор 20 000 активных пользователей...")

# НАСТРОЙКИ
RAW_DIR = "raw_data"
CLEAN_DIR = "clean_data"
TARGET_SIZE = 20000  # Сколько юзеров нам нужно

os.makedirs(CLEAN_DIR, exist_ok=True)

# =========================================================
# 1. ЧИТАЕМ ВСЕ ТРАНЗАКЦИИ
# =========================================================
print("💰 Сканируем все файлы платежей в raw_data...")
# Ищем файлы, где есть 'pay' в названии
pay_files = glob.glob(f"{RAW_DIR}/*pay*")
chunks = []

for f in pay_files:
    try:
        # Читаем только нужные колонки для скорости
        if f.endswith('.csv'):
            df = pd.read_csv(f)
        else:
            df = pd.read_parquet(f)

        # Нормализуем имена
        if 'amount' in df.columns: df['price'] = df['amount']

        # Оставляем только нужные колонки
        cols = [c for c in df.columns if c in ['user_id', 'price', 'brand_id', 'timestamp']]
        chunks.append(df[cols])
        print(f"  -> Прочитан {os.path.basename(f)}: {len(df)} строк")
    except Exception as e:
        print(f"  ⚠️ Ошибка чтения {f}: {e}")

if not chunks:
    print("❌ Файлы платежей не найдены! Скачай их в папку raw_data.")
    exit()

# Склеиваем всё в одну кучу
full_pay = pd.concat(chunks, ignore_index=True)
print(f"📊 Всего транзакций загружено: {len(full_pay)}")

# =========================================================
# 2. ОТБИРАЕМ ТОП АКТИВНЫХ
# =========================================================
print("🏆 Выбираем самых активных пользователей...")

# Считаем, сколько раз каждый юзер покупал
user_counts = full_pay['user_id'].value_counts()

# Берем тех, у кого хотя бы 2 покупки (чтобы не было случайных)
active_candidates = user_counts[user_counts >= 2]

if len(active_candidates) < TARGET_SIZE:
    print(f"⚠️ Внимание! Найдено всего {len(active_candidates)} активных юзеров.")
    print("💡 СОВЕТ: Скачай еще 2-3 файла платежей в папку raw_data, чтобы набрать 20к.")
    selected_ids = active_candidates.index  # Берем всех, кто есть
else:
    # Берем топ-20000
    selected_ids = active_candidates.head(TARGET_SIZE).index
    print(f"✅ Успешно отобрано топ-{len(selected_ids)} пользователей.")

# Фильтруем транзакции - оставляем только избранных
final_pay = full_pay[full_pay['user_id'].isin(selected_ids)].copy()

# Сохраняем базу транзакций (это заменит payments_step1.csv)
final_pay.to_csv(f"{CLEAN_DIR}/payments_step1.csv", index=False)
print(f"💾 Транзакции сохранены: {CLEAN_DIR}/payments_step1.csv")

# =========================================================
# 3. ПОДТЯГИВАЕМ ПРОФИЛИ (Возраст, Город)
# =========================================================
print("👥 Обновляем список пользователей...")

user_files = glob.glob(f"{RAW_DIR}/*user*.pq") + glob.glob(f"{RAW_DIR}/*user*.csv")
if user_files:
    try:
        # Читаем метаданные всех юзеров
        if user_files[0].endswith('.csv'):
            all_users = pd.read_csv(user_files[0])
        else:
            all_users = pd.read_parquet(user_files[0])

        # Оставляем только наших 20к
        train_users = all_users[all_users['user_id'].isin(selected_ids)].copy()

        # Если каких-то юзеров нет в справочнике (бывает), создаем заглушки
        found_ids = set(train_users['user_id'])
        missing_ids = set(selected_ids) - found_ids

        if missing_ids:
            print(f"⚠️ {len(missing_ids)} юзеров нет в справочнике users.pq, добавляем пустышки.")
            missing_df = pd.DataFrame({'user_id': list(missing_ids)})
            train_users = pd.concat([train_users, missing_df])

        train_users.to_csv(f"{CLEAN_DIR}/train_users_10k.csv", index=False)  # Название оставим старое для совместимости
        print(f"💾 Профили сохранены: {CLEAN_DIR}/train_users_10k.csv")

    except Exception as e:
        print(f"Ошибка чтения users: {e}")
else:
    print("❌ Файл users.pq не найден! Создаю заглушку.")
    pd.DataFrame({'user_id': list(selected_ids)}).to_csv(f"{CLEAN_DIR}/train_users_10k.csv", index=False)

print("\n🎉 ГОТОВО! Теперь запускай остальные шаги пайплайна.")