import pandas as pd
import numpy as np
import os
import shutil


INPUT_CSV = "clean_data/all_users_meta.csv"
OUTPUT_DIR = "clean_data/users_meta_chunks"
ROWS_PER_CHUNK = 5000000

print(f"Начинаем нарезку файла: {INPUT_CSV}")

if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)

cols = ['user_id', 'socdem_cluster', 'region']
chunk_idx = 0

try:
    for chunk in pd.read_csv(INPUT_CSV, usecols=cols, chunksize=ROWS_PER_CHUNK):
        chunk['user_id'] = chunk['user_id'].astype('int32')
        chunk['region'] = chunk['region'].fillna(-1).astype('int16')
        chunk['socdem_cluster'] = chunk['socdem_cluster'].fillna(-1).astype('int8')


        output_file = f"{OUTPUT_DIR}/part_{chunk_idx}.parquet"
        chunk.to_parquet(output_file, index=False, compression='brotli')

        print(f"Сохранен кусок {chunk_idx}: {output_file}")
        chunk_idx += 1

    print(f"Файл нарезан на {chunk_idx} частей в папке {OUTPUT_DIR}")
except Exception as e:
    print(f"Ошибка: {e}")