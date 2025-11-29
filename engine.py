import pandas as pd
import json
from products import PSB_PRODUCTS, PREDICTION_OFFERS, TREND_MAPPING
from twin_matcher import TwinMatcher


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Loading EEVA Engine...")

        # 1. Данные (Активные юзеры)
        self.users = pd.read_csv(users_file).set_index('user_id')
        # Транзакции (Для Маркова)
        self.trans = pd.read_csv(trans_file, usecols=['user_id', 'category_final', 'brand_id'])

        # 2. Модуль Двойников (Smart Look-alike)
        self.matcher = TwinMatcher("clean_data/twin_index.pkl")

        # 3. Марков (Предсказания)
        try:
            with open("markov_chains.json", "r", encoding='utf-8') as f:
                self.markov = json.load(f)
            print("Markov Model: CONNECTED")
        except:
            self.markov = {}

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

    def _predict_next(self, user_id):
        user_tx = self.trans[self.trans['user_id'] == user_id]
        if user_tx.empty: return None, 0, None, []

        last_action_raw = user_tx.iloc[-1]['category_final']
        recent_brands = user_tx['brand_id'].unique()[-3:].tolist()

        pred_data = self.markov.get(last_action_raw)
        if pred_data:
            # Маппинг предсказания в Тренд ПСБ
            pred_trend = TREND_MAPPING.get(pred_data['prediction'], pred_data['prediction'])
            return pred_trend, pred_data['probability'], last_action_raw, recent_brands
        return None, 0, last_action_raw, recent_brands

    def recommend(self, user_id, time_of_day="Day"):
        target_id = user_id
        is_twin = False
        match_type = "Real Data"

        # Если юзера нет в активной базе -> Ищем двойника
        if user_id not in self.users.index:
            is_twin = True
            # Передаем ID и список доступных активных юзеров для фолбэка
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        try:
            # Дальше работаем с target_id (Это или сам юзер, или его двойник)
            user_row = self.users.loc[target_id]
            seg_tag, seg_name, mult = self._get_segment_info(user_row['cluster_id'])
            proj_spend = int(user_row['total_spend'] * mult)

            # Предсказания строим по истории target_id
            pred_trend, prob, last_cat, brands = self._predict_next(target_id)

            # Основной продукт (Стратегия)
            primary_prod = PSB_PRODUCTS[seg_tag]["default"]
            primary_reason = f"Базовый продукт для профиля {seg_name}"

            # Дополнительный продукт (Тактика)
            secondary_prod = None
            secondary_reason = ""
            insight_type = ""

            # Вариант А: Марков
            if pred_trend and prob > 0.15 and pred_trend in PREDICTION_OFFERS:
                secondary_prod = PREDICTION_OFFERS[pred_trend]
                secondary_reason = f"После '{last_cat}' часто возникает потребность: '{pred_trend}' ({int(prob * 100)}%)"
                insight_type = "🔮 AI Prediction"

            # Вариант Б: Ночь
            elif time_of_day == "Night" and "night" in PSB_PRODUCTS[seg_tag]:
                secondary_prod = PSB_PRODUCTS[seg_tag]["night"]
                secondary_reason = "Клиент активен в ночное время"
                insight_type = "🌙 Context Rule"

            # Вариант В: Инвестиции
            elif "invest" in PSB_PRODUCTS[seg_tag]:
                secondary_prod = PSB_PRODUCTS[seg_tag]["invest"]
                secondary_reason = "Предложение для накопления капитала"
                insight_type = "💰 Smart Upsell"

            # Фолбэк (СБП)
            else:
                secondary_prod = {"name": "СБП", "desc": "Переводы без комиссии."}
                secondary_reason = "Полезный сервис"
                insight_type = "⚙️ Service"

            return {
                "user_id": user_id,
                "is_twin": is_twin,
                "match_type": match_type,  # Тип совпадения (Real / SocDem / Random)
                "segment_name": seg_name,
                "stats": {"projected_month_spend": proj_spend},
                "recent_brands": brands,
                "primary": {
                    "type": "Strategic Offer",
                    "product": primary_prod,
                    "reason": primary_reason
                },
                "secondary": {
                    "type": insight_type,
                    "product": secondary_prod,
                    "reason": secondary_reason
                }
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def get_llm_prompt(self, data):
        if not data: return ""
        sec = data['secondary']
        return f"""
        Ты ассистент банка ПСБ. Клиент: {data['segment_name']} (Прогноз: {data['stats']['projected_month_spend']} ₽).
        Предложи: "{data['primary']['product']['name']}" И "{sec['product']['name']}".
        Аргумент: {sec['reason']}.
        """