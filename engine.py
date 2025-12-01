import pandas as pd
import json
import os
import random
from twin_matcher import TwinMatcher
from yagpt_client import YandexGPT
from psb_catalog import CATALOG, PREDICTION_TAGS, TREND_MAPPING


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Загрузка ядра рекомендаций v6.1 (Stable)...")

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

        # 2. Модуль поиска двойников
        twin_path = "clean_data/twin_index.pkl"
        if os.path.exists("clean_data/twin_index.pkl.bz2"):
            twin_path = "clean_data/twin_index.pkl.bz2"

        self.matcher = TwinMatcher(twin_path)
        self.llm = YandexGPT()

        # 3. Марковские цепи
        try:
            with open("markov_chains.json", "r", encoding='utf-8') as f:
                self.markov = json.load(f)
            print("Модель переходов: ПОДКЛЮЧЕНА")
        except:
            self.markov = {}
            print("Модель переходов: НЕДОСТУПНА")

        # 4. Матрица несовместимости
        self.INCOMPATIBILITY_MATRIX = {
            "YOUTH": ["VIP", "DEFENSE", "SAVER"],
            "SAVER": ["YOUTH", "VIP", "DEFENSE"],
            "VIP": ["YOUTH", "SAVER"],
            "DEFENSE": ["YOUTH"],
            "MASS": ["VIP", "DEFENSE"],
            "CREDIT_RISK": ["VIP", "invest"]
        }

    def _get_segment_info(self, cluster_id):
        # 7 Кластеров
        if cluster_id == 2: return "VIP", "Премиальный сегмент", 3.0
        if cluster_id == 6: return "DEFENSE", "ОПК и Силовые структуры", 1.2
        if cluster_id in [0, 5]: return "YOUTH", "Молодежный сегмент", 0.8
        if cluster_id == 4: return "SAVER", "Сберегательная модель", 0.9
        if cluster_id == 1: return "CREDIT_RISK", "Кредитная оптимизация", 0.7
        if cluster_id == 3: return "MASS", "Активный пользователь", 1.1
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
            trend = TREND_MAPPING.get(raw_pred, raw_pred)
            return trend, pred_data['probability'], last_action_raw

        return None, 0, last_action_raw

    def _calculate_score(self, item, user_segment, user_tags):
        """
        Расчет релевантности продукта (Баллы)
        """
        score = 0
        prod_segments = item.get('segment', [])
        prod_tags = item.get('tags', [])
        prod_name = item.get('name', '')

        # 1. БЛОКИРОВКА ПО СЕГМЕНТУ
        forbidden = self.INCOMPATIBILITY_MATRIX.get(user_segment, [])
        for fs in forbidden:
            if fs in prod_segments:
                # Исключение: Mass продукты можно предлагать рисковым
                if "MASS" in prod_segments and user_segment not in ["CREDIT_RISK", "VIP"]:
                    continue
                if user_segment == "CREDIT_RISK" and fs in ["invest", "VIP"]:
                    return -1
                return -1

        # 2. ПРИОРИТЕТ СЕГМЕНТА
        if user_segment in prod_segments:
            score += 100  # Прямое попадание
        elif "MASS" in prod_segments or "ALL" in prod_segments:
            score += 20  # Универсальный продукт
        else:
            return -1

        # 3. ПРИОРИТЕТ ПОТРЕБНОСТЕЙ (ТЕГОВ)
        matches = sum(1 for t in prod_tags if t in user_tags)
        score += matches * 30

        # 4. ШТРАФЫ И КОРРЕКТИРОВКИ (Fix "Accent" problem)

        # Если продукт инвестиционный, а клиенту инвестиции не нужны (нет тега invest) -> сильный штраф
        if "saving" in prod_tags or "invest" in prod_segments:
            if "invest" not in user_tags and "saving" not in user_tags:
                score -= 50

        # Не предлагать кредит, если он не нужен явно
        if "Кредит" in prod_name and "credit" not in user_tags and "debt" not in user_tags:
            score -= 10

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

        # Сортировка по баллам
        ranked_items.sort(key=lambda x: (-x[1], x[0]['name']))
        return [r[0] for r in ranked_items]

    def recommend(self, user_id, time_of_day="Day"):
        target_id = user_id
        is_twin = False
        match_type = "Реальный профиль"

        # 1. ПОИСК ДВОЙНИКА
        if user_id not in self.users.index:
            is_twin = True
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        try:
            # 2. ПОЛУЧЕНИЕ ПРОФИЛЯ
            if target_id in self.users.index:
                user_row = self.users.loc[target_id]
                try:
                    cluster_id = int(float(user_row['cluster_id']))
                except:
                    cluster_id = 3  # Default to Mass

                try:
                    user_spend = float(user_row['total_spend'])
                except:
                    user_spend = 50000.0
            else:
                cluster_id = 3
                user_spend = 50000.0

            seg_tag, seg_name, mult = self._get_segment_info(cluster_id)
            pred_trend, prob, last_cat = self._predict_next(target_id)

            # 3. ФОРМИРОВАНИЕ ПОТРЕБНОСТЕЙ (Tags)
            needed_tags = []

            # БАЗОВЫЕ ТЕГИ (Чтобы дебетовки всегда были в топе)
            needed_tags.extend(['shopping', 'lifestyle', 'transfer'])

            # ЛОГИКА ПО ТРАТАМ
            if user_spend > 150000:
                needed_tags.extend(['luxury', 'travel', 'invest'])
            elif user_spend > 50000:
                needed_tags.extend(['car', 'tech', 'cash'])
            else:
                needed_tags.extend(['social', 'salary', 'groceries'])

            # ДОП. ТЕГИ ПО СЕГМЕНТАМ
            if seg_tag == "DEFENSE": needed_tags.append('gov')
            if seg_tag == "YOUTH": needed_tags.extend(['entertainment', 'tech'])
            if seg_tag == "CREDIT_RISK": needed_tags.extend(['debt', 'optimization'])

            # SAVING добавляем только если есть деньги или это пенсионер
            if user_spend > 40000 or seg_tag == "SAVER":
                needed_tags.append('saving')

            # 4. ПОДБОР PRIMARY
            all_candidates = self._get_ranked_products(seg_tag, needed_tags)

            primary_list = []
            if all_candidates:
                primary_list.append({"product": all_candidates[0], "desc": "Лидер рейтинга"})
                if len(all_candidates) > 1:
                    primary_list.append({"product": all_candidates[1], "desc": "Альтернатива"})
            else:
                # Заглушка, если ничего не подошло
                debit = CATALOG.get('debit', [{}])[0]
                primary_list.append({"product": debit, "desc": "Универсальное решение"})

            # 5. ПОДБОР SECONDARY
            secondary_prod = None
            reason = "Специальное предложение"
            source = "Экосистема"

            excluded = [p['product'].get('name') for p in primary_list]

            # А. Марков
            if pred_trend and pred_trend in PREDICTION_TAGS:
                context_tags = PREDICTION_TAGS[pred_trend]
                candidates = self._get_ranked_products(seg_tag, context_tags, exclude_names=excluded)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = f"Актуально на основе последних покупок"
                    source = "Актуальная потребность"

            # Б. Ночь
            if not secondary_prod and time_of_day == "Night":
                candidates = self._get_ranked_products(seg_tag, ['online', 'entertainment'], exclude_names=excluded)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = "Удобно для покупок в вечернее время"
                    source = "Вечерний сценарий"

            # В. Fallback
            if not secondary_prod:
                candidates = self._get_ranked_products(seg_tag, needed_tags, exclude_names=excluded)
                if candidates:
                    secondary_prod = candidates[0]
                else:
                    secondary_prod = CATALOG['service'][2]  # СБП Плюс
                source = "Популярный выбор"
                reason = "Часто выбирают в вашем сегменте"

            # 6. LLM
            try:
                llm_text = self.llm.generate_offer(
                    segment=seg_name,
                    product_name=secondary_prod.get('name', 'Продукт'),
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
                "stats": {"projected_spend": int(user_spend * mult)},
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
            print(f"❌ Error logic for {user_id}: {e}")
            safe_prod = CATALOG.get('debit', [{}])[0]

            return {
                "user_id": user_id,
                "is_twin": True,
                "match_type": "Безопасный режим",
                "segment_name": "Новый клиент",
                "last_cat": None,
                "stats": {"projected_spend": 0},
                "primary": [{"product": safe_prod, "desc": "Базовый продукт"}],
                "secondary": {
                    "type": "Сервис",
                    "product": {"name": "СБП Плюс", "desc": "Платежи"},
                    "reason": "Популярный сервис",
                    "marketing_msg": "Начните с удобных сервисов ПСБ!"
                },
                "debug": {"error": str(e), "segment": "N/A", "trend": "N/A"}
            }