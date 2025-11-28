import json

import pandas as pd
import numpy as np
from products import PSB_PRODUCTS, PREDICTION_OFFERS, TREND_MAPPING

class RecommendationEngine:
    def __init__(self, user_file, trans_file):
        print("Initializing Recommendation Engine V1.0")
        self.users = pd.read_csv(user_file).set_index("user_id")
        self.trans = pd.read_csv("clean_data/payments_ready_markov.zip", compression='zip', usecols=['user_id', 'category_final', 'brand_id'])

        try:
            with open("markov_chains.json", "r", encoding='utf-8') as f:
                self.markov = json.load(f)
            print("Markov chains connected")
        except FileNotFoundError:
            print("Markov file not found. Branch 3 disabled.")
            self.markov = {}
        print("Launched")

    def _get_segment_info(self, cluster_id):
        # Множитель x120 для красивых цифр (компенсация короткого периода)
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
        """Ветка 3: Марков + Маппинг в продукты ПСБ"""
        user_tx = self.trans[self.trans['user_id'] == user_id]
        if user_tx.empty: return None, 0, None, []

        # Последнее действие пользователя
        last_action_raw = user_tx.iloc[-1]['category_final']
        recent_brands = user_tx['brand_id'].unique()[-3:].tolist()

        # Предсказание Маркова (например: "Дом и Ремонт")
        pred_data = self.markov.get(last_action_raw)

        if pred_data:
            pred_cat_raw = pred_data['prediction']  # "Дом и Ремонт"
            prob = pred_data['probability']

            # ВАЖНО: Превращаем категорию в Тренд ПСБ (через TREND_MAPPING)
            # "Дом и Ремонт" -> "Ремонт"
            # Если нет в маппинге, оставляем как есть
            pred_trend = TREND_MAPPING.get(pred_cat_raw, pred_cat_raw)

            return pred_trend, prob, last_action_raw, recent_brands

        return None, 0, last_action_raw, recent_brands

    def recommend(self, user_id, time_of_day="Day"):
        """
        ОРКЕСТРАТОР
        """
        if user_id not in self.users.index: return None

        # 1. ДАННЫЕ ЮЗЕРА
        user_row = self.users.loc[user_id]
        seg_tag, seg_name, mult = self._get_segment_info(user_row['cluster_id'])
        proj_spend = int(user_row['total_spend'] * mult)

        # 2. МАРКОВ (Паттерны)
        # Получаем уже нормализованный тренд (например, "Ремонт" или "Спорт и Красота")
        pred_trend, prob, last_cat, brands = self._predict_next(user_id)

        # --- СБОРКА 1: ОСНОВНОЕ ПРЕДЛОЖЕНИЕ (Стратегия) ---
        primary_prod = PSB_PRODUCTS[seg_tag]["default"]
        primary_reason = f"Базовый продукт для профиля {seg_name}"

        # --- СБОРКА 2: ДОПОЛНИТЕЛЬНОЕ ПРЕДЛОЖЕНИЕ (Тактика) ---
        secondary_prod = None
        secondary_reason = ""
        insight_type = ""

        # Вариант А: Есть сильный сигнал от Маркова (и есть продукт ПСБ под этот тренд)
        # Ищем предсказанный тренд в PREDICTION_OFFERS
        if pred_trend and prob > 0.15 and pred_trend in PREDICTION_OFFERS:
            secondary_prod = PREDICTION_OFFERS[pred_trend]
            secondary_reason = f"После '{last_cat}' часто возникает потребность: '{pred_trend}' ({int(prob * 100)}%)"
            insight_type = "🔮 AI Prediction"

        # Вариант Б: Если Марков молчит -> Контекст (Ночь)
        elif time_of_day == "Night" and "night" in PSB_PRODUCTS[seg_tag]:
            secondary_prod = PSB_PRODUCTS[seg_tag]["night"]
            secondary_reason = "Клиент активен в ночное время"
            insight_type = "🌙 Context Rule"

        # Вариант В: Умный Upsell (Инвестиции)
        elif "invest" in PSB_PRODUCTS[seg_tag]:
            secondary_prod = PSB_PRODUCTS[seg_tag]["invest"]
            secondary_reason = "Предложение для накопления капитала"
            insight_type = "💰 Smart Upsell"

        # Заглушка, если вообще ничего не нашлось (редко)
        else:
            secondary_prod = {"name": "Система быстрых платежей", "desc": "Переводы без комиссии."}
            secondary_reason = "Полезный сервис"
            insight_type = "⚙️ Service"

        return {
            "user_id": user_id,
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

    def get_llm_prompt(self, data):
        if not data: return ""
        sec = data['secondary']
        return f"""
        Ты ассистент банка ПСБ. Клиент: {data['segment_name']} (Прогноз: {data['stats']['projected_month_spend']} ₽).

        1. Предложи ОСНОВНОЙ продукт: "{data['primary']['product']['name']}" ({data['primary']['product']['desc']}).
        2. Добавь "КСТАТИ" (Cross-sell): "{sec['product']['name']}" ({sec['reason']}).

        Сделай это одним связным, продающим сообщением. Упомяни выгоду.
        """
