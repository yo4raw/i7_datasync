"""Brooches INSERT文テスト"""

import os
from dotenv import load_dotenv
import pandas as pd
from csv_fetcher import CSVFetcher
from validators import DataValidator
from transformers import DataTransformer
import math

load_dotenv()

# CSVを取得
csv_fetcher = CSVFetcher()
spreadsheet_id = os.getenv("SPREADSHEET_ID")
gid = 1087762308  # brooches

df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, gid, header=0)
print(f"Fetched {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")
print()

# 検証
validator = DataValidator()
valid_df, errors = validator.validate_brooches_data(df)
print(f"Valid: {len(valid_df)} rows")
print()

# 変換
transformer = DataTransformer()
transformed_df = transformer.transform_for_database(valid_df)

# INSERT文を構築（最初の1行だけ）
columns = list(transformed_df.columns)
quoted_columns = [f'`{col}`' for col in columns]

row = transformed_df.iloc[0]
values = []
for col in columns:
    val = row[col]
    if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
        values.append('NULL')
    elif isinstance(val, (int, float)):
        if math.isinf(val) or math.isnan(val):
            values.append('NULL')
        else:
            values.append(str(val))
    else:
        escaped_val = str(val).replace("'", "''")
        values.append(f"'{escaped_val}'")

stmt = f"INSERT INTO brooches ({', '.join(quoted_columns)}) VALUES ({', '.join(values)})"
print("First INSERT statement:")
print(stmt)
print()
print(f"Length: {len(stmt)} characters")
