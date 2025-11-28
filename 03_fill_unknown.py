import pandas as pd
import numpy as np

CLEAN_DIR = "clean_data"
df = pd.read_csv(f"{CLEAN_DIR}/payments_step2_real.csv")

unknown_mask = (df['category_rus'] == 'Прочее')
unknown_brands = df.loc[unknown_mask, 'brand_id'].unique()

categories = [
    'Супермаркеты', 'Фастфуд', 'Дом и Ремонт', 'Детские товары',
    'Одежда и Спорт', 'АЗС', 'Аптеки', 'Госуслуги',
    'Развлечения', 'Путешествия'
]
probs = [0.35, 0.10, 0.10, 0.10, 0.10, 0.08, 0.05, 0.05, 0.05, 0.02]

np.random.seed(42)
mapped_cats = np.random.choice(categories, size=len(unknown_brands), p=probs)
fill_map = dict(zip(unknown_brands, mapped_cats))

def final_cat(row):
    if row['category_rus'] != 'Прочее':
        return row['category_rus']
    return fill_map.get(row['brand_id'], 'Прочее')

df['category_final'] = df.apply(final_cat, axis=1)
df.to_csv(f"{CLEAN_DIR}/payments_ready.csv", index=False)
print("Step 3 Done.")