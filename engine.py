import pandas as pd
import json
import random
from twin_matcher import TwinMatcher
from yagpt_client import YandexGPT
from psb_catalog import CATALOG, PREDICTION_TAGS, TREND_MAPPING


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Loading EEVA Engine v3.2 (Crash Proof)")

        # 1. Загрузка данных
        # Проверяем расширение, чтобы читать и CSV и Parquet
        if users_file.endswith('.parquet'):
            self.users = pd.read_parquet(users_file).set_index('user_id')
        else:
            self.users = pd.read_csv(users_file).set_index('user_id')

        if trans_file.endswith('.parquet'):
            self.trans = pd.read_parquet(trans_file)
        else:
            self.trans = pd.read_csv(trans_file, usecols=['user_id', 'category_final', 'brand_id'])

        # 2. Модули
        self.matcher = TwinMatcher("clean_data/twin_index.pkl.bz2")
        self.llm = YandexGPT()

        # 3. Марков
        try:
            with open("markov_chains.json", "r", encoding='utf-8') as f:
                self.markov = json.load(f)
            print("✅ Markov Model: CONNECTED")
        except:
            self.markov = {}
            print("⚠️ Markov Model: OFFLINE")

    def _get_segment_info(self, cluster_id):
        if cluster_id == 2: return "VIP", "💎 Premium / VIP", 3.0
        if cluster_id == 6: return "DEFENSE", "🛡 ОПК / Силовые структуры", 1.2
        if cluster_id in [0, 5]: return "YOUTH", "🌙 Student / Young", 0.8
        if cluster_id == 4: return "SAVER", "🏠 Pensioner / Saver", 0.9
        if cluster_id == 1: return "CREDIT_RISK", "⚠️ Credit Optimization", 0.7
        return "MASS", "🛒 Mass Market", 1.0

    def _predict_next(self, user_id):
        user_tx = self.trans[self.trans['user_id'] == user_id]

        if user_tx.empty:
            return None, 0, None

        last_action_raw = user_tx.iloc[-1]['category_final']
        pred_data = self.markov.get(last_action_raw)

        if pred_data:
            raw_pred = pred_data['prediction']
            trend = TREND_MAPPING.get(raw_pred, raw_pred)
            return trend, pred_data['probability'], last_action_raw

        return None, 0, last_action_raw

    def _find_best_product(self, segment, tags, exclude_name=None):
        candidates = []

        for category, items in CATALOG.items():
            for item in items:
                # Безопасное получение имени
                prod_name = item.get('name', 'Unknown')
                if exclude_name and prod_name == exclude_name:
                    continue

                # --- ФИКС ЗДЕСЬ ---
                # Используем .get(), чтобы код не падал, если ключа нет
                prod_segments = item.get('segment', [])
                prod_tags = item.get('tags', [])
                # ------------------

                # Проверка сегмента или ALL
                if segment in prod_segments or "ALL" in prod_segments or "MASS" in prod_segments:
                    matches = sum(1 for t in prod_tags if t in tags)
                    if matches > 0:
                        candidates.append((item, matches * 2))
                    else:
                        candidates.append((item, 1))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_n = candidates[:3]
        return random.choice(top_n)[0]

    def recommend(self, user_id, time_of_day="Day"):
        target_id = user_id
        is_twin = False
        match_type = "Real Data"

        # 1. Twin Logic
        if user_id not in self.users.index:
            is_twin = True
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        try:
            # 2. Получаем профиль
            user_row = self.users.loc[target_id]
            cluster_id = int(user_row['cluster_id'])

            seg_tag, seg_name, mult = self._get_segment_info(cluster_id)
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
                # Берем первый попавшийся дебетовый как заглушку, если каталог пустой или не совпал
                try:
                    primary_prod = CATALOG['debit'][0]
                except:
                    primary_prod = {"name": "Дебетовая карта", "desc": "Универсальная карта"}

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

            # Логика Лайфстайла
            else:
                context_tags = ['saving', 'debt']
                reason = "Персонально для вас"
                source = "🧠 Smart Fit"

            # Ищем продукт
            primary_name = primary_prod.get('name')
            secondary_prod = self._find_best_product(seg_tag, context_tags, exclude_name=primary_name)

            # Fallback Secondary
            if not secondary_prod:
                secondary_prod = self._find_best_product(seg_tag, [], exclude_name=primary_name)
                if not secondary_prod:
                    # Заглушка, если вообще ничего не нашли
                    secondary_prod = {"name": "СБП Плюс", "desc": "Платежи без комиссии"}
                source = "🏆 Best Seller"

            # 5. Генерация текста (LLM)
            # Оборачиваем в try, чтобы ошибка LLM не ломала весь сайт
            try:
                llm_text = self.llm.generate_offer(
                    segment=seg_name,
                    product_name=secondary_prod.get('name', 'Продукт'),
                    reason=reason,
                    context_trigger=source
                )
            except:
                llm_text = f"Рекомендуем: {secondary_prod.get('name', 'Продукт')}"

            return {
                "user_id": user_id,
                "is_twin": is_twin,
                "match_type": match_type,
                "segment_name": seg_name,
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
            # Выводим ошибку в консоль, но не крашим приложение, если это возможно
            print(f"❌ CRITICAL ERROR for {user_id}: {e}")
            # Возвращаем хоть что-то, чтобы UI показал ошибку красиво
            return None