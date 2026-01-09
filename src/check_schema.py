#!/usr/bin/env python3
"""Turso DBのスキーマを確認するスクリプト"""

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

# songsテーブルのスキーマを確認
print("=" * 60)
print("SONGS TABLE SCHEMA")
print("=" * 60)

schema_result = execute_query("PRAGMA table_info(songs)")
print(f"\nRaw response: {schema_result}\n")

if schema_result and len(schema_result) > 0:
    result = schema_result[0]
    if 'results' in result and 'rows' in result['results']:
        rows = result['results']['rows']
        columns = result['results']['columns']

        print(f"Columns: {columns}\n")
        print("Schema:")
        print("-" * 60)
        for row in rows:
            print(f"Column: {row[1]:20s} Type: {row[2]:10s} NotNull: {row[3]} PK: {row[5]}")
        print("-" * 60)

# CREATE TABLE文を確認
print("\n" + "=" * 60)
print("CREATE TABLE STATEMENT")
print("=" * 60)

create_result = execute_query("SELECT sql FROM sqlite_master WHERE type='table' AND name='songs'")
print(f"\nRaw response: {create_result}\n")

if create_result and len(create_result) > 0:
    result = create_result[0]
    if 'results' in result and 'rows' in result['results']:
        rows = result['results']['rows']
        if rows and len(rows) > 0:
            print("CREATE TABLE SQL:")
            print("-" * 60)
            print(rows[0][0])
            print("-" * 60)

# サンプルデータのID列の値を確認
print("\n" + "=" * 60)
print("SAMPLE DATA (First 5 rows)")
print("=" * 60)

sample_result = execute_query("SELECT ID, 分類, アーティスト名 FROM songs LIMIT 5")
print(f"\nRaw response: {sample_result}\n")

if sample_result and len(sample_result) > 0:
    result = sample_result[0]
    if 'results' in result and 'rows' in result['results']:
        rows = result['results']['rows']
        columns = result['results']['columns']

        print(f"Columns: {columns}\n")
        print("Data:")
        print("-" * 60)
        for row in rows:
            print(f"ID: {row[0]} (type: {type(row[0]).__name__}), 分類: {row[1]}, アーティスト名: {row[2]}")
        print("-" * 60)

print("\n✅ Schema check complete")
