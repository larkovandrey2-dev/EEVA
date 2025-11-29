# engine.py
import pandas as pd
import json
import random
import os
import streamlit as st
from twin_matcher import TwinMatcher
from yagpt_client import YandexGPT
from psb_catalog import CATALOG, PREDICTION_TAGS, TREND_MAPPING


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Loading EEVA Engine v4.0 (Turbo)...")

        # 1. ЗАГРУЗКА ДАННЫХ (С КЭШИРОВАНИЕМ STREAMLIT)
        self.users, self.trans = self._load_data(users_file, trans_file)

        # 2. ЗАГРУЗКА МОДУЛЕЙ
        self.matcher = self._load_matcher("clean_data/twin_index.pkl")
        self.llm = YandexGPT()

        # 3. МАРКОВ
        self.markov = self._load_markov("markov_chains.json")

    # === КЭШИРОВАННЫЕ МЕТОДЫ ЗАГРУЗКИ ===
    # Декоратор st.cache_resource сохраняет результат функции в памяти сервера.
    # Если параметры (пути к файлам) не меняются, функция не выполняется повторно!

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _load_data(users_path, trans_path):
        print("   -> Reading Parquet Data...")

        # Читаем USERS
        if users_path.endswith('.parquet'):
            users = pd.read_parquet(users_path)
        else:
            users = pd.read_csv(users_path)

        if 'user_id' in users.columns:
            users = users.set_index('user_id')

        # Читаем TRANS
        if trans_path.endswith('.parquet'):
            trans = pd.read_parquet(trans_path)
        else:
            trans = pd.read_csv(trans_path, usecols=['user_id', 'category_final', 'brand_id'])

        return users, trans

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _load_matcher(path):
        return TwinMatcher(path)

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def _load_markov(path):
        try:
            with open(path, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    # === ЛОГИКА (ОСТАЕТСЯ ПРЕЖНЕЙ) ===
    def _get_segment_info(self, cluster_id):
        if cluster_id == 2: return "VIP", "💎 Premium / VIP", 3.0
        if cluster_id == 6: return "DEFENSE", "🛡 ОПК / Силовые структуры", 1.2
        if cluster_id in [0, 5]: return "YOUTH", "🌙 Student / Young", 0.8
        if cluster_id == 4: return "SAVER", "🏠 Pensioner / Saver", 0.9
        if cluster_id == 1: return "CREDIT_RISK", "⚠️ Credit Optimization", 0.7
        return "MASS", "🛒 Mass Market", 1.0

    def _predict_next(self, user_id):
        # Оптимизация: фильтрация по индексу быстрее, если транс будет индексирован,
        # но пока оставим как есть, так как Parquet уже быстрый
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
                if exclude_name and item['name'] == exclude_name:
                    continue
                if segment in item['segment'] or "ALL" in item['segment'] or "MASS" in item['segment']:
                    matches = sum(1 for t in item['tags'] if t in tags)
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
        last_cat = None

        # Проверка наличия в индексе
        if user_id not in self.users.index:
            is_twin = True
            # TwinMatcher уже загружен и закэширован
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        try:
            user_row = self.users.loc[target_id]
            cluster_id = int(user_row['cluster_id'])

            seg_tag, seg_name, mult = self._get_segment_info(cluster_id)
            pred_trend, prob, last_cat = self._predict_next(target_id)

            user_spend = user_row['total_spend']
            if user_spend > 80000:
                needed_tags = ['luxury', 'travel', 'saving']
            else:
                needed_tags = ['shopping', 'cash', 'salary']

            primary_prod = self._find_best_product(seg_tag, needed_tags)
            if not primary_prod:
                primary_prod = CATALOG['debit'][0]

            secondary_prod = None
            reason = "Специальное предложение"
            source = "Ecosystem"
            context_tags = []

            if pred_trend and pred_trend in PREDICTION_TAGS:
                context_tags = PREDICTION_TAGS[pred_trend]
                reason = f"Актуально после категории '{last_cat}'"
                source = "🔮 Instant Need"
            elif time_of_day == "Night":
                context_tags = ['entertainment', 'transfer', 'online']
                reason = "Для ночных покупок и развлечений"
                source = "🌙 Night Context"
            else:
                context_tags = ['saving', 'debt']
                reason = "Персонально для вас"
                source = "🧠 Smart Fit"

            secondary_prod = self._find_best_product(seg_tag, context_tags, exclude_name=primary_prod['name'])

            if not secondary_prod:
                secondary_prod = self._find_best_product(seg_tag, [], exclude_name=primary_prod['name'])
                if not secondary_prod:
                    secondary_prod = CATALOG['service'][2]
                source = "🏆 Best Seller"

            # LLM вызов - асинхронность здесь не поможет, так как requests синхронный,
            # но это блокирующая операция. Для демо можно оставить как есть или сделать заглушку,
            # если LLM тормозит.
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
            print(f"❌ Error logic for {user_id}: {e}")
            return None