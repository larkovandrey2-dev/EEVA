# twin_matcher.py
import pandas as pd
import pickle
import random
import numpy as np

class TwinMatcher:
    def __init__(self, index_path):
        # Убираем print("Loading..."), чтобы не спамило при кэшировании
        try:
            with open(index_path, "rb") as f:
                data = pickle.load(f)
                self.twin_map = data['twin_map']
                self.user_meta = data['user_meta']
            # print(f"✅ TwinMatcher Ready.")
        except Exception as e:
            print(f"⚠️ Twin Index Error: {e}")
            self.twin_map = {}
            self.user_meta = {}

    # Метод find_twin остается без изменений
    def find_twin(self, user_id, active_user_ids):
        if user_id not in self.user_meta:
            return self._get_fallback(active_user_ids), "🎲 Unknown Profile"

        meta = self.user_meta[user_id]

        def clean_val(val):
            try:
                if val is None or pd.isna(val): return -1
                return int(val)
            except:
                return -1

        soc = clean_val(meta.get('socdem_cluster'))
        reg = clean_val(meta.get('region_id'))

        if (soc, reg) in self.twin_map:
            return self.twin_map[(soc, reg)], "⭐ Exact Match"

        if soc != -1:
            for (k_soc, k_reg), t_id in self.twin_map.items():
                if k_soc == soc:
                    return t_id, "🧬 SocDem Look-alike"

        if reg != -1:
            for (k_soc, k_reg), t_id in self.twin_map.items():
                if k_reg == reg:
                    return t_id, "🌍 Region Look-alike"

        return self._get_fallback(active_user_ids), "🛡 Safe Fallback"

    def _get_fallback(self, all_ids):
        if hasattr(all_ids, 'tolist'):
            all_ids = all_ids.tolist()
        return random.choice(all_ids)