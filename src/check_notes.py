#!/usr/bin/env python3
"""songsテーブルのノーツ数カラムを確認するスクリプト"""

import os
import sys
import requests
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
    print("Error: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")
    sys.exit(1)

# HTTP URLに変換
http_url = TURSO_DATABASE_URL.replace('libsql://', 'https://')

def execute_query(sql: str):
    """クエリを実行して結果を返す"""
    response = requests.post(
        http_url,
        headers={
            "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"statements": [sql]},
        timeout=30
    )
    response.raise_for_status()
    return response.json()

# ノーツ数カラムを含むサンプルデータを確認
print("=" * 80)
print("SONGS TABLE - NOTES COLUMNS CHECK")
print("=" * 80)

query = """
SELECT
    ID,
    曲名,
    `Shout×1白`,
    `Shout×1色`,
    `Beat×1白`,
    `Beat×1色`,
    `Melody×1白`,
    `Melody×1色`,
    `Shout×1.5白`,
    `Shout×1.5色`
FROM songs
LIMIT 10
"""

result = execute_query(query)

if result and len(result) > 0:
    data = result[0]
    if 'results' in data and 'rows' in data['results']:
        rows = data['results']['rows']
        columns = data['results']['columns']

        print(f"\nColumns: {columns}\n")
        print("Sample Data:")
        print("-" * 80)
        for row in rows:
            print(f"ID: {row[0]:3d} | 曲名: {row[1]:30s} | "
                  f"Shout×1白: {row[2]:4} | Shout×1色: {row[3]:4} | "
                  f"Beat×1白: {row[4]:4} | Beat×1色: {row[5]:4} | "
                  f"Melody×1白: {row[6]:4} | Melody×1色: {row[7]:4} | "
                  f"Shout×1.5白: {row[8]:4} | Shout×1.5色: {row[9]:4}")
        print("-" * 80)

        # null値が0に変換されているか確認
        print("\n✅ Checking for NULL values in notes columns...")
        has_null = False
        for row in rows:
            for i in range(2, 10):  # ノーツ数カラムのインデックス
                if row[i] is None:
                    has_null = True
                    print(f"⚠️  Found NULL in row ID={row[0]}, column={columns[i]}")

        if not has_null:
            print("✅ No NULL values found - all nulls converted to 0!")

print("\n" + "=" * 80)
