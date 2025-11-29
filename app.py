import streamlit as st
from engine import RecommendationEngine

# --- Настройка страницы ---
st.set_page_config(page_title="PSB Smart Offers", layout="centered")


# --- Инициализация ---
@st.cache_resource
def get_engine():
    USERS_PATH = "clean_data/users_fast.parquet"
    TRANS_PATH = "clean_data/trans_fast.parquet"
    return RecommendationEngine(USERS_PATH, TRANS_PATH)


try:
    engine = get_engine()
    data_loaded = True
except Exception as e:
    st.error(f"Engine Load Error: {e}")
    data_loaded = False

# ==========================================
# CSS СТИЛИ
# ==========================================
st.markdown("""
<style>
    /* === ФИКСЫ DEBUG ПАНЕЛИ === */
    .streamlit-expanderHeader { background-color: #F0F7FF !important; color: #2B2C84 !important; border: 1px solid #D1D5DB; border-radius: 8px; }
    .streamlit-expanderHeader p { color: #2B2C84 !important; font-weight: 700; font-size: 1rem; }
    .streamlit-expanderContent { background-color: #FFFFFF !important; border: 1px solid #D1D5DB; border-top: none; color: #000000 !important; }

    /* === ОБЩИЕ === */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Verdana:wght@400;700&display=swap');
    h1, h2, h3, .stButton > button, [data-testid="stMetricValue"] { font-family: 'Montserrat', sans-serif !important; }
    p, div, label, input { font-family: 'Verdana', sans-serif !important; }

    .stApp, .main .block-container { background-color: #FFFFFF !important; color: #000000 !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .main .block-container { padding-top: 2rem !important; }

    /* === ИНПУТЫ === */
    .stTextInput > div > div > input { background-color: #FFFFFF !important; border: 1px solid #4B5563 !important; color: #000000 !important; caret-color: #000000 !important; }
    .stTextInput > div > div > input:focus { border-color: #EA5614 !important; border-width: 2px; }
    .stTextInput > label { color: #2B2C84 !important; font-weight: 700 !important; }

    /* === КНОПКА === */
    .stButton > button { background-color: #EA5614 !important; color: white !important; border-radius: 8px; border: none; font-weight: 600; }
    .stButton > button:hover { background-color: #C1440E !important; }

    /* === МЕТРИКИ === */
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; color: #2B2C84 !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #374151 !important; font-size: 0.85rem !important; font-weight: 600; }

    /* === ТАБЫ (ВКЛАДКИ) === */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: nowrap;
        background-color: #F3F4F6;
        border-radius: 4px 4px 0 0;
        color: #4B5563;
        font-weight: 600;
        border: 1px solid #E5E7EB;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFF5F0 !important;
        color: #EA5614 !important;
        border-color: #EA5614 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# UI ЧАСТЬ
# ==========================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("PSB_logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #2B2C84'>PSB BANK</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #374151;'>Рекомендательная система</h3>", unsafe_allow_html=True)

# Поиск
user_input = st.text_input("Введите User ID", placeholder="Например: 16466")

if st.button("Получить рекомендации"):
    if not user_input:
        st.warning("Введите user_id!")
    else:
        try:
            user_id = int(user_input.strip())
            rec = engine.recommend(user_id)
        except ValueError:
            st.error("User ID должен быть числом.")
            st.stop()

        if rec:
            # 1. СТАТУС
            is_twin = rec.get('is_twin', False)
            match_type = rec.get('match_type', 'Real Data')
            segment = rec.get('segment_name', 'Unknown')

            if is_twin:
                st.info(f"**Новый клиент** (Cold Start). Профиль: **{match_type}**. Сегмент: **{segment}**")
            else:
                st.success(f"Клиент найден в базе. Сегмент: **{segment}**")

            # 2. КАРТОЧКИ
            col_p, col_s = st.columns(2)

            # --- PRIMARY CARD (С ТАБАМИ) ---
            with col_p:
                primary_list = rec.get('primary', [])
                # Создаем вкладки: Вариант 1, Вариант 2
                tab1, tab2 = st.tabs(["Вариант №1", "Вариант №2"])


                # Функция отрисовки карточки
                def draw_primary_card(p_item, badge_text="🔥 Стратегическое"):
                    prod = p_item.get('product', {})
                    html = f"""
                    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 0 12px 12px 12px; border: 1px solid #D1D5DB; border-top: 6px solid #EA5614; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-top: -16px;">
                        <div style="color: #EA5614; font-weight: 800; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
                            {badge_text} 
                        </div>
                        <div style="font-family: 'Montserrat', sans-serif; font-size: 1.3em; font-weight: 700; color: #111827; margin-bottom: 10px; line-height: 1.2;">
                            {prod.get('name', 'Продукт')}
                        </div>
                        <div style="font-size: 0.95em; color: #374151; margin-bottom: 20px; line-height: 1.5; font-weight: 400;">
                            {prod.get('desc', '')}
                        </div>
                        <div style="font-size: 0.9em; color: #000000; background: #FFF5F0; padding: 12px; border-radius: 6px; border-left: 4px solid #EA5614;">
                            <b style="color: #EA5614;">Обоснование:</b><br>Базовый продукт для вашего профиля
                        </div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)


                with tab1:
                    if len(primary_list) > 0:
                        draw_primary_card(primary_list[0])
                    else:
                        st.info("Нет предложений")

                with tab2:
                    if len(primary_list) > 1:
                        draw_primary_card(primary_list[1], badge_text="⚡ Альтернатива")
                    else:
                        st.info("Нет альтернатив")

            # --- SECONDARY CARD ---
            with col_s:
                s_data = rec.get('secondary', {})
                prod_s = s_data.get('product', {})

                if prod_s:
                    marketing_msg = s_data.get('marketing_msg', s_data.get('reason', ''))
                    source_type = s_data.get('type', 'Recommendation').upper()

                    # Отступ сверху, чтобы выровнять с табами визуально
                    st.write("")
                    st.write("")
                    # Можно добавить пустой div height, если табы высокие, но обычно норм

                    html_s = f"""
                    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #D1D5DB; border-top: 6px solid #2B2C84; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-top: 15px;">
                        <div style="color: #2B2C84; font-weight: 800; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
                            {source_type}
                        </div>
                        <div style="font-family: 'Montserrat', sans-serif; font-size: 1.3em; font-weight: 700; color: #111827; margin-bottom: 10px; line-height: 1.2;">
                            {prod_s.get('name', 'Продукт')}
                        </div>
                        <div style="font-size: 0.95em; color: #374151; margin-bottom: 20px; line-height: 1.5; font-weight: 400;">
                            {prod_s.get('desc', '')}
                        </div>
                        <div style="font-size: 0.9em; color: #000000; background: #F0F7FF; padding: 12px; border-radius: 6px; border-left: 4px solid #2B2C84;">
                            <b style="color: #2B2C84;">AI Инсайт:</b><br>{marketing_msg}
                        </div>
                    </div>
                    """
                    st.markdown(html_s, unsafe_allow_html=True)
                else:
                    st.markdown("Нет доп. рекомендаций")

            # 3. DEBUG BLOCK
            st.write("")
            with st.expander("🛠 Как это работает? (Debug & Logic Trace)"):
                debug_info = rec.get('debug', {})
                stats = rec.get('stats', {})

                d1, d2, d3, d4 = st.columns(4)
                d1.metric("Segment", debug_info.get('segment', 'N/A'))
                d2.metric("Source", "Twin" if rec.get('is_twin') else "Real")
                d3.metric("Match", rec.get('match_type', '-').split()[-1])
                d4.metric("Spend", f"{stats.get('projected_spend', 0)} ₽")

                st.divider()
                st.markdown("<h5 style='color: #2B2C84; margin-bottom: 10px;'>🧠 AI Logic Trace</h5>",
                            unsafe_allow_html=True)

                trend = debug_info.get('trend')
                if trend:
                    st.markdown(f"""
                    <div style="background-color: #F0F9EB; padding: 10px; border-radius: 6px; border-left: 4px solid #4E621C; margin-bottom: 10px;">
                        <b style="color: #000;">Markov Prediction:</b><br>
                        <span style="color: #1F2937;">Последняя транзакция -> Паттерн -> Тренд: <b>{trend}</b></span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #FFF0F0; padding: 10px; border-radius: 6px; border-left: 4px solid #EA5614; margin-bottom: 10px;">
                        <b style="color: #000;">Markov Prediction:</b><br>
                        <span style="color: #1F2937;">Нет явного паттерна.</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Показываем продукты из primary списка в дебаге
                st.caption(f"Selected Primary: {[p['product']['name'] for p in rec.get('primary', [])]}")

        else:
            st.error("Ошибка: Engine вернул пустой ответ.")