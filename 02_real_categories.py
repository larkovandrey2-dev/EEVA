import pandas as pd
import os

CLEAN_DIR = "clean_data"
RAW_DIR = "raw_data"
pay = pd.read_csv(f"{CLEAN_DIR}/payments_step1.csv")

# Get categories from items
brand_map = {}
items_path = f"{RAW_DIR}/items.pq"

if os.path.exists(items_path):
    try:
        items = pd.read_parquet(items_path, columns=['brand_id', 'category'])
        brand_map_df = items.groupby('brand_id')['category'].agg(
            lambda x: x.mode()[0] if not x.mode().empty else "Unknown"
        ).reset_index()
        brand_map = dict(zip(brand_map_df['brand_id'], brand_map_df['category']))
    except:
        pass

pay['real_category'] = pay['brand_id'].map(brand_map).fillna("Unknown")

translation = {
    'Foodstuffs and Beverages': 'Супермаркеты',
    'Cosmetics, Personal Care, and Health Maintenance Products': 'Красота',
    'Home Improvement and Countryside Retreat Essentials': 'Дом и Ремонт',
    "Children's Products and Childcare Items": 'Детские товары',
    'Outerwear, Casual Apparel, and Specialized Workwear': 'Одежда и Спорт',
    'Cleaning Supplies and Everyday Household Items': 'Дом',
    'Pet Supplies: Food, Accessories, and Grooming Products': 'Животные',
    'Electronics': 'Электроника',
    'Unknown': 'Прочее'
}

pay['category_rus'] = pay['real_category'].apply(lambda x: translation.get(x, "Прочее"))
pay.to_csv(f"{CLEAN_DIR}/payments_step2_real.csv", index=False)
print("Step 2 Done.")