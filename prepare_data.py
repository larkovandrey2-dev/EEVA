import pandas as pd
import numpy as np
import os

print("🚀 [STEP: PREPARE] Подготовка данных с Умным Заполнением (Smart Augmentation)...")

# --- НАСТРОЙКИ ---
CLEAN_DIR = "clean_data"
RAW_DIR = "raw_data"

# Ищем лучший файл транзакций
PAY_FILE = f"{CLEAN_DIR}/payments_repaired.csv"
if not os.path.exists(PAY_FILE):
    PAY_FILE = f"{CLEAN_DIR}/payments_step1.csv"

# Файл с кластерами (обязателен для умного заполнения)
CLUSTERS_FILE = f"{CLEAN_DIR}/users_clustered.csv"

# --- 1. ЗАГРУЗКА ДАННЫХ ---
print(f"   -> Читаем транзакции: {PAY_FILE}")
try:
    pay = pd.read_csv(PAY_FILE)
except Exception as e:
    print(f"Ошибка: {e}")
    exit()

print(f"Читаем кластеры: {CLUSTERS_FILE}")
try:
    users = pd.read_csv(CLUSTERS_FILE)
    # Оставляем только нужное
    users = users[['user_id', 'cluster_id']]
except Exception as e:
    print(f"⚠️ Файл кластеров не найден! Умное заполнение будет работать как обычный рандом.")
    users = pd.DataFrame(columns=['user_id', 'cluster_id'])

# Объединяем транзакции с кластерами
pay = pay.merge(users, on='user_id', how='left')
# Если кластера нет (юзер выпал), ставим -1
pay['cluster_id'] = pay['cluster_id'].fillna(-1).astype(int)

# --- 2. РАБОТА С БРЕНДАМИ (Items.pq) ---
# Приводим brand_id к строке
if 'brand_id' in pay.columns:
    pay['brand_id'] = pay['brand_id'].fillna(-1).astype(str).str.replace('.0', '', regex=False)

brand_map = {}
items_path = f"{RAW_DIR}/items.pq"

if os.path.exists(items_path):
    try:
        print("   -> Подгружаем справочник брендов...")
        items = pd.read_parquet(items_path, columns=['brand_id', 'category'])
        items['brand_id'] = items['brand_id'].astype(str)

        # Делаем словарь (быстрый маппинг)
        # Если дубли, берем первый попавшийся
        brand_map = dict(zip(items['brand_id'], items['category']))
    except:
        pass

# Мапим реальные категории
pay['real_category'] = pay['brand_id'].map(brand_map).fillna("Unknown")

# --- 3. ПЕРЕВОД НА РУССКИЙ ---
translation = {
    'Foodstuffs and Beverages': 'Супермаркеты',
    'Cosmetics, Personal Care, and Health Maintenance Products': 'Красота',
    'Home Improvement and Countryside Retreat Essentials': 'Дом и Ремонт',
    "Children's Products and Childcare Items": 'Детские товары',
    'Outerwear, Casual Apparel, and Specialized Workwear': 'Одежда и Спорт',
    'Cleaning Supplies and Everyday Household Items': 'Дом',
    'Pet Supplies: Food, Accessories, and Grooming Products': 'Животные',
    'Electronics': 'Электроника',
    'Travel': 'Путешествия',
    'Entertainment': 'Развлечения',
    'Dining': 'Фастфуд',
    'Unknown': 'Прочее'
}
pay['category_final'] = pay['real_category'].apply(lambda x: translation.get(x, "Прочее"))

# --- 4. SMART FILLING (Синтетическое обогащение по профилю) ---
print("   🧠 Запускаем генерацию категорий на основе Кластеров...")


# Функция-помощник для заполнения по маске
def fill_by_cluster(df, cluster_ids, categories, probs):
    # Выбираем строки: (Кластер совпал) И (Категория неизвестна)
    mask = (df['cluster_id'].isin(cluster_ids)) & (df['category_final'] == 'Прочее')
    count = mask.sum()

    if count > 0:
        # Генерируем случайные категории с учетом весов
        # np.random.seed(42) # Можно включить для воспроизводимости
        fill_values = np.random.choice(categories, size=count, p=probs)
        df.loc[mask, 'category_final'] = fill_values
        print(f"      -> Заполнено {count} строк для кластеров {cluster_ids}")


# 1. МОЛОДЕЖЬ (Clusters 5, 0) -> Фастфуд, Развлечения, Такси
fill_by_cluster(
    pay, [5, 0],
    categories=['Фастфуд', 'Развлечения', 'Супермаркеты', 'Такси', 'Красота'],
    probs=[0.35, 0.25, 0.20, 0.15, 0.05]
)

# 2. VIP (Cluster 2) -> Путешествия, Рестораны, АЗС
fill_by_cluster(
    pay, [2],
    categories=['Путешествия', 'АЗС', 'Супермаркеты', 'Фастфуд', 'Развлечения'],
    probs=[0.30, 0.20, 0.20, 0.15, 0.15]
)

# 3. СБЕРЕГАТЕЛИ / СЕМЬЯ (Cluster 4) -> Дом, Аптеки, Супермаркеты
fill_by_cluster(
    pay, [4],
    categories=['Супермаркеты', 'Аптеки', 'Дом и Ремонт', 'Детские товары'],
    probs=[0.50, 0.20, 0.20, 0.10]
)

# 4. СРЕДНИЙ КЛАСС (Остальные: 1, 3, 6, -1) -> Сбалансированно
rest_clusters = [1, 3, 6, -1]
fill_by_cluster(
    pay, rest_clusters,
    categories=['Супермаркеты', 'АЗС', 'Дом и Ремонт', 'Фастфуд', 'Одежда и Спорт'],
    probs=[0.40, 0.15, 0.15, 0.15, 0.15]
)

#5. ФИНАЛ
OUT_FILE = f"{CLEAN_DIR}/payments_ready_markov.csv"
pay.to_csv(OUT_FILE, index=False)

print(f"УСПЕХ! Данные готовы.")
print(f"Сохранено в: {OUT_FILE}")
