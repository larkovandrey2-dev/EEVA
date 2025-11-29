import pandas as pd
import pickle
import random
import numpy as np


class TwinMatcher:
    def __init__(self, index_path):
        print("🧬 Initializing TwinMatcher Module...")
        try:
            with open(index_path, "rb") as f:
                data = pickle.load(f)
                self.twin_map = data['twin_map']  # (Soc, Reg) -> ActiveID
                self.user_meta = data['user_meta']  # UserID -> {Soc, Reg}
            print(f"✅ TwinMatcher Ready. Indexed Users: {len(self.user_meta):,}")
        except Exception as e:
            print(f"⚠️ Twin Index Error: {e}. Fallback mode active.")
            self.twin_map = {}
            self.user_meta = {}

    def find_twin(self, user_id, active_user_ids):
        """
        Главный метод: Найти активного двойника для любого user_id.
        active_user_ids: список всех активных ID (для рандома).
        Возвращает: (twin_id, match_type)
        """

        # 1. Защита: Если юзера нет в метаданных -> Глобальный Рандом
        if user_id not in self.user_meta:
            return self._get_fallback(active_user_ids), "🎲 Unknown Profile"

        # 2. Получаем метаданные
        meta = self.user_meta[user_id]

        # Функция очистки (чтобы float 5.0 стало int 5, а NaN стало -1)
        def clean_val(val):
            try:
                if val is None or pd.isna(val): return -1
                return int(val)
            except:
                return -1

        soc = clean_val(meta.get('socdem_cluster'))
        reg = clean_val(meta.get('region_id'))

        # --- КАСКАДНЫЙ ПОИСК (LEVELS) ---

        # LEVEL 1: Exact Match (Точное попадание)
        # "Такой же пенсионер из того же города"
        if (soc, reg) in self.twin_map:
            return self.twin_map[(soc, reg)], "⭐ Exact Match"

        # LEVEL 2: SocDem Only (Игнорируем регион)
        # "Такой же пенсионер, но из другого города"
        if soc != -1:
            for (k_soc, k_reg), t_id in self.twin_map.items():
                if k_soc == soc:
                    return t_id, "🧬 SocDem Look-alike"

        # LEVEL 3: Region Only (Игнорируем возраст)
        # "Земляк (кто-то из того же города)"
        if reg != -1:
            for (k_soc, k_reg), t_id in self.twin_map.items():
                if k_reg == reg:
                    return t_id, "🌍 Region Look-alike"

        # LEVEL 4: Safe Fallback (Если ничего не совпало)
        # Берем случайного из активной базы
        return self._get_fallback(active_user_ids), "🛡 Safe Fallback"

    def _get_fallback(self, all_ids):
        # Возвращаем случайный ID из списка
        # all_ids может быть Pandas Index или List
        if hasattr(all_ids, 'tolist'):
            all_ids = all_ids.tolist()
        return random.choice(all_ids)