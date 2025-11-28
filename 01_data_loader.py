import pandas as pd
import glob
import os

RAW_DIR = "raw_data"
CLEAN_DIR = "clean_data"
os.makedirs(CLEAN_DIR, exist_ok=True)

# 1. Users processing
user_files = glob.glob(f"{RAW_DIR}/*user*.pq") + glob.glob(f"{RAW_DIR}/*user*.csv")
if not user_files:
    raise FileNotFoundError("Users file not found in raw_data")

try:
    if user_files[0].endswith('.csv'):
        df_users = pd.read_csv(user_files[0])
    else:
        df_users = pd.read_parquet(user_files[0])
except:
    df_users = pd.read_parquet(user_files[0], engine='fastparquet')

df_users.to_csv(f"{CLEAN_DIR}/all_users_meta.csv", index=False)

train_users = df_users.sample(n=10000, random_state=42)
train_ids = set(train_users['user_id'].values)
train_users.to_csv(f"{CLEAN_DIR}/train_users_10k.csv", index=False)

# 2. Payments processing
pay_files = glob.glob(f"{RAW_DIR}/*pay*")
chunks = []

for f in pay_files:
    try:
        if f.endswith('.csv'):
            df = pd.read_csv(f)
        else:
            df = pd.read_parquet(f)

        df = df[df['user_id'].isin(train_ids)]
        if 'amount' in df.columns:
            df['price'] = df['amount']
        chunks.append(df)
    except:
        pass

if chunks:
    full_pay = pd.concat(chunks, ignore_index=True)
    full_pay.to_csv(f"{CLEAN_DIR}/payments_step1.csv", index=False)
    print("Step 1 Done.")
else:
    print("No payment files found.")