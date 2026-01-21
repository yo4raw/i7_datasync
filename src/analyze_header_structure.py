#!/usr/bin/env python3
"""2行ヘッダー構造を分析するスクリプト"""

import pandas as pd
import requests
from io import StringIO
from dotenv import load_dotenv

from constants import SPREADSHEET_ID, SONGS_GID

load_dotenv()

# CSV URL構築
url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SONGS_GID}"

print("=" * 80)
print("SONGS CSV 2-ROW HEADER STRUCTURE ANALYSIS")
print("=" * 80)

# CSV取得
response = requests.get(url, timeout=30)
response.encoding = 'utf-8'

# Row 1とRow 2を別々に読み込み
lines = response.text.split('\n')
row1_values = lines[0].split(',')
row2_values = lines[1].split(',')

print(f"\n📊 Header Structure:")
print(f"  Row 1 (Categories): {len(row1_values)} columns")
print(f"  Row 2 (Column Names): {len(row2_values)} columns")

# Row 1とRow 2をマッピング
print(f"\n🔍 Combined Header Mapping (first 40 columns):")
print("-" * 80)

current_category = ""
for i in range(min(40, len(row1_values))):
    cat = row1_values[i].strip()
    name = row2_values[i].strip() if i < len(row2_values) else ""

    # カテゴリーが空でない場合は更新
    if cat:
        current_category = cat

    # 組み合わせカラム名を生成
    if current_category and name:
        combined = f"{current_category}_{name}"
    elif name:
        combined = name
    else:
        combined = "(empty)"

    print(f"{i+1:3d}. Cat: '{current_category:40s}' | Name: '{name:20s}' → '{combined}'")

# 重複カラム名を検出して、それぞれのカテゴリーを表示
print(f"\n⚠️  Duplicate Column Names with Categories:")
print("-" * 80)

from collections import defaultdict
name_to_categories = defaultdict(list)

current_category = ""
for i in range(len(row2_values)):
    cat = row1_values[i].strip() if i < len(row1_values) else ""
    name = row2_values[i].strip()

    if cat:
        current_category = cat

    if name:
        name_to_categories[name].append((i, current_category))

# 重複のみ表示
for name, occurrences in sorted(name_to_categories.items()):
    if len(occurrences) > 1:
        print(f"\n'{name}' appears {len(occurrences)} times:")
        for idx, cat in occurrences:
            print(f"  Column {idx+1:3d}: Category '{cat}'")

print("\n" + "=" * 80)
