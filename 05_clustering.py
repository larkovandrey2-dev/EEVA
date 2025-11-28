import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# НАСТРОЙКИ
CLEAN_DIR = "clean_data"
INPUT_FILE = f"{CLEAN_DIR}/master_features_final.csv"
MODEL_FILE = f"{CLEAN_DIR}/kmeans_model.pkl"
SCALER_FILE = f"{CLEAN_DIR}/scaler.pkl"
CLUSTERED_DATA = f"{CLEAN_DIR}/users_clustered.csv"

print("🧠 [ВЕТКА 1] Запуск кластеризации (Lifestyle)...")

# 1. Загружаем подготовленные фичи
df = pd.read_csv(INPUT_FILE)
df = df.fillna(0) # На всякий случай

# 2. Выбираем колонки для обучения
# Исключаем ID и абсолютные суммы (чтобы не делить чисто по богатству),
# фокусируемся на ПОВЕДЕНИИ (доли трат, время, частота)
feature_cols = [
    'tx_count', 'avg_check', 'saving_rate',
    'night_share', 'weekend_share'
]
# Добавляем все колонки, начинающиеся на share_ (доли категорий)
share_cols = [c for c in df.columns if c.startswith('share_')]
feature_cols.extend(share_cols)

print(f"Используем {len(feature_cols)} фичей для кластеризации.")

# 3. Нормализация данных (Scikit-learn не любит разный масштаб)
X = df[feature_cols]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. K-Means (Ставим 7 кластеров - оптимально для демо: Студент, Семья, Богач и т.д.)
kmeans = KMeans(n_clusters=7, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_scaled)

# 5. Сохраняем результаты
df['cluster_id'] = clusters
df.to_csv(CLUSTERED_DATA, index=False)

with open(MODEL_FILE, 'wb') as f:
    pickle.dump(kmeans, f)
with open(SCALER_FILE, 'wb') as f:
    pickle.dump(scaler, f)

print(f"\nГотово! Данные с кластерами: {CLUSTERED_DATA}")
def get_segment_name(row):
    cid = row['cluster_id']
    if cid == 6:
        return "💎 VIP "
    elif cid in [1, 3]:
        return "💼 Средний класс"
    else:
        if row['share_Фастфуд'] > 0.15:
            return "🍔 Студенты"
        return "🏠 Эконом / Семья"

df['Segment_Name'] = df.apply(get_segment_name, axis=1)

print("\n📊 ИТОГОВАЯ СЕГМЕНТАЦИЯ ДЛЯ ПРЕЗЕНТАЦИИ:")
report = df.groupby('Segment_Name')[['total_spend', 'night_share', 'share_Фастфуд', 'share_Детские товары']].mean()
print(report)