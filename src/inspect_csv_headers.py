#!/usr/bin/env python3
"""CSVヘッダーを詳細に調査するスクリプト"""

import pandas as pd
import requests
from io import StringIO
from collections import Counter
from dotenv import load_dotenv

from constants import SPREADSHEET_ID, SONGS_GID

load_dotenv()

# CSV URL構築
url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SONGS_GID}"

print("=" * 80)
print("SONGS CSV HEADER INSPECTION")
print("=" * 80)

# CSV取得
response = requests.get(url, timeout=30)
response.encoding = 'utf-8'

# 最初の3行を表示
print("\n📄 First 3 rows of raw CSV:")
print("-" * 80)
lines = response.text.split('\n')[:3]
for i, line in enumerate(lines, 1):
    print(f"Row {i}: {line[:200]}...")  # 最初の200文字のみ
print("-" * 80)

# header=1でDataFrameを読み込み（songsテーブルと同じ）
df = pd.read_csv(StringIO(response.text), header=1)

print("\n🔍 Column Analysis:")
print("-" * 80)
print(f"Total columns: {len(df.columns)}")

# 重複カラム名を検出
column_counts = Counter(df.columns)
duplicates = {col: count for col, count in column_counts.items() if count > 1 or '.' in str(col)}

if duplicates:
    print(f"\n⚠️  Found {len(duplicates)} problematic columns:")
    for col, count in sorted(duplicates.items()):
        print(f"  - '{col}' (appears {count} times or has suffix)")
else:
    print("\n✅ No duplicate columns found")

# .1, .2などのサフィックスを持つカラムをリスト
suffixed_cols = [col for col in df.columns if '.' in str(col) and not col.startswith('×')]
if suffixed_cols:
    print(f"\n⚠️  Columns with pandas auto-generated suffixes (.1, .2, etc.):")
    for col in suffixed_cols:
        # 元のカラム名を推定
        base_name = col.rsplit('.', 1)[0]
        print(f"  - '{col}' (base: '{base_name}')")

        # 両方のカラムのデータを比較
        if base_name in df.columns:
            original = df[base_name].head(3)
            duplicate = df[col].head(3)
            print(f"    Original: {list(original)}")
            print(f"    Duplicate: {list(duplicate)}")

            # データが同じかチェック
            if original.equals(duplicate):
                print("    ⚠️  Data is IDENTICAL - can safely drop duplicate")
            else:
                print("    ⚠️  Data is DIFFERENT - need to investigate meaning")

# 全カラム名をリスト
print(f"\n📝 All column names (first 30):")
print("-" * 80)
for i, col in enumerate(df.columns[:30], 1):
    col_str = str(col)
    if '.' in col_str and not col_str.startswith('×'):
        print(f"{i:3d}. '{col}' ⚠️")
    else:
        print(f"{i:3d}. '{col}'")

if len(df.columns) > 30:
    print(f"... and {len(df.columns) - 30} more columns")

print("\n" + "=" * 80)
