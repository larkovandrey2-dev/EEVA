import streamlit as st
from engine import RecommendationEngine


USERS_PATH = "clean_data/users_fast.parquet"
TRANS_PATH = "clean_data/trans_fast.parquet"

# --- Настройка страницы ---
st.set_page_config(page_title="ПСБ. Рекомендации", layout="centered")


# --- Инициализация ---
@st.cache_resource
def get_engine():
    return RecommendationEngine(USERS_PATH, TRANS_PATH)


try:
    engine = get_engine()
    data_loaded = True
except Exception as e:
    st.error(f"Ошибка загрузки системы: {e}")
    data_loaded = False

# ==========================================
# CSS: ПЛИТОЧНЫЙ ДИЗАЙН (TILES)
# ==========================================
st.markdown("""
<style>
    /* === ШРИФТЫ === */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Verdana:wght@400;700&display=swap');

    h1, h2, h3, .stButton > button { font-family: 'Montserrat', sans-serif !important; font-weight: 600; }
    p, div, label, input { font-family: 'Verdana', sans-serif !important; }

    /* === ОСНОВНОЙ ФОН === */
    .stApp, .main .block-container { background-color: #FFFFFF !important; color: #000000 !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .main .block-container { padding-top: 2rem !important; }

    /* === ИНПУТЫ === */
    .stTextInput > div > div > input {
        background-color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
        color: #000000 !important;
        font-weight: 500;
        caret-color: #000000 !important;
    }
    .stTextInput > div > div > input:focus { border-color: #EA5614 !important; border-width: 2px; }
    .stTextInput > label { color: #2B2C84 !important; font-weight: 700 !important; }

    /* === КНОПКИ === */
    .stButton > button {
        background-color: #EA5614 !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(234, 86, 20, 0.2);
        transition: transform 0.1s ease-in-out;
    }
    .stButton > button:hover { 
        background-color: #C1440E !important; 
        transform: translateY(-2px);
    }

    /* === ПЛИТКИ (TILES) === */
    .tile-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px; /* Закругленные углы */
        padding: 24px;
        height: 100%;
        min-height: 320px; /* Фиксируем минимальную высоту для выравнивания */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.3s ease, transform 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .tile-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-4px);
        border-color: #EA5614;
    }

    /* Верхняя цветная полоска внутри плитки */
    .tile-accent-primary {
        position: absolute; top: 0; left: 0; right: 0; height: 6px;
        background: #EA5614;
    }
    .tile-accent-secondary {
        position: absolute; top: 0; left: 0; right: 0; height: 6px;
        background: #2B2C84;
    }

    /* Контент внутри плитки */
    .tile-header {
        font-size: 0.75rem;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 12px;
    }
    .text-orange { color: #EA5614; }
    .text-blue { color: #2B2C84; }

    .tile-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
        line-height: 1.2;
    }

    .tile-desc {
        font-size: 0.95rem;
        color: #4B5563;
        margin-bottom: 20px;
        line-height: 1.5;
        flex-grow: 1; /* Растягивает описание, прижимая футер вниз */
    }

    .tile-footer {
        background-color: #F9FAFB;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.85rem;
        color: #1F2937;
        border-left: 3px solid #D1D5DB;
    }

    .tile-footer b { display: block; margin-bottom: 4px; color: #111827; }

    /* === DEBUG === */
    .streamlit-expanderHeader { background-color: #F0F7FF !important; color: #2B2C84 !important; border: 1px solid #D1D5DB; }
     [data-testid="stMetricLabel"] { 
        color: #374151 !important; /* ТЕМНО-СЕРЫЙ ЦВЕТ (ПОЧТИ ЧЕРНЫЙ) */
        font-size: 0.9rem !important; 
        font-weight: 600 !important;
        opacity: 1 !important; /* Убираем прозрачность, если она есть */
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        color: #2B2C84 !important; /* СИНИЙ ДЛЯ ЗНАЧЕНИЙ */
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

#---UI---#

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("PSB_logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #2B2C84'>ПСБ БАНК</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #374151;'>Система персональных предложений</h3>",
            unsafe_allow_html=True)

# Поиск
user_input = st.text_input("Введите ID клиента", placeholder="Например: 16466")

if st.button("Подобрать продукты"):
    if not user_input:
        st.warning("Введите ID!")
    else:
        try:
            user_id = int(user_input.strip())
            rec = engine.recommend(user_id)
        except ValueError:
            st.error("ID должен быть числом.")
            st.stop()

        if rec:
            # --- 1. СТАТУС КЛИЕНТА ---
            is_twin = rec.get('is_twin', False)
            segment = rec.get('segment_name', 'Неизвестно')
            match_type = rec.get('match_type', 'Real Data')

            if is_twin:
                st.info(f"**Новый клиент** (Холодный старт). Метод: **{match_type}**. Сегмент: **{segment}**")
            else:
                st.success(f"Клиент найден в базе. Сегмент: **{segment}**")

            # --- ОТСТУП ---
            st.markdown("<br>", unsafe_allow_html=True)

            # ==========================================
            # ВЕРХНИЙ РЯД: 2 ПЛИТКИ (PRIMARY)
            # ==========================================
            primary_list = rec.get('primary', [])

            c1, c2 = st.columns(2)

            # ПЛИТКА 1 (СТРАТЕГИЯ)
            with c1:
                if len(primary_list) > 0:
                    p1 = primary_list[0]
                    prod1 = p1.get('product', {})

                    html_p1 = f"""
                    <div class="tile-card">
                        <div class="tile-accent-primary"></div>
                        <div class="tile-header text-orange">🔥 Стратегический выбор</div>
                        <div class="tile-title">{prod1.get('name', 'Продукт')}</div>
                        <div class="tile-desc">{prod1.get('desc', '')}</div>
                        <div class="tile-footer" style="border-left-color: #EA5614; background: #FFF5F0;">
                            <b>Почему это подходит:</b>
                            {p1.get('desc', 'Базовый продукт')}
                        </div>
                    </div>
                    """
                    st.markdown(html_p1, unsafe_allow_html=True)
                else:
                    st.info("Нет предложений")

            # ПЛИТКА 2 (АЛЬТЕРНАТИВА)
            with c2:
                if len(primary_list) > 1:
                    p2 = primary_list[1]
                    prod2 = p2.get('product', {})

                    # Изменяем текст причины, чтобы он не дублировал заголовок
                    reason_text = "Отличные условия для вашего сегмента" if "Альтернатив" in p2.get('desc',
                                                                                                    '') else p2.get(
                        'desc')

                    html_p2 = f"""
                    <div class="tile-card">
                        <div class="tile-accent-primary" style="opacity: 0.5;"></div>
                        <div class="tile-header text-orange" style="opacity: 0.8;">⚡ Вариант для сравнения</div>
                        <div class="tile-title">{prod2.get('name', 'Продукт')}</div>
                        <div class="tile-desc">{prod2.get('desc', '')}</div>
                        <div class="tile-footer">
                            <b>В чем особенность:</b>
                            {reason_text}
                        </div>
                    </div>
                    """
                    st.markdown(html_p2, unsafe_allow_html=True)
                else:
                    # Заглушка, чтобы сохранить сетку
                    st.markdown("""
                    <div class="tile-card" style="justify-content: center; align-items: center; border-style: dashed;">
                        <span style="color: #9CA3AF; font-style: italic;">Альтернатив не найдено</span>
                    </div>
                    """, unsafe_allow_html=True)

            # ==========================================
            # НИЖНИЙ РЯД: 1 ШИРОКАЯ ПЛИТКА (AI / SECONDARY)
            # ==========================================
            st.markdown("<br>", unsafe_allow_html=True)

            s_data = rec.get('secondary', {})
            prod_s = s_data.get('product', {})

            if prod_s:
                marketing_msg = s_data.get('marketing_msg', s_data.get('reason', ''))

                # Перевод типов
                raw_type = s_data.get('type', '').replace("🔮 ", "").replace("🌙 ", "").replace("🧠 ", "").replace("🏆 ",
                                                                                                                "")
                type_map = {
                    "Instant Need": "Моментальная потребность",
                    "Night Context": "Ночной контекст",
                    "Smart Fit": "Персональный подбор",
                    "Best Seller": "Популярное",
                    "Ecosystem": "Экосистема"
                }
                source_ru = type_map.get(raw_type, raw_type)

                html_s = f"""
                <div class="tile-card" style="min-height: auto;">
                    <div class="tile-accent-secondary"></div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 250px;">
                            <div class="tile-header text-blue">🔮 {source_ru} (ИИ Рекомендация)</div>
                            <div class="tile-title">{prod_s.get('name', 'Продукт')}</div>
                            <div class="tile-desc" style="margin-bottom: 0;">{prod_s.get('desc', '')}</div>
                        </div>
                        <div style="flex: 1; min-width: 250px; background: #F0F7FF; border-radius: 12px; padding: 15px; border-left: 4px solid #2B2C84; align-self: center;">
                            <b style="color: #2B2C84; display: block; margin-bottom: 5px;">✨ Анализ потребностей:</b>
                            <span style="color: #1F2937; line-height: 1.5;">{marketing_msg}</span>
                        </div>
                    </div>
                </div>
                """
                st.markdown(html_s, unsafe_allow_html=True)

            # ==========================================
            # DEBUG
            # ==========================================
            st.write("")
            with st.expander("🛠 Технические детали (Debug)"):
                debug_info = rec.get('debug', {})
                stats = rec.get('stats', {})

                d1, d2, d3, d4 = st.columns(4)
                d1.metric("Сегмент", debug_info.get('segment', 'N/A'))
                d2.metric("Тип данных", "Двойник" if is_twin else "Реальные")
                d3.metric("Алгоритм", match_type.split()[0])
                d4.metric("Прогноз трат", f"{stats.get('projected_spend', 0)} ₽")

                st.divider()
                st.markdown("<h5 style='color: #2B2C84; margin-bottom: 10px;'>🧠 Логика принятия решений</h5>",
                            unsafe_allow_html=True)

                trend = debug_info.get('trend')
                trend_text = trend if trend else "Не выявлен"
                color_bg = "#F0F9EB" if trend else "#FFF0F0"

                # Улучшенные цвета для читаемости (Debug Block)
                if trend:
                    # Успех: Нежно-зеленый фон, Темно-зеленый текст
                    bg = "#E6FFFA"
                    border = "#047857"  # Emerald 700
                    text_color = "#064E3B"  # Emerald 900
                else:
                    # Нейтрально/Ошибка: Светло-серый фон, Темно-серый текст
                    bg = "#F3F4F6"
                    border = "#6B7280"
                    text_color = "#1F2937"

                trend_text = trend if trend else "Паттерн не выявлен"

                st.markdown(f"""
                <div style="background-color: {bg}; padding: 12px; border-radius: 8px; border-left: 5px solid {border}; margin-bottom: 12px;">
                    <b style="color: {text_color}; font-size: 0.9rem; display: block; margin-bottom: 4px;">Предиктивная модель (Markov):</b>
                    <span style="color: {text_color}; font-size: 0.9rem; line-height: 1.4;">
                    Последняя транзакция → Анализ цепочек → Следующий шаг: <br>
                    <span style="font-weight: 700; font-size: 1rem; color: {border};">{trend_text}</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

                if prod_s:
                    tags_str = ", ".join(rec.get('secondary', {}).get('product', {}).get('tags', []))
                    st.caption(f"Теги продукта: {tags_str}")

        else:
            st.error("Ошибка: Система вернула пустой ответ.")