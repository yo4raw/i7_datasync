# i7_datasync

アイドリッシュセブンのゲームデータ（楽曲、カード、固有ブローチ）をGoogle SpreadsheetからTursoデータベースへ自動同期するGitHub Actionsワークフロー。

## 概要

このプロジェクトは、公開されているGoogle SpreadsheetのCSVエクスポートURLから3種類のゲームデータを取得し、Tursoデータベースに自動的に同期します。

### 主な機能

- **CSV Export Access**: Google Spreadsheetの公開CSVエクスポートURLから直接データ取得（Google Sheets API不要）
- **Full Sync Pattern**: シンプルで確実な全削除→全挿入パターンによるデータ同期
- **Automated Scheduling**: GitHub Actionsで1時間ごとに自動実行
- **Environment Parity**: Docker開発環境と本番環境でTursoを統一使用

## 技術スタック

- **言語**: Python 3.11+
- **ランタイム**: Docker 24+ / docker-compose 2.0+
- **データベース**: Turso (libSQL)
- **主要ライブラリ**:
  - pandas 2.0+ (CSVデータ処理)
  - requests 2.31+ (HTTP取得)
  - libsql-client 0.3+ (Turso接続)

## セットアップ

### 必要な環境変数

以下の環境変数を`.env`ファイルに設定してください：

```bash
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=your-auth-token
SPREADSHEET_ID=your-spreadsheet-id
LOG_LEVEL=INFO  # Optional: DEBUG, INFO, WARNING, ERROR
```

### Docker開発環境

1. リポジトリをクローン:
   ```bash
   git clone <repository-url>
   cd i7_datasync
   ```

2. `.env`ファイルを作成し、必要な環境変数を設定

3. Docker環境で同期を実行:
   ```bash
   docker-compose up
   ```

### ローカル開発

1. 仮想環境を作成:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate
   ```

2. 依存関係をインストール:
   ```bash
   pip install -r requirements.txt
   ```

3. 同期スクリプトを実行:
   ```bash
   python src/main.py
   ```

## テスト

### ユニットテストの実行

Docker環境でテストを実行:
```bash
docker build -t i7-datasync-test .
docker run --rm i7-datasync-test python -m pytest tests/ -v
```

ローカル環境でテストを実行:
```bash
pytest tests/ -v
```

#### ユニットテストカバレッジ

- `test_csv_fetcher.py`: CSV取得、HTTPエラー、タイムアウト、リトライロジック
- `test_db_client.py`: Turso接続、トランザクション、ロールバック
- `test_validators.py`: データ検証（songs、cards、brooches）
- `test_schema_manager.py`: スキーマ生成、型推論、カラム名サニタイゼーション

### 統合テスト

実際のSpreadsheetとTursoデータベースを使用した統合テストを実行:

```bash
# 統合テストのみ実行
docker-compose run --rm sync pytest tests/test_integration.py -v

# または、実際の同期を実行
docker-compose run sync
```

#### 統合テストカバレッジ

- CSV取得（実際のSpreadsheet）
- データベース接続（実際のTurso）
- スキーマ初期化
- 単一テーブル同期
- 完全同期フロー（3テーブル）
- データ検証統合
- データ整合性確認
- エラーハンドリング
- トランザクションロールバック

### パフォーマンステスト

大量データ処理のパフォーマンスを測定:

```bash
docker-compose run --rm sync pytest tests/test_performance.py -v -s
```

#### パフォーマンステストカバレッジ

- CSV解析（10,000レコード）
- データ検証（10,000レコード）
- データ変換（10,000レコード）
- バッチ挿入（10,000レコード）
- 完全同期フロー
- メモリリーク検出（10回繰り返し）
- 並行操作時のメモリ使用量

**パフォーマンス目標**:

- 処理時間: 30分以内（10,000レコード）
- メモリ使用量: 512MB以内

## GitHub Actions設定

### 必要なSecrets

GitHubリポジトリの Settings > Secrets and variables > Actions で以下のsecretsを設定してください：

- `TURSO_DATABASE_URL`: TursoデータベースのURL
- `TURSO_AUTH_TOKEN`: Turso認証トークン
- `SPREADSHEET_ID`: Google SpreadsheetのID

### 手動トリガー

GitHub ActionsのUI（Actions > Sync Spreadsheet to Database > Run workflow）から手動で同期を実行できます。

## アーキテクチャ

### 3層構造

```
┌─────────────────────────────┐
│  Data Source Layer          │
│  - CSVFetcher               │
└─────────────────────────────┘
           ↓
┌─────────────────────────────┐
│  Business Logic Layer       │
│  - DataValidator            │
│  - DataTransformer          │
│  - SyncOrchestrator         │
└─────────────────────────────┘
           ↓
┌─────────────────────────────┐
│  Data Persistence Layer     │
│  - DatabaseClient           │
│  - SchemaManager            │
└─────────────────────────────┘
```

### データフロー

1. **CSV取得**: CSVFetcherがGoogle SpreadsheetからCSVデータを取得
2. **検証**: DataValidatorがデータの整合性をチェック
3. **変換**: DataTransformerがデータベース挿入用に最適化
4. **同期**: SyncOrchestratorが全テーブルの同期を調整
5. **永続化**: DatabaseClientがトランザクション内でデータを更新

## プロジェクト構造

```
i7_datasync/
├── .github/
│   └── workflows/
│       └── sync-spreadsheet.yml  # GitHub Actions設定
├── src/
│   ├── main.py                   # エントリーポイント
│   ├── constants.py              # GID定数
│   ├── logger.py                 # JSONロガー
│   ├── csv_fetcher.py            # CSV取得
│   ├── db_client.py              # Turso接続
│   ├── schema_manager.py         # スキーマ管理
│   ├── validators.py             # データ検証
│   ├── transformers.py           # データ変換
│   └── orchestrator.py           # 同期調整
├── tests/
│   ├── test_csv_fetcher.py       # CSVFetcher単体テスト
│   ├── test_db_client.py          # DatabaseClient単体テスト
│   ├── test_validators.py         # DataValidator単体テスト
│   ├── test_schema_manager.py     # SchemaManager単体テスト
│   ├── test_integration.py        # 統合テスト
│   └── test_performance.py        # パフォーマンステスト
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## トラブルシューティング

詳細なトラブルシューティング情報は[TROUBLESHOOTING.md](TROUBLESHOOTING.md)を参照してください。

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。
