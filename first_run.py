from engine import RecommendationEngine

USERS_PATH = "clean_data/users_fast.parquet"
TRANS_PATH = "clean_data/trans_fast.parquet"
engine = RecommendationEngine(USERS_PATH,TRANS_PATH)
first_user_id = 1923871
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")
first_user_id = 25282222
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")
first_user_id = 777
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")
first_user_id = 1162
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")
first_user_id = 99999999999
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")
first_user_id = 8715263
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")
first_user_id = 15992
rec = engine.recommend(first_user_id)
if rec:
    print(rec)
else:
    print("❌ Юзер не найден или ошибка")