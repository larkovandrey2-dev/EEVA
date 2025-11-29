import streamlit as st
from engine import RecommendationEngine

USERS_PATH = "clean_data/users_fast.parquet"
TRANS_PATH = "clean_data/trans_fast.parquet"

# --- Настройка страницы ---
st.set_page_config(page_title="PSB Smart Offers", layout="centered")


@st.cache_resource(show_spinner="Загрузка AI ядра...")
def get_engine():
    return RecommendationEngine(USERS_PATH, TRANS_PATH)


try:
    engine = get_engine()
    data_loaded = True
except Exception as e:
    st.error(f"Engine Load Error: {e}")
    data_loaded = False


st.markdown("""
<style>
    /* === 1. ИСПРАВЛЕНИЕ ИНПУТА (ЧЕРНЫЙ ТЕКСТ И КУРСОР) === */
    .stTextInput > div > div > input {
        color: #000000 !important;          /* Черный текст */
        caret-color: #000000 !important;    /* Черный курсор */
        background-color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
        font-weight: 500 !important;
        -webkit-text-fill-color: #000000 !important; /* Фикс для Safari/Chrome */
    }
    .stTextInput > div > div > input::placeholder {
        color: #6B7280 !important; /* Серый плейсхолдер */
        opacity: 1 !important;
    }

    /* === 2. DEBUG ПАНЕЛЬ (ЧЕТКОСТЬ) === */
    .streamlit-expanderHeader {
        background-color: #F0F7FF !important;
        color: #2B2C84 !important;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
    }
    .streamlit-expanderHeader p { 
        color: #2B2C84 !important; 
        font-weight: 700 !important; 
        font-size: 1rem !important; 
    }
    .streamlit-expanderContent {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB;
        border-top: none;
        color: #000000 !important;
    }

    /* === 3. МЕТРИКИ (ПОПРАВИЛ ШРИФТ) === */
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
        color: #2B2C84 !important;
        font-weight: 700 !important;
        /* Убрал Montserrat, чтобы цифры не плыли */
        font-family: sans-serif !important; 
    }
    [data-testid="stMetricLabel"] { 
        color: #374151 !important;
        font-size: 0.8rem !important; 
        font-weight: 600;
    }

    /* === ОСТАЛЬНОЕ === */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Verdana:wght@400;700&display=swap');

    h1, h2, h3, .stButton > button { font-family: 'Montserrat', sans-serif !important; font-weight: 600; }
    p, div, label { font-family: 'Verdana', sans-serif !important; }

    .stApp, .main .block-container { background-color: #FFFFFF !important; color: #000000 !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .main .block-container { padding-top: 2rem !important; }

    .stTextInput > label { color: #2B2C84 !important; font-weight: 700 !important; }

    .stButton > button {
        background-color: #EA5614 !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton > button:hover { background-color: #C1440E !important; }
</style>
""", unsafe_allow_html=True)



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
            # --- 1. СТАТУС КЛИЕНТА ---
            is_twin = rec.get('is_twin', False)
            match_type = rec.get('match_type', 'Real Data')
            segment = rec.get('segment_name', 'Unknown')

            if is_twin:
                st.info(f"**Новый клиент** (Cold Start). Профиль: **{match_type}**. Сегмент: **{segment}**")
            else:
                st.success(f"Клиент найден в базе. Сегмент: **{segment}**")

            # --- 2. КАРТОЧКИ ---
            col_p, col_s = st.columns(2)

            # Primary (Стратегия)
            with col_p:
                p_data = rec.get('primary', {})
                prod = p_data.get('product', {})

                if prod:
                    html_p = f"""
                    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #D1D5DB; border-top: 6px solid #EA5614; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                        <div style="color: #EA5614; font-weight: 800; font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
                            🔥 Стратегическое
                        </div>
                        <div style="font-family: 'Montserrat', sans-serif; font-size: 1.3em; font-weight: 700; color: #111827; margin-bottom: 10px; line-height: 1.2;">
                            {prod.get('name', 'Продукт')}
                        </div>
                        <div style="font-size: 0.95em; color: #374151; margin-bottom: 20px; line-height: 1.5; font-weight: 400;">
                            {prod.get('desc', '')}
                        </div>
                        <div style="font-size: 0.9em; color: #000000; background: #FFF5F0; padding: 12px; border-radius: 6px; border-left: 4px solid #EA5614;">
                            <b style="color: #EA5614;">Обоснование:</b><br>{p_data.get('desc', 'Базовый продукт для сегмента')}
                        </div>
                    </div>
                    """
                    st.markdown(html_p, unsafe_allow_html=True)
                else:
                    st.info("Нет предложений")

            # Secondary (Тактика/AI)
            with col_s:
                s_data = rec.get('secondary', {})
                prod_s = s_data.get('product', {})

                if prod_s:
                    marketing_msg = s_data.get('marketing_msg', s_data.get('reason', ''))
                    source_type = s_data.get('type', 'Recommendation').upper()

                    html_s = f"""
                    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #D1D5DB; border-top: 6px solid #2B2C84; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
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
                    st.markdown("""
                    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #E5E7EB; height: 100%; display: flex; align-items: center; justify-content: center; color: #646872;">
                        <i>Дополнительных рекомендаций нет</i>
                    </div>
                    """, unsafe_allow_html=True)

            # --- 3. DEBUG BLOCK ---
            st.write("")
            with st.expander("🛠 Как это работает? (Debug & Logic Trace)"):

                debug_info = rec.get('debug', {})
                stats = rec.get('stats', {})

                # Метрики
                d1, d2, d3, d4 = st.columns(4)
                d1.metric("Segment", debug_info.get('segment', 'N/A'))
                d2.metric("Source", "Twin" if rec.get('is_twin') else "Real")
                d3.metric("Match", rec.get('match_type', '-').split()[
                    -1])  # Берем только последнее слово (Unknown / Profile), чтобы влезло
                d4.metric("Spend", f"{stats.get('projected_spend', 0)} ₽")

                st.divider()
                st.markdown("<h5 style='color: #2B2C84; margin-bottom: 10px;'>🧠 AI Logic Trace</h5>",
                            unsafe_allow_html=True)

                # Логика Маркова (Визуализация)
                trend = debug_info.get('trend')
                last_cat = rec["last_cat"] if rec["last_cat"] is not None else "Unknown"

                if trend:
                    st.markdown(f"""
                    <div style="background-color: #F0F9EB; padding: 12px; border-radius: 6px; border-left: 5px solid #4E621C; margin-bottom: 10px;">
                        <b style="color: #000; font-size: 0.9rem;">Markov Prediction:</b><br>
                        <span style="color: #374151; font-size: 0.9rem;">
                        Последняя транзакция → <span style="color: #15803d; font-weight: 700;">Сработал паттерн</span> → 
                        Тренд: <span style="background-color: #dcfce7; padding: 2px 6px; border-radius: 4px; color: #166534; font-weight: 700;">{trend}</span>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #FEF2F2; padding: 12px; border-radius: 6px; border-left: 5px solid #EF4444; margin-bottom: 10px;">
                        <b style="color: #000; font-size: 0.9rem;">Markov Prediction:</b><br>
                        <span style="color: #374151; font-size: 0.9rem;">Нет явного паттерна поведения.</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Теги
                sec_prod = rec.get('secondary', {}).get('product', {})
                if sec_prod:
                    tags = sec_prod.get('tags', [])
                    # Красивые теги
                    tags_html = "".join([
                                            f"<span style='background:#E5E7EB; padding:2px 8px; border-radius:12px; margin-right:5px; font-size:0.8rem; color:#374151;'>#{t}</span>"
                                            for t in tags])
                    st.markdown(f"<div style='margin-top:5px;'><b>Matched Tags:</b> {tags_html}</div>",
                                unsafe_allow_html=True)

        else:
            st.error("Ошибка: Engine вернул пустой ответ.")