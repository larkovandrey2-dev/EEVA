import pandas as pd
import json
import os

FILE_PATH = "clean_data/payments_ready_markov.csv"
OUTPUT_FILE = "markov_chains.json"

print("Запуск построения Цепей Маркова...")

try:
    df = pd.read_csv(FILE_PATH)
    print(f"   -> Загружено {len(df)} транзакций.")
    if 'category_final' not in df.columns:
        print("ОШИБКА: В файле нет колонки 'category_final'.")
        print("Сначала нужно восстановить категории по brand_id (Step 2).")
        exit()

except Exception as e:
    print(f"Ошибка чтения файла: {e}")
    exit()


if 'timestamp' in df.columns:
    df = df.sort_values(['user_id', 'timestamp'])
else:
    df = df.sort_values(['user_id'])

df['next_cat'] = df.groupby('user_id')['category_final'].shift(-1)


valid_transitions = df.dropna(subset=['next_cat'])
valid_transitions = valid_transitions[valid_transitions['category_final'] != valid_transitions['next_cat']]

print(f"Проанализировано {len(valid_transitions)} переходов.")


matrix = pd.crosstab(valid_transitions['category_final'], valid_transitions['next_cat'], normalize='index')


markov_dict = {}

THRESHOLD = 0.15

for current_cat in matrix.index:
    best_next = matrix.loc[current_cat].sort_values(ascending=False)

    if not best_next.empty:
        top_cat = best_next.index[0]
        prob = best_next.values[0]
        if prob >= THRESHOLD:
            markov_dict[current_cat] = {
                "prediction": top_cat,
                "probability": round(prob, 2)
            }
            print(f"{current_cat} -> {top_cat} ({int(prob * 100)}%)")

with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
    json.dump(markov_dict, f, ensure_ascii=False, indent=4)

print(f"Матрица Маркова сохранена в {OUTPUT_FILE}")
