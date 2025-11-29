import pickle
import pandas as pd
import random
import numpy as np

print("🕵️‍♂️ Запуск инспекции Индекса Двойников...")

INDEX_FILE = "clean_data/twin_index.pkl"
ACTIVE_FILE = "clean_data/users_clustered.csv"

# 1. ЗАГРУЗКА ИНДЕКСА
try:
    with open(INDEX_FILE, "rb") as f:
        data = pickle.load(f)

    twin_map = data['twin_map']  # (Soc, Reg) -> Twin_ID
    user_meta = data['user_meta']  # User_ID -> {Soc, Reg}

    print(f"✅ Индекс загружен успешно.")
    print(f"   📊 Всего пользователей в базе (Meta): {len(user_meta):,}")
    print(f"   🧩 Уникальных групп (SocDem + Region): {len(twin_map)}")

    # Проверка на разнообразие
    unique_twins = set(twin_map.values())
    print(f"   👥 Количество уникальных 'Двойников': {len(unique_twins)}")

    if len(unique_twins) < 5:
        print("⚠️ ВНИМАНИЕ: Очень мало уникальных двойников! Возможно, что-то не так с группировкой.")
    else:
        print("   👍 Разнообразие в норме. Система не предлагает одного и того же всем.")

except Exception as e:
    print(f"❌ Ошибка чтения pickle: {e}")
    exit()

# 2. ПОДГРУЗКА ДАННЫХ О ДВОЙНИКАХ (Чтобы понять, кто они)
try:
    df_active = pd.read_csv(ACTIVE_FILE).set_index('user_id')
    print(f"✅ Активные профили подгружены: {len(df_active)}")
except:
    print("⚠️ Не могу загрузить users_clustered.csv, детальной инфы не будет.")
    df_active = pd.DataFrame()

# 3. СИМУЛЯЦИЯ (Тест на случайных людях)
print("\n🎲 ТЕСТ-ДРАЙВ: Берем 10 случайных 'холодных' юзеров...")

all_ids = list(user_meta.keys())
# Берем 10 случайных ID для надежности
sample_ids = random.sample(all_ids, 10)

print(f"{'USER ID':<12} | {'SOCDEM':<8} | {'REGION':<8} | {'-> TWIN ID':<12} | {'TWIN TYPE'}")
print("-" * 80)

for uid in sample_ids:
    # 1. Достаем мету
    meta = user_meta[uid]
    soc = meta.get('socdem_cluster')
    reg = meta.get('region_id')


    # --- БЕЗОПАСНОЕ ПРЕОБРАЗОВАНИЕ В СТРОКУ (FIX) ---
    # Проверяем на None и NaN (float('nan'))
    def safe_str(val):
        if val is None: return "NaN"
        try:
            if np.isnan(val): return "NaN"
        except:
            pass
        # Если это число, убираем .0 (для красоты)
        return str(int(val)) if isinstance(val, float) and val.is_integer() else str(val)


    soc_str = safe_str(soc)
    reg_str = safe_str(reg)
    # -----------------------------------------------

    # 2. Ищем двойника
    # Ключ должен совпадать с тем, как сохраняли в pickle (обычно float или int)
    key = (soc, reg)
    twin_id = twin_map.get(key, "Not Found")

    # 3. Узнаем, кто этот двойник (если есть база активных)
    twin_info = "Unknown"

    if twin_id != "Not Found" and not df_active.empty:
        # Проверяем, есть ли такой twin_id в базе активных
        if twin_id in df_active.index:
            try:
                cluster = df_active.loc[twin_id]['cluster_id']
                spend = df_active.loc[twin_id]['total_spend']

                # Простая расшифровка для наглядности
                if cluster == 2:
                    twin_info = f"VIP ({spend:.0f})"
                elif cluster in [5, 0]:
                    twin_info = f"Youth ({spend:.0f})"
                elif cluster == 4:
                    twin_info = f"Saver ({spend:.0f})"
                else:
                    twin_info = f"Middle ({spend:.0f})"
            except:
                twin_info = "Error"
        else:
            twin_info = "Not in Active"

    # Печатаем
    print(f"{str(uid):<12} | {soc_str:<8} | {reg_str:<8} | {str(twin_id):<12} | {twin_info}")

print("-" * 80)
print("💡 ЛЕГЕНДА: Youth = Молодежь, Middle = Зарплатники, Saver = Сберегатели, VIP = Богатые.")
print("✅ Если колонка TWIN TYPE разнообразная — твой Smart Look-alike работает!")