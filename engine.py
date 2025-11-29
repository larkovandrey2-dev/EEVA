import pandas as pd
import json
import os
import random
from twin_matcher import TwinMatcher
from yagpt_client import YandexGPT
from psb_catalog import CATALOG, PREDICTION_TAGS, TREND_MAPPING


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Loading EEVA Engine v6.0 (Final)...")

        # 1. Загрузка данных
        if users_file.endswith('.parquet'):
            self.users = pd.read_parquet(users_file)
        else:
            self.users = pd.read_csv(users_file)

        if 'user_id' in self.users.columns:
            self.users = self.users.set_index('user_id')

        # Загрузка транзакций
        if trans_file.endswith('.parquet'):
            self.trans = pd.read_parquet(trans_file)
        else:
            self.trans = pd.read_csv(trans_file)

        # 2. Модули
        twin_path = "clean_data/twin_index.pkl"
        if os.path.exists("clean_data/twin_index.pkl.bz2"):
            twin_path = "clean_data/twin_index.pkl.bz2"

        self.matcher = TwinMatcher(twin_path)
        self.llm = YandexGPT()

        # 3. Марков
        try:
            with open("markov_chains.json", "r", encoding='utf-8') as f:
                self.markov = json.load(f)
            print("Markov Model: CONNECTED")
        except:
            self.markov = {}
            print("Markov Model: OFFLINE")

        # 4.Матрица несовместимости
        self.INCOMPATIBILITY_MATRIX = {
            "YOUTH": ["VIP", "DEFENSE", "SAVER"],
            "SAVER": ["YOUTH", "VIP", "DEFENSE"],
            "VIP": ["YOUTH", "SAVER"],
            "DEFENSE": ["YOUTH"],
            "MASS": ["VIP", "DEFENSE"],
            "CREDIT_RISK": ["VIP", "invest", "luxury"]
        }

    def _get_segment_info(self, cluster_id):
        if cluster_id == 2: return "VIP", "Премиальный сегмент", 3.0
        if cluster_id == 6: return "DEFENSE", "ОПК и Силовые структуры", 1.2
        if cluster_id in [0, 5]: return "YOUTH", "Молодежный сегмент", 0.8
        if cluster_id == 4: return "SAVER", "Сберегательная модель / Пенсионеры", 0.9
        if cluster_id == 1: return "CREDIT_RISK", "Кредитная оптимизация", 0.7
        return "MASS", "Массовый сегмент", 1.0

    def _predict_next(self, user_id):
        try:
            user_tx = self.trans[self.trans['user_id'] == user_id]
        except:
            user_tx = self.trans[self.trans['user_id'] == str(user_id)]

        if user_tx.empty: return None, 0, None

        last_action_raw = user_tx.iloc[-1]['category_final']
        pred_data = self.markov.get(last_action_raw)

        if pred_data:
            raw_pred = pred_data['prediction']
            prob = pred_data['probability']
            DIVERSITY_MAP = {
                "АЗС": ["Транспорт", "Дом и Ремонт", "Фастфуд"],
                "Детские товары": ["Развлечения", "Аптеки", "Одежда и Спорт"],
                "Дом и Ремонт": ["Электроника", "Транспорт"],
                "Красота": ["Одежда и Спорт", "Развлечения", "Аптеки"],
                "Путешествия": ["Транспорт", "Развлечения"],
                "Развлечения": ["Фастфуд", "Красота"],
                "Супермаркеты": ["Дом и Ремонт", "Аптеки", "Детские товары"],
                "Фастфуд": ["Развлечения", "Транспорт"]
            }

            # 40% шанс выбрать альтернативный путь, если он есть
            if last_action_raw in DIVERSITY_MAP and random.random() < 0.4:
                raw_pred = random.choice(DIVERSITY_MAP[last_action_raw])

            trend = TREND_MAPPING.get(raw_pred, raw_pred)
            return trend, prob, last_action_raw

        return None, 0, last_action_raw

    def _calculate_score(self, item, user_segment, user_tags):
        score = 0
        prod_segments = item.get('segment', [])
        prod_tags = item.get('tags', [])
        forbidden = self.INCOMPATIBILITY_MATRIX.get(user_segment, [])
        for fs in forbidden:
            if fs in prod_segments:
                if "MASS" in prod_segments and user_segment not in ["CREDIT_RISK", "VIP"]:
                    continue
                if user_segment == "CREDIT_RISK" and fs in ["invest", "VIP"]:
                    return -1
                return -1

        if user_segment in prod_segments:
            score += 100
        elif "MASS" in prod_segments or "ALL" in prod_segments:
            score += 20
        else:
            return -1
        matches = sum(1 for t in prod_tags if t in user_tags)
        score += matches * 30

        return score

    def _get_ranked_products(self, user_segment, user_tags, exclude_names=None):
        if exclude_names is None: exclude_names = []
        ranked_items = []

        for category, items in CATALOG.items():
            for item in items:
                if item.get('name') in exclude_names:
                    continue
                score = self._calculate_score(item, user_segment, user_tags)
                if score > 0:
                    ranked_items.append((item, score))

        ranked_items.sort(key=lambda x: (-x[1], x[0]['name']))
        return [r[0] for r in ranked_items]

    def recommend(self, user_id, time_of_day="Day"):
        target_id = user_id
        is_twin = False
        match_type = "Real Data"

        # 1. Поиск Юзера / Двойника
        if user_id not in self.users.index:
            is_twin = True
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        # Получаем данные профиля
        try:
            if target_id in self.users.index:
                user_row = self.users.loc[target_id]
                try:
                    cluster_id = int(float(user_row['cluster_id']))
                except:
                    cluster_id = 3

                try:
                    user_spend = float(user_row['total_spend'])
                except:
                    user_spend = 50000.0
            else:
                cluster_id = 3
                user_spend = 50000.0

            seg_tag, seg_name, mult = self._get_segment_info(cluster_id)
            pred_trend, prob, last_cat = self._predict_next(target_id)

            needed_tags = []

            # Логика для Кредитного Риска
            if seg_tag == "CREDIT_RISK":
                needed_tags = ['debt', 'optimization', 'cash']
            # Логика для ОПК
            elif seg_tag == "DEFENSE":
                needed_tags = ['gov', 'salary', 'home']
            # Логика по тратам
            elif user_spend > 150000:
                needed_tags.extend(['luxury', 'travel', 'invest'])
            elif user_spend > 50000:
                needed_tags.extend(['shopping', 'cash', 'car'])
            else:
                needed_tags.extend(['social', 'salary', 'saving'])
            all_candidates = self._get_ranked_products(seg_tag, needed_tags)

            primary_list = []
            if all_candidates:
                primary_list.append({"product": all_candidates[0], "desc": "Лидер рейтинга"})
                if len(all_candidates) > 1:
                    primary_list.append({"product": all_candidates[1], "desc": "Альтернатива"})
            else:
                primary_list.append({"product": CATALOG['debit'][0], "desc": "Универсальное решение"})

            secondary_prod = None
            reason = "Специальное предложение"
            source = "Ecosystem"

            excluded = [p['product']['name'] for p in primary_list]

            # А. Марков (Instant Need)
            if pred_trend and pred_trend in PREDICTION_TAGS:
                context_tags = PREDICTION_TAGS[pred_trend]
                candidates = self._get_ranked_products(seg_tag, context_tags, exclude_names=excluded)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = f"Актуально после категории '{last_cat}'"
                    source = "🔮 Instant Need"

            # Б. Ночь
            if not secondary_prod and time_of_day == "Night":
                candidates = self._get_ranked_products(seg_tag, ['online', 'entertainment', 'transfer'],
                                                       exclude_names=excluded)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = "Удобно для ночных операций"
                    source = "🌙 Night Context"

            # В. Fallback (Интересное предложение)
            if not secondary_prod:
                candidates = self._get_ranked_products(seg_tag, ['transfer', 'tech', 'cashback'],
                                                       exclude_names=excluded)
                if candidates:
                    secondary_prod = candidates[0]
                else:
                    secondary_prod = CATALOG['service'][2]  # СБП Плюс
                source = "🏆 Best Seller"
                reason = "Популярно в вашем сегменте"

            # LLM Генерация
            try:
                llm_text = self.llm.generate_offer(
                    segment=seg_name,
                    product_name=secondary_prod.get('name'),
                    reason=reason,
                    context_trigger=source
                )
            except:
                llm_text = f"Рекомендуем: {secondary_prod.get('name')}"

            return {
                "user_id": user_id,
                "is_twin": is_twin,
                "match_type": match_type,
                "segment_name": seg_name,
                "last_cat": last_cat,
                "stats": {"projected_spend": int(user_spend)},
                "primary": primary_list,
                "secondary": {
                    "type": source,
                    "product": secondary_prod,
                    "reason": reason,
                    "marketing_msg": llm_text
                },
                "debug": {"tags": needed_tags, "segment": seg_tag, "trend": pred_trend}
            }

        except Exception as e:
            print(f"❌ Error logic: {e}")
            # Безопасный Fallback
            safe_primary = [{"product": CATALOG['debit'][0], "desc": "Базовый продукт"}]
            safe_secondary = {
                "name": "СБП Плюс",
                "desc": "Сервис быстрых платежей",
                "segment": ["ALL"],
                "tags": ["transfer"]
            }
            return {
                "user_id": user_id,
                "is_twin": True,
                "match_type": "🛡 Safe Fallback",
                "segment_name": "New Client",
                "last_cat": None,
                "stats": {"projected_spend": 0},
                "primary": safe_primary,
                "secondary": {
                    "type": "⚙️ System",
                    "product": safe_secondary,
                    "reason": "Популярный сервис",
                    "marketing_msg": "Начните с удобных сервисов ПСБ!"
                },
                "debug": {"error": str(e)}
            }