from engine import RecommendationEngine

USERS_PATH = "clean_data/users_clustered.csv"
TRANS_PATH = "clean_data/payments_ready_markov.zip"
engine = RecommendationEngine(USERS_PATH,TRANS_PATH)
first_user_id = 16466
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