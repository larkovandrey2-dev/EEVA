import pandas as pd
import json
import random
from twin_matcher import TwinMatcher
from yagpt_client import YandexGPT
from psb_catalog import CATALOG, PREDICTION_TAGS, TREND_MAPPING


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Loading EEVA Engine v3.1 (Fixed)")
        # Грузим данные
        self.users = pd.read_parquet(users_file).set_index('user_id')
        self.trans = pd.read_parquet(trans_file, columns=['user_id', 'category_final', 'brand_id'])

        # Модули
        self.matcher = TwinMatcher("clean_data/twin_index.pkl.bz2")
        self.llm = YandexGPT()

        # Марков
        try:
            with open("markov_chains.json", "r", encoding='utf-8') as f:
                self.markov = json.load(f)
            print("✅ Markov Model: CONNECTED")
        except:
            self.markov = {}
            print("⚠️ Markov Model: OFFLINE")

    def _get_segment_info(self, cluster_id):
        # Возвращает 3 значения: TAG, Name, Multiplier
        if cluster_id == 2: return "VIP", "💎 Premium / VIP", 3.0
        if cluster_id == 6: return "DEFENSE", "🛡 ОПК / Силовые структуры", 1.2
        if cluster_id in [0, 5]: return "YOUTH", "🌙 Student / Young", 0.8
        if cluster_id == 4: return "SAVER", "🏠 Pensioner / Saver", 0.9
        if cluster_id == 1: return "CREDIT_RISK", "⚠️ Credit Optimization", 0.7
        return "MASS", "🛒 Mass Market", 1.0

    def _predict_next(self, user_id):
        """
        Возвращает ровно 3 значения:
        1. Тренд (строка или None)
        2. Вероятность (float)
        3. Последняя категория (строка или None)
        """
        user_tx = self.trans[self.trans['user_id'] == user_id]

        if user_tx.empty:
            return None, 0, None

        last_action_raw = user_tx.iloc[-1]['category_final']

        pred_data = self.markov.get(last_action_raw)

        if pred_data:
            # Маппим сырое предсказание на наш каталог
            raw_pred = pred_data['prediction']
            trend = TREND_MAPPING.get(raw_pred, raw_pred)
            return trend, pred_data['probability'], last_action_raw

        return None, 0, last_action_raw

    def _find_best_product(self, segment, tags, exclude_name=None):
        candidates = []

        for category, items in CATALOG.items():
            for item in items:
                if exclude_name and item['name'] == exclude_name:
                    continue

                # Проверка сегмента или ALL
                if segment in item['segment'] or "ALL" in item['segment'] or "MASS" in item['segment']:

                    matches = sum(1 for t in item['tags'] if t in tags)

                    if matches > 0:
                        candidates.append((item, matches * 2))  # Приоритет тегам
                    else:
                        candidates.append((item, 1))  # Просто сегмент

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        # Берем рандом из топ-3 для вариативности
        top_n = candidates[:3]
        return random.choice(top_n)[0]

    def recommend(self, user_id, time_of_day="Day"):
        target_id = user_id
        is_twin = False
        match_type = "Real Data"
        last_cat = None
        # 1. Twin Logic
        if user_id not in self.users.index:
            is_twin = True
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        try:
            # 2. Получаем профиль
            user_row = self.users.loc[target_id]
            cluster_id = int(user_row['cluster_id'])

            # Распаковка 3 значений
            seg_tag, seg_name, mult = self._get_segment_info(cluster_id)

            # Распаковка 3 значений
            pred_trend, prob, last_cat = self._predict_next(target_id)

            # 3. Выбор Primary продукта
            user_spend = user_row['total_spend']
            if user_spend > 80000:
                needed_tags = ['luxury', 'travel', 'saving']
            else:
                needed_tags = ['shopping', 'cash', 'salary']

            primary_prod = self._find_best_product(seg_tag, needed_tags)

            # Fallback
            if not primary_prod:
                primary_prod = CATALOG['debit'][0]

            # 4. Выбор Secondary (Context) продукта
            secondary_prod = None
            reason = "Специальное предложение"
            source = "Ecosystem"
            context_tags = []

            # Логика Маркова
            if pred_trend and pred_trend in PREDICTION_TAGS:
                context_tags = PREDICTION_TAGS[pred_trend]
                reason = f"Актуально после категории '{last_cat}'"
                source = "🔮 Instant Need"

            # Логика Времени
            elif time_of_day == "Night":
                context_tags = ['entertainment', 'transfer', 'online']
                reason = "Для ночных покупок и развлечений"
                source = "🌙 Night Context"

            # Логика Лайфстайла (если нет Маркова)
            else:
                context_tags = ['saving', 'debt']
                reason = "Персонально для вас"
                source = "🧠 Smart Fit"

            # Ищем продукт, исключая Primary
            secondary_prod = self._find_best_product(seg_tag, context_tags, exclude_name=primary_prod['name'])

            # Fallback Secondary
            if not secondary_prod:
                secondary_prod = self._find_best_product(seg_tag, [], exclude_name=primary_prod['name'])
                if not secondary_prod:  # Если совсем всё плохо
                    secondary_prod = CATALOG['service'][2]  # СБП Плюс
                source = "🏆 Best Seller"

            # 5. Генерация текста (LLM)
            # Чтобы не падало, добавим try/except на сам вызов LLM
            try:
                llm_text = self.llm.generate_offer(
                    segment=seg_name,
                    product_name=secondary_prod['name'],
                    reason=reason,
                    context_trigger=source
                )
            except:
                llm_text = f"Рекомендуем: {secondary_prod['name']}"

            return {
                "user_id": user_id,
                "is_twin": is_twin,
                "match_type": match_type,
                "segment_name": seg_name,
                "last_cat": last_cat,
                "stats": {"projected_spend": int(user_row['total_spend'] * mult)},
                "primary": {"product": primary_prod, "desc": "Базовый продукт"},
                "secondary": {
                    "type": source,
                    "product": secondary_prod,
                    "reason": reason,
                    "marketing_msg": llm_text
                },
                "debug": {"tags": context_tags, "segment": seg_tag, "trend": pred_trend}
            }

        except Exception as e:
            # Для отладки выведем полный трейс
            print(f"❌ Error logic for {user_id}: {e}")
            return None