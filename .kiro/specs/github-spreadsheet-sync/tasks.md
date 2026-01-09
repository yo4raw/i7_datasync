# Implementation Plan

## タスク概要

本実装計画は、Google Spreadsheet同期システムの開発を段階的に進めるためのタスクリストです。3層アーキテクチャ（Data Source、Business Logic、Data Persistence）に基づき、各コンポーネントを順次実装し、最終的にGitHub Actionsワークフローで統合します。

---

## 1. プロジェクトセットアップと環境構築

- [x] 1.1 (P) Pythonプロジェクト初期化とディレクトリ構造作成
  - プロジェクトルートに`src/`ディレクトリを作成
  - `requirements.txt`または`pyproject.toml`で依存関係管理ファイルを作成
  - pandas 2.0+、requests 2.31+、libsql-client 0.3+を依存関係に追加
  - _Requirements: 5_

- [x] 1.2 (P) Docker環境構築
  - `Dockerfile`を作成（Python 3.11+ベースイメージ使用）
  - `docker-compose.yml`を作成（環境変数注入、ボリュームマウント設定）
  - `.env.example`を作成（TURSO_DATABASE_URL、TURSO_AUTH_TOKEN、SPREADSHEET_ID、LOG_LEVEL）
  - `.gitignore`に`.env`を追加済みであることを確認
  - _Requirements: 5_

- [x] 1.3 定数定義とロガー設定
  - `src/constants.py`を作成
  - GID定数を定義（SONGS_GID=1083871743、CARDS_GID=480354522、BROOCHES_GID=1087762308）
  - `src/logger.py`を作成（環境変数LOG_LEVELでログレベル制御、JSON形式ログ出力）
  - _Requirements: 7_

## 2. Data Source Layer実装

- [x] 2.1 (P) CSVFetcherクラス実装
  - `src/csv_fetcher.py`を作成
  - `fetch_csv_as_dataframe(spreadsheet_id, gid, timeout)`メソッドを実装
  - CSVエクスポートURLテンプレート（`https://docs.google.com/spreadsheets/d/{id}/export?format=csv&gid={gid}`）を使用
  - requests.get()でCSV取得、pandas.read_csv()でDataFrame変換
  - HTTPエラー（4xx/5xx）、タイムアウト時の例外処理とリトライロジック（最大3回）
  - 取得レコード数をログ記録
  - _Requirements: 1_

## 3. Data Persistence Layer実装

- [x] 3.1 (P) DatabaseClientクラス実装
  - `src/db_client.py`を作成
  - `__init__()`で環境変数（TURSO_DATABASE_URL、TURSO_AUTH_TOKEN）から接続情報取得
  - `connect()`メソッドでTursoデータベース接続確立
  - `execute_transaction(delete_query, insert_statements)`メソッドを実装（トランザクション内でDELETE + バッチINSERT実行）
  - トランザクション失敗時の自動ロールバック
  - 削除・挿入レコード数を返却
  - _Requirements: 2, 3, 6_

- [x] 3.2 SchemaManagerクラス実装
  - `src/schema_manager.py`を作成
  - `ensure_table_exists(table_name, df)`メソッドを実装（テーブル未存在時にCREATE TABLE実行）
  - `infer_column_types(df)`メソッドを実装（pandasのdtypeからSQL型へマッピング: int64→INTEGER、object→TEXT、float64→REAL）
  - Spreadsheetヘッダーからカラム名取得、IDカラムを主キーとして定義
  - SQLインジェクション防止のためカラム名サニタイゼーション実装
  - _Requirements: 2_

## 4. Business Logic Layer実装

- [x] 4.1 (P) DataValidatorクラス実装 - 楽曲データ検証
  - `src/validators.py`を作成
  - `validate_songs_data(df)`メソッドを実装
  - IDフィールドの空チェック
  - 数値フィールド（ノーツ数、秒数など）の型変換可能性チェック
  - 無効行のスキップと詳細エラーログ記録（行番号、フィールド名、エラー内容）
  - 有効なDataFrameとエラーメッセージリストを返却
  - _Requirements: 8_

- [x] 4.2 (P) DataValidatorクラス実装 - カードデータ検証
  - `validate_cards_data(df)`メソッドを`validators.py`に追加
  - IDフィールドとcardIDフィールドの空チェック
  - rarity値の妥当性チェック（UR/SSR/SR/R）
  - 数値フィールドの型変換可能性チェック
  - 無効行のスキップとエラーログ記録
  - _Requirements: 8_

- [x] 4.3 (P) DataValidatorクラス実装 - 固有ブローチデータ検証
  - `validate_brooches_data(df)`メソッドを`validators.py`に追加
  - IDフィールドとcardIDフィールドの空チェック
  - スコア関連フィールドの非負整数チェック
  - 無効行のスキップとエラーログ記録
  - _Requirements: 8_

- [x] 4.4 (P) DataTransformerクラス実装
  - `src/transformers.py`を作成
  - SpreadsheetのDataFrameをデータベース挿入用に変換するメソッド実装
  - データ型の最適化（int64、float64、object）
  - 空文字列のNULL変換処理
  - _Requirements: 3_

- [x] 4.5 SyncOrchestratorクラス実装 - 基本構造
  - `src/orchestrator.py`を作成
  - `__init__()`でCSVFetcher、DatabaseClient、DataValidator、DataTransformerを依存性注入
  - SyncResultデータクラスを定義（table_name、deleted_count、inserted_count、skipped_count、success、error_message）
  - _Requirements: 3, 7_

- [x] 4.6 SyncOrchestratorクラス実装 - 単一テーブル同期
  - `sync_single_table(table_name, gid, spreadsheet_id)`メソッドを実装
  - CSVFetcherでデータ取得 → DataValidatorで検証 → DataTransformerで変換 → DatabaseClientで同期の全体フロー制御
  - トランザクション境界制御（各テーブル独立）
  - エラー時のロールバックとログ記録
  - SyncResult返却
  - _Requirements: 3, 7_

- [x] 4.7 SyncOrchestratorクラス実装 - 全テーブル同期
  - `sync_all_tables(spreadsheet_id, sheet_configs)`メソッドを実装
  - 3つのテーブル（songs、cards、brooches）を順次同期
  - 実行時間監視（30分超過でタイムアウト警告）
  - 各テーブルのSyncResultリストを返却
  - _Requirements: 3, 7, 9_

## 5. メインエントリーポイント実装

- [x] 5.1 メインスクリプト実装
  - `src/main.py`を作成
  - 環境変数読み込み（TURSO_DATABASE_URL、TURSO_AUTH_TOKEN、SPREADSHEET_ID）
  - シート設定定義（{"songs": SONGS_GID, "cards": CARDS_GID, "brooches": BROOCHES_GID}）
  - 各コンポーネントのインスタンス化とSyncOrchestrator初期化
  - SchemaManagerで3テーブルのスキーマ初期化
  - SyncOrchestrator.sync_all_tables()実行
  - 実行結果サマリーログ出力
  - 終了コード制御（成功: 0、失敗: 1）
  - _Requirements: 3, 4, 10_

## 6. GitHub Actions Workflow実装

- [x] 6.1 GitHub Actions Workflowファイル作成
  - `.github/workflows/sync-spreadsheet.yml`を作成
  - cronスケジュール設定（`0 */1 * * *`：1時間ごと）
  - 手動トリガー（workflow_dispatch）設定
  - Dockerコンテナビルドとsync実行ステップ定義
  - GitHub Secretsから環境変数注入（TURSO_DATABASE_URL、TURSO_AUTH_TOKEN、SPREADSHEET_ID）
  - 実行結果サマリーの記録
  - _Requirements: 4, 6_

## 7. テストとバリデーション

- [x] 7.1 (P) CSVFetcherユニットテスト
  - `tests/test_csv_fetcher.py`を作成
  - モックHTTPレスポンスで正常系テスト（DataFrameが正しく生成されることを確認）
  - HTTPエラー（404、500）時の例外処理テスト
  - タイムアウト時のリトライロジックテスト
  - _Requirements: 11_

- [x] 7.2 (P) DatabaseClientユニットテスト
  - `tests/test_db_client.py`を作成
  - モックlibsql-client接続でトランザクションテスト
  - 環境変数未設定時のエラーハンドリングテスト
  - トランザクション失敗時のロールバックテスト
  - _Requirements: 11_

- [x] 7.3 (P) DataValidatorユニットテスト
  - `tests/test_validators.py`を作成
  - 各テーブル（songs、cards、brooches）の検証ロジックテスト
  - 有効データ、無効データ、境界値でのテスト
  - エラーメッセージ形式の検証
  - _Requirements: 11_

- [x] 7.4 (P) SchemaManagerユニットテスト
  - `tests/test_schema_manager.py`を作成
  - DataFrame型からSQL型へのマッピングテスト（int64→INTEGER、object→TEXT、float64→REAL）
  - CREATE TABLE文生成の正確性テスト
  - カラム名サニタイゼーションテスト
  - _Requirements: 11_

- [x] 7.5 統合テスト - Docker環境での完全同期フロー
  - Docker環境で実際のSpreadsheet CSVエクスポートと実際のTursoデータベースを使用
  - 環境変数（.env）から実際の接続情報読み込み
  - 3テーブル（songs、cards、brooches）の完全同期サイクル実行
  - 同期結果の検証（削除・挿入レコード数、データ整合性）
  - エラーハンドリングとログ記録の動作確認
  - _Requirements: 11_

- [x] 7.6 パフォーマンステスト
  - 大量データ（10,000レコード）挿入時の処理時間測定（目標: 30分以内）
  - メモリ使用量プロファイリング（目標: 512MB以内）
  - バッチ挿入パフォーマンス検証
  - _Requirements: 9_

## 8. ドキュメント整備

- [x] 8.1 README作成
  - `README.md`を作成
  - プロジェクト概要、目的、主要機能を記載
  - セットアップ手順（ローカル開発環境構築方法）を記載
  - Docker環境での実行方法（`docker-compose up`）を記載
  - 環境変数の説明（.env.exampleを参照）
  - _Requirements: 12_

- [x] 8.2 トラブルシューティングガイド作成
  - `TROUBLESHOOTING.md`を作成
  - 一般的なエラーと解決方法を記載（CSV取得失敗、DB接続失敗、トランザクションエラー等）
  - ログ確認方法とデバッグ手順を記載
  - _Requirements: 12_

---

## タスク実行の注意事項

- **並列実行可能タスク**: `(P)`マーカー付きタスクは並列実行可能
- **依存関係**: 各Major Taskは前のMajor Taskの完了後に開始（例: Task 4はTask 3完了後）
- **環境変数**: .envファイルとGitHub Secretsで同一の環境変数名を使用
- **テスト**: Docker環境で実際のSpreadsheet + Tursoを使用した実環境テスト必須
- **コミット**: 各Major Task完了時にコミット推奨

