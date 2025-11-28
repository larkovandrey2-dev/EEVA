import streamlit as st
from engine import RecommendationEngine
from products import TREND_MAPPING, CONTEXT_OFFERS


engine = RecommendationEngine("clean_data/users_clustered.csv")


st.markdown("""
<style>
    /* Шрифты: Montserrat как аналог Gilroy + Verdana fallback */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Verdana:wght@400;700&display=swap');

    /* Основные шрифты */
    h1, h2, h3, .stButton > button {
        font-family: 'Montserrat', Verdana, sans-serif !important;
        font-weight: 600;
    }
    p, .stTextInput label, .stMarkdown, .stDataFrame {
        font-family: 'Verdana', Montserrat, sans-serif !important;
        font-weight: 400;
    }
    .stSuccess, .stWarning {
        font-family: 'Montserrat', Verdana, sans-serif !important;
        font-weight: 700;
    }

    /* Фон: белый, текст тёмный */
    .stApp, .main .block-container, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Поле ввода: белый фон, тёмный текст/лейбл/плейсхолдер/курсор */
    .stTextInput > div > div > input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 5px;
        caret-color: #000000 !important;  /* Курсор чёрный */
        outline: none !important;  /* Убираем дефолтный outline */
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF6200 !important;  /* Оранжевый фокус */
        outline: 2px solid #FF6200 !important;  /* Видимый обвод для курсора */
        caret-color: #000000 !important;  /* Курсор чёрный на фокусе */
    }
    .stTextInput > div > div > input::placeholder {
        color: #000000 !important;
        opacity: 0.6 !important;
    }
    .stTextInput > label {
        color: #374151 !important;
    }

    /* Скроллбар в поле: тёмный */
    .stTextInput > div > div > input::-webkit-scrollbar {
        width: 8px;
    }
    .stTextInput > div > div > input::-webkit-scrollbar-track {
        background: #FFFFFF !important;
    }
    .stTextInput > div > div > input::-webkit-scrollbar-thumb {
        background: #9CA3AF !important;
        border-radius: 4px;
    }
    .stTextInput > div > div > input::-webkit-scrollbar-thumb:hover {
        background: #6B7280 !important;
    }

    /* Кнопка: оранжевая */
    .stButton > button {
        background-color: #FF6200 !important;
        color: #FFFFFF !important;
        border-radius: 10px;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #E55A00 !important;
    }

    /* Заголовки: чёрный, центр */
    h1 {
        text-align: center !important;
        color: #000000 !important;
        text-shadow: none;
        white-space: normal !important;
        word-wrap: break-word !important;
        line-height: 1.3;
        font-size: 2em;
        margin-bottom: 1rem;
    }

    /* Таблица: белый фон, тёмный текст */
    .stDataFrame {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    .stDataFrame thead tr th {
        background-color: #F9FAFB !important;
        color: #000000 !important;
        border-bottom: 1px solid #D1D5DB !important;
    }
    .stDataFrame tbody tr td {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-color: #D1D5DB !important;
    }

    /* Уведомления: светлые, тёмный текст (усиленный фикс для warning) */
    .stAlert, .stWarning {  /* Основной класс для warning */
        background-color: #FFF3CD !important;  /* Жёлтый фон */
        color: #000000 !important;  /* Чёрный текст */
        border-left: 4px solid #FF6200 !important;
        border-radius: 5px;
    }
    .stAlert > div, .stWarning > div, .stWarning .element-container {  /* Вложенные div */
        color: #000000 !important;  /* Текст внутри чёрный */
    }
    .stInfo {
        background-color: #D1ECF1 !important;
        color: #000000 !important;
        border-left: 4px solid #17A2B8 !important;
        border-radius: 5px;
    }
    .stSuccess {
        background-color: #D4EDDA !important;
        color: #000000 !important;
        border-left: 4px solid #28A745 !important;
        border-radius: 5px;
    }
    .stError {
        background-color: #F8D7DA !important;
        color: #000000 !important;
        border-left: 4px solid #DC3545 !important;
        border-radius: 5px;
    }
    /* Общий текст в уведомлениях */
    .stAlert > div > div, .stWarning > div > div {
        color: #000000 !important;
    }

    /* Лого: центр */
    .logo-container {
        text-align: center;
        margin: 1rem auto;
        display: block;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# UI
col1, col2, col3 = st.columns([1, 2, 1]) # Центрированный логотип
with col2:
    st.image("PSB_logo.png", width=540,)

st.title("Рекомендательная система банковских продуктов")


user_id = st.text_input("Введите User ID. Например: 123")

if st.button("Получить рекомендации"):
    if not user_id:
        st.warning("Введите user_id!")
    else:
        try:
            user_id_int = int(user_id.strip())  # Преобразование в int, убираем пробелы
        except ValueError:
            st.error("User ID должен быть числом (напр. 1228, без кавычек).")
            st.stop()  # Остановка, если не число

        recommendation = engine.recommend(user_id_int)  # Передаём int в recommend
        if recommendation:
            st.success(f"Рекомендации для {user_id}:")
            st.write(f"**Сегмент:** {recommendation['segment_name']}")
            st.write(f"**Кластер ID:** {recommendation['cluster_id']}")
            st.write(f"**Статистика:** Реальные траты за 48ч: {recommendation['stats']['real_48h_spend']} руб. | Прогноз на месяц: {recommendation['stats']['projected_month_spend']} руб.")
            st.write(f"**Причина:** {recommendation['reason']}")

            # Продукты из PSB_PRODUCTS (через engine)
            product = recommendation['product']
            st.subheader("Рекомендованные продукты:")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**День:**")
                st.write(f"**{product['default']['name']}**")
                st.write(product['default']['desc'])
            with col2:
                st.write("**Ночь:**")
                st.write(f"**{product['night']['name']}**")
                st.write(product['night']['desc'])
            with col3:
                st.write("**Инвестиции:**")
                st.write(f"**{product['invest']['name']}**")
                st.write(product['invest']['desc'])

            # LLM-промпт из engine
            # llm_prompt = engine.get_llm_prompt(recommendation)
            # st.subheader("LLM-промпт для генерации ответа:")
            # st.text_area("", llm_prompt, height=150, disabled=True)

            # Спецпредложение из CONTEXT_OFFERS по cluster_id
            cluster_key = recommendation['cluster_id']
            # Маппинг cluster_id к тренду (обратный TREND_MAPPING)
            reverse_trend = {v: k for k, v in TREND_MAPPING.items()}
            trend = reverse_trend.get(cluster_key)
            if trend:
                offer = CONTEXT_OFFERS.get(TREND_MAPPING[trend], {})
                if offer:
                    st.subheader("Спецпредложение по тренду:")
                    st.write(f"**Тренд:** {trend}")
                    st.write(f"**{offer['name']}** - {offer['desc']}")

        else:
            st.error("Пользователь не найден в CSV. Проверь user_id в users_clustered.csv.")

