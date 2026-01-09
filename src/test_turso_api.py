"""Turso HTTP APIのテストスクリプト"""

import os
import requests
import json
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# 環境変数から接続情報を取得
database_url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

print(f"Database URL: {database_url}")
print(f"Auth Token: {auth_token[:20]}..." if auth_token else "None")

# libsql:// を https:// に変換
if database_url.startswith("libsql://"):
    host = database_url.replace("libsql://", "")
    http_url = f"https://{host}"
else:
    http_url = database_url

print(f"HTTP URL: {http_url}")
print()

# テスト1: 接続テスト (SELECT 1)
print("=== Test 1: Connection Test (SELECT 1) ===")
response = requests.post(
    http_url,
    headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    },
    json={"statements": ["SELECT 1"]},
    timeout=10
)
print(f"Status Code: {response.status_code}")
print(f"Response Type: {type(response.json())}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
print()

# テスト2: テーブル作成とデータ挿入
print("=== Test 2: CREATE TABLE and INSERT ===")
response = requests.post(
    http_url,
    headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    },
    json={
        "statements": [
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)",
            "DELETE FROM test_table",
            "INSERT INTO test_table (id, name) VALUES (1, 'test1')",
            "INSERT INTO test_table (id, name) VALUES (2, 'test2')"
        ]
    },
    timeout=10
)
print(f"Status Code: {response.status_code}")
print(f"Response Type: {type(response.json())}")
result = response.json()
print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
print()

# レスポンスの構造を詳しく調べる
print("=== Response Structure Analysis ===")
if isinstance(result, list):
    print(f"Response is a list with {len(result)} elements")
    for i, item in enumerate(result):
        print(f"  Element {i}: type={type(item)}, keys={list(item.keys()) if isinstance(item, dict) else 'N/A'}")
        if isinstance(item, dict):
            print(f"    Content: {json.dumps(item, indent=4, ensure_ascii=False)}")
elif isinstance(result, dict):
    print(f"Response is a dict with keys: {list(result.keys())}")
    print(f"Content: {json.dumps(result, indent=2, ensure_ascii=False)}")
else:
    print(f"Response is of type: {type(result)}")
print()

# テスト3: SELECTで確認
print("=== Test 3: SELECT to verify ===")
response = requests.post(
    http_url,
    headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    },
    json={"statements": ["SELECT * FROM test_table"]},
    timeout=10
)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
