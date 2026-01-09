# Project Structure

## Organization Philosophy

**Layered by Responsibility**: コンポーネントを技術的責任で分離

- データソース層、ビジネスロジック層、永続化層の3層構造
- 各層は独立してテスト・メンテナンス可能
- 単一責任原則に従った明確な境界

## Directory Patterns

### Source Code (`/src/` or root)
**Purpose**: Python実装コード（layered architecture）
**Pattern**:
```
src/
├── csv_fetcher.py      # Data Source Layer
├── validators.py       # Business Logic Layer
├── transformers.py     # Business Logic Layer
├── orchestrator.py     # Business Logic Layer
├── db_client.py        # Data Persistence Layer
└── main.py             # Entry point
```

各ファイルは対応する層の責任を持つ。

### Configuration (`/.env`, `/.env.example`)
**Purpose**: 環境変数設定
**Pattern**:
- `.env`: 実際の設定（gitignore済み、各開発者がローカルで作成）
- `.env.example`: テンプレート（バージョン管理対象、機密情報なし）

**Principle**: GitHub Secretsと同一の環境変数名を使用

### Docker (`/docker-compose.yml`, `/Dockerfile`)
**Purpose**: コンテナ定義
**Pattern**: シンプルなPython実行環境、環境変数注入

### Kiro Specs (`.kiro/specs/`)
**Purpose**: 機能仕様と設計ドキュメント
**Pattern**: 各機能ごとにディレクトリ（例: `github-spreadsheet-sync/`）

## Naming Conventions

- **Files**: `snake_case.py` (Python標準)
- **Classes**: `PascalCase` (例: `CSVFetcher`, `DatabaseClient`)
- **Functions/Variables**: `snake_case` (例: `fetch_csv_as_dataframe`)
- **Constants**: `UPPER_SNAKE_CASE` (例: `SONGS_GID = 1083871743`)

## Import Organization

```python
# Standard library
import os
from typing import Dict, List

# Third-party
import pandas as pd
import requests
from libsql_client import Client

# Local modules
from csv_fetcher import CSVFetcher
from db_client import DatabaseClient
```

**Order**: 標準ライブラリ → サードパーティ → ローカルモジュール

## Code Organization Principles

### Layer Independence
各層は下位層にのみ依存:
```
Data Source Layer (独立)
         ↑
Business Logic Layer
         ↑
Data Persistence Layer
```

### Configuration via Environment
ハードコードせず環境変数を使用:
```python
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
```

GIDなどの定数は例外（コード内定義）。

### Transaction Boundaries
データ同期は単一トランザクション内で完結:
```python
with db_client.transaction():
    db_client.delete_all(table)
    db_client.insert_batch(table, data)
```

### Error Propagation
各層でエラーをキャッチし、適切にログ記録後に上位層へ伝播。

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
