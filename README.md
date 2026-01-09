# i7_datasync

アイナナのゲームデータ（楽曲、カード、固有ブローチ）をGoogle SpreadsheetからTursoデータベースへガンガン自動同期するやで！GitHub Actionsでバリバリ動かすんや！

## なにこれ？

公開されとるGoogle SpreadsheetのCSVエクスポートURLから3種類のゲームデータを取得して、Tursoデータベースにバシッと自動同期するんやで。ほんま最高や！

### 主な機能（めっちゃすごいで）

- **CSV Export Access**: Google Spreadsheetの公開CSVエクスポートURLから直接データ取得や（Google Sheets API？そんなもん要らんのや！）
- **Full Sync Pattern**: シンプルで確実な全削除→全挿入パターンでガツンと同期や
- **Automated Scheduling**: GitHub Actionsで1時間ごとに自動実行やで（サボらんで！）
- **Environment Parity**: Docker開発環境と本番環境でTurso統一使用や（環境差異？知らんがな！）

## 技術スタック（強すぎる布陣や）

- **言語**: Python 3.11+（最新版や！）
- **ランタイム**: Docker 24+ / docker-compose 2.0+（コンテナ最強や）
- **データベース**: Turso (libSQL)（SQLite派生の超高速DBやで）
- **主要ライブラリ**:
  - pandas 2.0+（データ処理はこいつに任せとけ）
  - requests 2.31+（HTTP通信バリバリや）
  - libsql-client 0.3+（Turso接続の相棒や）

## セットアップ（簡単やで！）

### 必要な環境変数（これだけ設定したらええんや）

以下の環境変数を`.env`ファイルに書いとけや：

```bash
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=your-auth-token
SPREADSHEET_ID=your-spreadsheet-id
LOG_LEVEL=INFO  # オプションや: DEBUG, INFO, WARNING, ERROR
```

### Docker開発環境（ワンパンや！）

1. リポジトリをクローンするんやで:
   ```bash
   git clone <repository-url>
   cd i7_datasync
   ```

2. `.env`ファイルを作って環境変数を設定するんや

3. Docker環境で同期を実行や:
   ```bash
   docker-compose up
   ```

   これだけでガンガン動くで！

### ローカル開発（Docker使わん派はこっちや）

1. 仮想環境を作るんやで:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windowsは .venv\Scripts\activate やで
   ```

2. 依存関係をインストールや:
   ```bash
   pip install -r requirements.txt
   ```

3. 同期スクリプトを実行や:
   ```bash
   python src/main.py
   ```

## テスト（品質保証バッチリや）

### ユニットテストの実行（基礎固めや）

Docker環境でテスト実行や:
```bash
docker build -t i7-datasync-test .
docker run --rm i7-datasync-test python -m pytest tests/ -v
```

ローカル環境でテスト実行や:
```bash
pytest tests/ -v
```

#### ユニットテストカバレッジ（めっちゃしっかりしとるで）

- `test_csv_fetcher.py`: CSV取得、HTTPエラー、タイムアウト、リトライロジック（網羅的や）
- `test_db_client.py`: Turso接続、トランザクション、ロールバック（完璧や）
- `test_validators.py`: データ検証（songs、cards、brooches）（全テーブル対応や）
- `test_schema_manager.py`: スキーマ生成、型推論、カラム名サニタイゼーション（安全第一や）

### 統合テスト（実戦テストや！）

実際のSpreadsheetとTursoデータベースを使った統合テスト実行や:

```bash
# 統合テストのみ実行
docker-compose run --rm sync pytest tests/test_integration.py -v

# または、実際の同期を実行や
docker-compose run sync
```

#### 統合テストカバレッジ（完璧やで）

- CSV取得（実際のSpreadsheetから取るで）
- データベース接続（実際のTursoに繋ぐで）
- スキーマ初期化（テーブル作成や）
- 単一テーブル同期（1個ずつ確認や）
- 完全同期フロー（3テーブル一気や）
- データ検証統合（バリデーション万全や）
- データ整合性確認（データ壊れてへんか確認や）
- エラーハンドリング（エラーにも強いで）
- トランザクションロールバック（失敗しても安心や）

### パフォーマンステスト（速度計測や！）

大量データ処理のパフォーマンスを測定するで:

```bash
docker-compose run --rm sync pytest tests/test_performance.py -v -s
```

#### パフォーマンステストカバレッジ（爆速確認や）

- CSV解析（10,000レコード）← めっちゃ大量や
- データ検証（10,000レコード）← バリデーションも爆速や
- データ変換（10,000レコード）← 変換処理も速いで
- バッチ挿入（10,000レコード）← 挿入も一瞬や
- 完全同期フロー（全体通しでどないや）
- メモリリーク検出（10回繰り返し）← メモリ漏れはあかんで
- 並行操作時のメモリ使用量（同時実行しても安心や）

**パフォーマンス目標（これクリアせなあかんで）**:

- 処理時間: 30分以内（10,000レコード）← これくらいは余裕や
- メモリ使用量: 512MB以内 ← 省メモリや

## GitHub Actions設定（自動化最強や）

### 必要なSecrets（これ設定せな動かんで）

GitHubリポジトリの Settings > Secrets and variables > Actions で以下のsecrets設定するんや：

- `TURSO_DATABASE_URL`: TursoデータベースのURL（これ必須や）
- `TURSO_AUTH_TOKEN`: Turso認証トークン（これも必須や）
- `SPREADSHEET_ID`: Google SpreadsheetのID（これないと始まらんで）

### 手動トリガー（好きなタイミングで動かせるで）

GitHub ActionsのUI（Actions > Sync Spreadsheet to Database > Run workflow）から手動で同期実行できるんや。便利やろ？

## アーキテクチャ（きれいな3層構造や）

### 3層構造（美しいで）

```
┌─────────────────────────────┐
│  Data Source Layer          │  ← ここでデータ取得や
│  - CSVFetcher               │
└─────────────────────────────┘
           ↓
┌─────────────────────────────┐
│  Business Logic Layer       │  ← ここでビジネスロジックや
│  - DataValidator            │
│  - DataTransformer          │
│  - SyncOrchestrator         │
└─────────────────────────────┘
           ↓
┌─────────────────────────────┐
│  Data Persistence Layer     │  ← ここでDB操作や
│  - DatabaseClient           │
│  - SchemaManager            │
└─────────────────────────────┘
```

### データフロー（この流れでガンガン同期するで）

1. **CSV取得**: CSVFetcherがGoogle SpreadsheetからCSVデータ取得や
2. **検証**: DataValidatorがデータの整合性をガッチリチェックや
3. **変換**: DataTransformerがデータベース挿入用に最適化するで
4. **同期**: SyncOrchestratorが全テーブルの同期をバシッと調整や
5. **永続化**: DatabaseClientがトランザクション内でデータをガツンと更新や

完璧な流れやろ？

## プロジェクト構造（整理整頓バッチリや）

```
i7_datasync/
├── .github/
│   └── workflows/
│       └── sync-spreadsheet.yml  # GitHub Actions設定（自動化の要や）
├── src/
│   ├── main.py                   # エントリーポイント（ここから始まるで）
│   ├── constants.py              # GID定数（設定まとめや）
│   ├── logger.py                 # JSONロガー（ログはJSONや）
│   ├── csv_fetcher.py            # CSV取得（データ取得の要や）
│   ├── db_client.py              # Turso接続（DB操作の要や）
│   ├── schema_manager.py         # スキーマ管理（テーブル管理や）
│   ├── validators.py             # データ検証（品質管理や）
│   ├── transformers.py           # データ変換（最適化や）
│   └── orchestrator.py           # 同期調整（指揮官や）
├── tests/
│   ├── test_csv_fetcher.py       # CSVFetcher単体テスト
│   ├── test_db_client.py          # DatabaseClient単体テスト
│   ├── test_validators.py         # DataValidator単体テスト
│   ├── test_schema_manager.py     # SchemaManager単体テスト
│   ├── test_integration.py        # 統合テスト（実戦や）
│   └── test_performance.py        # パフォーマンステスト（速度測定や）
├── Dockerfile                     # Docker設定（コンテナ化や）
├── docker-compose.yml             # Docker Compose設定（便利や）
├── requirements.txt               # Python依存関係（これだけや）
└── README.md                      # このファイルや！
```

きれいに整理されとるやろ？

## トラブルシューティング（困ったらこれ見てや）

詳細なトラブルシューティング情報は[TROUBLESHOOTING.md](TROUBLESHOOTING.md)を参照してくれや。

## ライセンス（自由に使ってええで）

MIT License

## 貢献（プルリク待っとるで！）

プルリクエストをめっちゃ歓迎するで！大きな変更の場合は、まずissueを開いて変更内容を議論してくれや。みんなで良くしていこうやないか！

---

**わいらと一緒にアイナナのデータ同期を最強にしようや！🐯⚾**
