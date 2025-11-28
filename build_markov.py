import pandas as pd
import json
import os

# 1. НАСТРОЙКИ
# Укажи здесь файл, где есть колонка 'category_final' (Русские названия)
# Если у тебя файл восстановленный и там только brand_id, сначала примени маппинг!
FILE_PATH = "clean_data/payments_ready_markov.csv"
OUTPUT_FILE = "markov_chains.json"

print("🔗 Запуск построения Цепей Маркова...")

# 2. ЗАГРУЗКА
try:
    df = pd.read_csv(FILE_PATH)
    print(f"   -> Загружено {len(df)} транзакций.")

    # Проверка на наличие колонки категорий
    if 'category_final' not in df.columns:
        print("❌ ОШИБКА: В файле нет колонки 'category_final'.")
        print("   Сначала нужно восстановить категории по brand_id (Step 2).")
        exit()

except Exception as e:
    print(f"❌ Ошибка чтения файла: {e}")
    exit()

# 3. ПОДГОТОВКА ДАННЫХ
# Сортируем, чтобы восстановить последовательность событий
# Если есть timestamp, сортируем по нему. Если нет - надеемся на порядок строк.
if 'timestamp' in df.columns:
    df = df.sort_values(['user_id', 'timestamp'])
else:
    df = df.sort_values(['user_id'])  # Просто по порядку строк

# Сдвигаем колонку, чтобы получить пары (Текущая -> Следующая)
df['next_cat'] = df.groupby('user_id')['category_final'].shift(-1)

# Убираем строки, где нет следующей покупки (конец истории юзера)
# И убираем "скучные" переходы (Супермаркет -> Супермаркет), это зашумляет
valid_transitions = df.dropna(subset=['next_cat'])
valid_transitions = valid_transitions[valid_transitions['category_final'] != valid_transitions['next_cat']]

print(f"   -> Проанализировано {len(valid_transitions)} переходов.")

# 4. МАТЕМАТИКА (Crosstab)
# Строим матрицу вероятностей
matrix = pd.crosstab(valid_transitions['category_final'], valid_transitions['next_cat'], normalize='index')

# 5. КОНВЕРТАЦИЯ В JSON
markov_dict = {}

# Порог вероятности (чтобы не предлагать бред с вероятностью 1%)
THRESHOLD = 0.15

for current_cat in matrix.index:
    # Ищем самую вероятную следующую категорию
    best_next = matrix.loc[current_cat].sort_values(ascending=False)

    if not best_next.empty:
        top_cat = best_next.index[0]
        prob = best_next.values[0]

        # Если вероятность достойная - сохраняем
        if prob >= THRESHOLD:
            markov_dict[current_cat] = {
                "prediction": top_cat,
                "probability": round(prob, 2)
            }
            print(f"      📍 {current_cat} -> {top_cat} ({int(prob * 100)}%)")

# 6. СОХРАНЕНИЕ
with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
    json.dump(markov_dict, f, ensure_ascii=False, indent=4)

print(f"\n✅ Матрица Маркова сохранена в {OUTPUT_FILE}")
print("   Теперь engine.py сможет предсказывать будущее!")