import pandas as pd
import json
from twin_matcher import TwinMatcher
from yagpt_client import YandexGPT
from psb_catalog import CATALOG, PREDICTION_TAGS, TREND_MAPPING


class RecommendationEngine:
    def __init__(self, users_file, trans_file):
        print("Loading EEVA Engine v5.0 (Deterministic Logic)...")

        # 1. Загрузка данных
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

        # 4. МАТРИЦА НЕСОВМЕСТИМОСТИ (Hard Blockers)
        # Ключ: Сегмент Юзера -> Значение: Запрещенные сегменты продуктов
        self.INCOMPATIBILITY_MATRIX = {
            "YOUTH": ["VIP", "DEFENSE", "SAVER"],  # Студент не может быть военным (в рамках продуктов) или пенсионером
            "SAVER": ["YOUTH", "VIP", "DEFENSE"],  # Пенсионер не может быть студентом
            "VIP": ["YOUTH", "SAVER"],  # VIPу не предлагаем эконом и студенческие
            "DEFENSE": ["YOUTH", "SAVER"],  # Военному не предлагаем студенческие
            "MASS": ["VIP", "DEFENSE"],  # Массовому не предлагаем спец. продукты
            "CREDIT_RISK": ["VIP", "invest"]  # Рисковым не предлагаем VIP и Инвестиции
        }

    def _get_segment_info(self, cluster_id):
        if cluster_id == 2: return "VIP", "💎 Premium / VIP", 3.0
        if cluster_id == 6: return "DEFENSE", "🛡 ОПК / Силовые структуры", 1.2
        if cluster_id in [0, 5]: return "YOUTH", "🌙 Student / Young", 0.8
        if cluster_id == 4: return "SAVER", "🏠 Pensioner / Saver", 0.9
        if cluster_id == 1: return "CREDIT_RISK", "⚠️ Credit Optimization", 0.7
        return "MASS", "🛒 Mass Market", 1.0

    def _predict_next(self, user_id):
        user_tx = self.trans[self.trans['user_id'] == user_id]
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
        Строгая математика вместо фильтров.
        Возвращает: Число (очки). Если -1, продукт запрещен.
        """
        score = 0

        prod_segments = item.get('segment', [])
        prod_tags = item.get('tags', [])
        prod_name = item.get('name', '')

        # 1. ПРОВЕРКА НА НЕСОВМЕСТИМОСТЬ (Hard Block)
        forbidden_segments = self.INCOMPATIBILITY_MATRIX.get(user_segment, [])
        # Если продукт принадлежит ТОЛЬКО к запрещенным сегментам - бан
        # Но если продукт ["MASS", "YOUTH"] а юзер "SAVER" (запрет Youth),
        # то MASS спасает ситуацию? Нет, если есть хоть один запрещенный тег - лучше не рисковать.
        for fs in forbidden_segments:
            if fs in prod_segments:
                return -1

                # 2. СЕГМЕНТНЫЙ СКОРИНГ
        if user_segment in prod_segments:
            score += 50  # Прямое попадание (Это карта именно для этого сегмента)
        elif "MASS" in prod_segments or "ALL" in prod_segments:
            score += 10  # Универсальный продукт (меньше приоритет)
        else:
            return -1  # Продукт вообще не для этого сегмента и не универсальный

        # 3. ТЕГОВЫЙ СКОРИНГ (Мягкий приоритет)
        # Теги добавляют баллы, но не являются обязательными условием (unless score=0)
        matches = sum(1 for t in prod_tags if t in user_tags)
        score += matches * 10

        # 4. БОНУСЫ
        # Кредиткам чуть меньше приоритет в Primary, если не указано иное
        if "Кредит" in prod_name and "credit" not in user_tags:
            score -= 5

        return score

    def _get_ranked_products(self, user_segment, user_tags, exclude_names=None):
        """
        Возвращает ВСЕ подходящие продукты, отсортированные по релевантности.
        """
        if exclude_names is None: exclude_names = []
        ranked_items = []

        # Проходим по всему каталогу
        for category, items in CATALOG.items():
            for item in items:
                if item.get('name') in exclude_names:
                    continue

                score = self._calculate_score(item, user_segment, user_tags)

                if score > 0:
                    ranked_items.append((item, score))

        # СОРТИРОВКА (ДЕТЕРМИНИРОВАННАЯ)
        # 1. По очкам (убывание)
        # 2. По имени (возрастание) - чтобы при равных очках всегда был один порядок
        ranked_items.sort(key=lambda x: (-x[1], x[0]['name']))

        return [r[0] for r in ranked_items]

    def recommend(self, user_id, time_of_day="Day"):
        target_id = user_id
        is_twin = False
        match_type = "Real Data"

        # Cold Start
        if user_id not in self.users.index:
            is_twin = True
            target_id, match_type = self.matcher.find_twin(user_id, self.users.index)

        try:
            # Данные
            user_row = self.users.loc[target_id]
            try:
                cluster_id = int(float(user_row['cluster_id']))
            except:
                cluster_id = -1

            seg_tag, seg_name, mult = self._get_segment_info(cluster_id)
            pred_trend, prob, last_cat = self._predict_next(target_id)
            user_spend = float(user_row['total_spend'])

            # === 1. ФОРМИРОВАНИЕ ПОТРЕБНОСТЕЙ (ТЕГОВ) ===
            needed_tags = []

            # По тратам
            if user_spend > 120000:
                needed_tags.extend(['luxury', 'travel', 'invest'])
            elif user_spend > 60000:
                needed_tags.extend(['shopping', 'cash', 'car'])
            else:
                needed_tags.extend(['social', 'salary', 'saving'])

            # По сегменту (усиление)
            if seg_tag == "DEFENSE": needed_tags.append('gov')
            if seg_tag == "YOUTH": needed_tags.extend(['entertainment', 'tech'])
            if seg_tag == "SAVER": needed_tags.append('pharmacy')

            # === 2. ПОДБОР PRIMARY (СТРАТЕГИЯ) ===
            # Получаем весь список, отсортированный по качеству
            all_candidates = self._get_ranked_products(seg_tag, needed_tags)

            primary_list = []
            if all_candidates:
                # Берем лучший
                primary_list.append({"product": all_candidates[0], "desc": "Лидер рейтинга для вашего профиля"})
                # Берем второй лучший (если есть)
                if len(all_candidates) > 1:
                    primary_list.append({"product": all_candidates[1], "desc": "Альтернативный вариант"})
            else:
                # Fallback (только если совсем пусто)
                primary_list.append({"product": CATALOG['debit'][0], "desc": "Универсальное решение"})

            # === 3. ПОДБОР SECONDARY (ТАКТИКА) ===
            secondary_prod = None
            reason = "Специальное предложение"
            source = "Ecosystem"
            context_tags = []

            # Список исключений (чтобы не дублировать Primary)
            excluded_names = [p['product']['name'] for p in primary_list]

            # А. Марков (Наивысший приоритет)
            if pred_trend and pred_trend in PREDICTION_TAGS:
                context_tags = PREDICTION_TAGS[pred_trend]
                # Ищем строго по тегам контекста
                candidates = self._get_ranked_products(seg_tag, context_tags, exclude_names=excluded_names)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = f"Актуально после категории '{last_cat}'"
                    source = "🔮 Instant Need"

            # Б. Контекст Времени
            if not secondary_prod and time_of_day == "Night":
                context_tags = ['online', 'entertainment']
                candidates = self._get_ranked_products(seg_tag, context_tags, exclude_names=excluded_names)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = "Удобно для покупок ночью"
                    source = "🌙 Night Context"

            # В. Умный Upsell (если предыдущие молчат)
            if not secondary_prod:
                # Пытаемся продать то, что клиент еще не купил, но может (Инвест или Кредит)
                upsell_tags = ['invest'] if user_spend > 50000 else ['credit', 'cash']
                candidates = self._get_ranked_products(seg_tag, upsell_tags, exclude_names=excluded_names)
                if candidates:
                    secondary_prod = candidates[0]
                    reason = "Дополнительные возможности"
                    source = "🧠 Smart Fit"

            # Г. Fallback
            if not secondary_prod:
                # Берем просто следующий лучший продукт из общего списка
                fallback_candidates = self._get_ranked_products(seg_tag, needed_tags, exclude_names=excluded_names)
                if fallback_candidates:
                    secondary_prod = fallback_candidates[0]
                else:
                    secondary_prod = {"name": "СБП Плюс", "desc": "Сервис быстрых платежей"}
                source = "🏆 Best Seller"
                reason = "Популярно среди клиентов"

            # LLM
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
                "stats": {"projected_spend": int(user_spend * mult)},
                "primary": primary_list,
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