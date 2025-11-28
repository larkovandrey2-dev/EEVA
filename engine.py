import pandas as pd
import numpy as np
from products import PSB_PRODUCTS, TREND_MAPPING, CONTEXT_OFFERS

class RecommendationEngine:
    def __init__(self, user_file):
        print("Initializing Recommendation Engine V1.0")
        self.users = pd.read_csv(user_file).set_index("user_id")
        print("Launched")
    def _get_segment_info(self, cluster_id):
        base_mult = 120.0
        mapping = {
            2: ("VIP", "💎 VIP / High-Spender", base_mult * 0.8),
            5: ("YOUTH", "🌙 Young & Active", base_mult * 1.2),
            0: ("YOUTH", "🌙 Young & Active", base_mult * 1.2),
            4: ("SAVER", "🛡 Rational Saver", base_mult * 1.0),
            6: ("MIDDLE", "💼 Upper Mass (Gold)", base_mult * 1.0),
            1: ("MIDDLE", "⚠️ Credit Risk", base_mult * 1.1),
            3: ("MIDDLE", "💄 Lifestyle / Beauty", base_mult * 1.0)
        }
        return mapping.get(cluster_id, ("MIDDLE", "🛒 Mass Market", base_mult))

    def recommend(self, user_id):
        try:
            if user_id not in self.users.index:
                return None

            user_row = self.users.loc[user_id]
            seg_tag, seg_name, mult = self._get_segment_info(user_row['cluster_id'])
            proj_spend = user_row['total_spend'] * mult
            product = PSB_PRODUCTS.get(seg_tag, PSB_PRODUCTS["MIDDLE"])
            result = {
            "user_id": user_id,
            "segment_name": seg_name,
            "cluster_id": int(user_row['cluster_id']),
            "stats": {
                    "real_48h_spend": int(user_row['total_spend'] * mult / 15),
                    "projected_month_spend": int(proj_spend)
                },
            "product": product,
            "reason": f"Продукт подобран для профиля: {seg_name}"
            }

            return result
        except Exception as e:
            print("Recommendation engine error: ", e)
            return None

    def get_llm_prompt(self, data):
        if not data: return ""
        return f"""
        Ты ассистент банка ПСБ.
        Клиент: {data['segment_name']} (Тратит ~{data['stats']['projected_month_spend']} руб/мес).
        Предложи продукт: "{data['product']['name']}" ({data['product']['desc']}).
        Сделай это коротко и вежливо.
        """