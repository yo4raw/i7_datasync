# Research & Design Decisions

---
**Purpose**: Google Spreadsheet同期システムの技術調査と設計判断の記録

**Usage**:
- 発見段階における調査活動と結果を記録
- design.mdで詳細に説明するには冗長すぎる設計判断のトレードオフを文書化
- 将来の監査や再利用のための参照と証拠を提供
---

## Summary
- **Feature**: `github-spreadsheet-sync`
- **Discovery Scope**: New Feature
- **Key Findings**:

  - Google SpreadsheetsのCSVエクスポートURL（公開アクセス）により認証不要でデータ取得可能
  - TursoはlibSQLベースでSQLiteと100%互換性があり、JWT認証を使用
  - GitHub ActionsはDockerコンテナ内でcron実行とシークレット管理が可能
  - Python環境でpandas + requests + libsql-client-pyの組み合わせが最適

## Research Log

### Google Spreadsheets データアクセス方式

- **Context**: Spreadsheetからデータを取得する最適な方法を調査
- **Sources Consulted**:
  - 実際のSpreadsheet CSV Export URLテスト
  - [pandas.read_csv — pandas documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
  - [Requests: HTTP for Humans](https://requests.readthedocs.io/)

- **Findings**:

  - **CSV Export URL検証**:
    - URL形式: `https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={sheet_gid}`
    - 対象Spreadsheetの全3シート（楽曲、カード、固有ブローチ）で公開アクセス可能を確認
    - 認証不要でHTTP GETリクエストで直接CSV取得可能
    - songs (gid=1083871743): 142レコード
    - cards (gid=480354522): 586レコード
    - brooches (gid=1087762308): 100+レコード

  - **Python実装パターン**:
    ```python
    import requests
    import pandas as pd
    from io import StringIO

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))
    ```

  - **利点**:
    - 認証不要（Google Service Account、OAuth 2.0不要）
    - 依存関係最小化（gspread/gspread-dataframe不要）
    - シンプルな実装（requests + pandas標準機能のみ）
    - ネットワークエラー処理が容易（requests標準機能）

- **Implications**:
  - CSV Export URL方式を採用（認証レイヤー削除でシステム簡素化）
  - requests + pandas.read_csv()で実装（標準的で保守性が高い）
  - 環境変数は TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, SPREADSHEET_ID のみ（GOOGLE_SERVICE_ACCOUNT_JSON 不要）

### Turso Database & libSQL統合

- **Context**: 本番環境でのTurso使用とSQLite開発環境との互換性確認
- **Sources Consulted**:
  - [libSQL - Turso](https://docs.turso.tech/libsql)
  - [Python SDK | Turso](https://docs.turso.tech/libsql/client-access/python-sdk)
  - [Batches in SQLite](https://turso.tech/blog/batches-in-sqlite-838e0961)
  - [GitHub - tursodatabase/libsql-client-py](https://github.com/tursodatabase/libsql-client-py)
  - [Working with Turso | Atlas Guides](https://atlasgo.io/guides/sqlite/turso)

- **Findings**:
  - **SQLite互換性**: libSQLはSQLiteのフォークで100% API互換性を維持
  - **認証**: JWT ベースの`authToken`パラメータで認証（環境変数から取得）
  - **接続パターン**:

    ```python
    import libsql_client
    client = libsql_client.create_client(
        url="libsql://[db-name].turso.io",
        auth_token="eyJhbGc..."
    )
    ```

  - **バッチ挿入パターン**:

    ```python
    rss = client.batch([
        libsql_client.Statement("insert into table values (?, ?)", ["val1", "val2"]),
        libsql_client.Statement("insert into table values (?, ?)", ["val3", "val4"]),
    ])
    ```

    - batch()は暗黙的トランザクション内で実行
    - すべてのステートメント成功でコミット、1つでも失敗で全体ロールバック

  - **トランザクション**: `transaction()`メソッドで明示的トランザクション作成可能だが、書き込みロック発生のため高負荷環境では注意

  - **スキーママイグレーション**:
    - Atlas: Terraform風の宣言的マイグレーションツール（推奨）
    - Drizzle: `push:sqlite`コマンドでスキーマ変更適用
    - Turso CLI: `db import`コマンドでSQLiteファイル直接インポート（WALモード必須）

- **Implications**:
  - SQLiteとTursoで同一のSQLクエリとPython SDKを使用可能
  - 環境変数（TURSO_DATABASE_URL、TURSO_AUTH_TOKEN）で接続先切り替え
  - batch()を使用したバッチ挿入でパフォーマンスとアトミック性を両立
  - 初期スキーマはSQLiteで作成しTurso CLIでインポート、以降はコード内でCREATE TABLE IF NOT EXISTSで管理

### GitHub Actions Workflow設計

- **Context**: Docker環境でのcronスケジュール実行とシークレット管理
- **Sources Consulted**:
  - [Github Actions, Docker, and the Beloved Cron](http://franciscojavierarceo.dev/post/docker-github-actions-and-cron)
  - [Using secrets with GitHub Actions - Docker Build](https://docs.docker.com/build/ci/github-actions/secrets/)
  - [GitHub Actions | Docker Docs](https://docs.docker.com/build/ci/github-actions/)
  - [Managing secrets in Docker Compose and GitHub Actions](https://jmh.me/blog/secrets-management-docker-compose-deployment)

- **Findings**:
  - **Cronスケジュール**: `cron: '0 */1 * * *'`で1時間ごとに実行
  - **シークレット管理方式**:
    1. GitHub Secretsに格納（TURSO_AUTH_TOKEN等）
    2. docker/build-push-actionの`secrets`パラメータ経由で渡す
    3. 実行時に環境変数として注入: `docker run -e TURSO_AUTH_TOKEN=${{ secrets.TURSO_AUTH_TOKEN }}`

  - **ベストプラクティス**:
    - シークレットをイメージレイヤーに埋め込まない
    - GitHub Secretsで一元管理
    - 実行時に環境変数として注入（ログに出力されない）
    - 定期的にトークンをローテーション（33%のセキュリティ侵害は認証情報の不備が原因）

- **Implications**:
  - 開発環境（.env）と本番環境（GitHub Secrets）で同一の環境変数名を使用:
    - `TURSO_DATABASE_URL`: Tursoデータベース URL（例: `libsql://[db-name].turso.io`）
    - `TURSO_AUTH_TOKEN`: Turso認証トークン（JWT形式）
    - `SPREADSHEET_ID`: 対象SpreadsheetのID
    - `LOG_LEVEL`: ログレベル（DEBUG/INFO/WARNING/ERROR、デフォルト: INFO）
  - 本番環境: GitHub Secretsに格納、workflow内で環境変数として注入
  - 開発環境: .envファイルに格納（.gitignore登録）、docker-compose.ymlで読み込み
  - SpreadsheetアクセスはCSVエクスポートURL（公開アクセス）を使用するため認証情報不要

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Simple Script | Python単一スクリプトで全処理 | シンプル、理解しやすい | テストしづらい、拡張性低い | 小規模には適切 |
| Layered Architecture | データ取得層、変換層、永続化層を分離 | テスト容易、拡張性高い、責任分離明確 | 初期実装コスト高い | 本システムに採用 |
| Event-driven | イベントキュー経由で処理 | 非同期、スケーラブル | 複雑、オーバーエンジニアリング | 現在の要件には不要 |

## Design Decisions

### Decision: Google Spreadsheetsデータアクセス方式（CSV Export URL採用）

- **Context**: Google Spreadsheetsからデータを取得する方法を選択
- **Alternatives Considered**:
  1. Google Sheets API (Service Account) — 認証必要、依存関係増加、セットアップ複雑
  2. Google Sheets API (OAuth 2.0) — ユーザー認証フロー必要、自動化に不向き
  3. CSV Export URL — 公開Spreadsheetからダイレクトアクセス、認証不要

- **Selected Approach**: CSV Export URL（公開アクセス）
  - URL形式: `https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}`
  - HTTP GETリクエストで直接CSV取得
  - pandas.read_csv()でDataFrame変換

- **Rationale**:
  - 対象Spreadsheetが公開設定されており、CSV Export URLでアクセス可能と確認済み
  - 認証レイヤー不要でシステム簡素化
  - 依存関係最小化（requests + pandas標準機能のみ）
  - Google API認証のセットアップ・メンテナンス不要
  - 実装がシンプルで保守性が高い

- **Trade-offs**:
  - Benefits: 認証不要、依存関係最小、シンプル実装、セットアップ容易
  - Compromises: Spreadsheetが公開設定である必要あり（本システムでは問題なし）

- **Verification**: 全3シート（songs, cards, brooches）で公開アクセス可能を確認済み

### Decision: データ同期方式（Full Delete + Insert）

- **Context**: Spreadsheetの変更をデータベースに反映する方式
- **Alternatives Considered**:
  1. Differential Sync — 変更検知、更新・挿入・削除、複雑なロジック
  2. Full Delete + Insert — 全削除後に全挿入、シンプル、確実

- **Selected Approach**: Full Delete + Insert
  - 各テーブルに対して`DELETE FROM table`実行
  - Spreadsheetから取得した全データをバッチ挿入
  - トランザクションで原子性保証

- **Rationale**:
  - ユーザー要件：「毎回全削除全取り込みでシンプルな仕様」
  - データ量は比較的少量（楽曲・カード・ブローチ数千件程度）
  - 差分検知の複雑性を回避
  - 確実性重視（データ不整合リスク低減）

- **Trade-offs**:
  - Benefits: 実装シンプル、テスト容易、バグ少ない、データ整合性高い
  - Compromises: 差分同期より処理時間長い（ただし1時間ごと実行で問題なし）

- **Follow-up**: パフォーマンスモニタリングで処理時間が30分超える場合は差分同期検討

### Decision: テーブル設計（3テーブル分離）

- **Context**: Spreadsheetの構造をデータベースに反映する設計
- **Alternatives Considered**:
  1. 単一テーブル — 全データを1テーブルに格納、type列で区別
  2. 3テーブル分離 — songs、cards、broochesテーブルで分離

- **Selected Approach**: 3テーブル分離（songs、cards、brooches）
  - 各テーブルはSpreadsheetのシート構造に対応
  - ヘッダー行からカラム名を取得
  - IDカラムを主キーとして定義

- **Rationale**:
  - ユーザー要件：「取り込むシートとなるべくDB構成を近い状態にしたい」
  - 各データタイプでカラム数・構造が異なる
  - クエリ性能向上（不要なデータ除外）
  - スキーマ明確化（型安全性向上）

- **Trade-offs**:
  - Benefits: 構造明確、クエリ最適化容易、メンテナンス性高い
  - Compromises: マイグレーション時に3テーブル管理必要

- **Follow-up**: 動的カラム追加対応のため、初回実行時にSpreadsheetヘッダーからスキーマ生成

### Decision: Python実装（requests + pandas + libsql-client）

- **Context**: Spreadsheet取得とDB操作のライブラリ選定
- **Alternatives Considered**:
  1. Google Sheets API (gspread/gspread-dataframe) — 認証必要、依存関係多い、セットアップ複雑
  2. CSV URL Export + sqlite3標準ライブラリ — シンプルだがTurso未対応
  3. CSV URL Export + requests + pandas + libsql-client — 認証不要、標準的、Turso対応

- **Selected Approach**: requests + pandas + libsql-client-py
  - requests: CSV URLからHTTP GETでデータ取得
  - pandas: CSV解析（pd.read_csv）、データ変換・検証
  - libsql-client-py: Turso接続とクエリ実行

- **Rationale**:
  - 認証不要（CSV Export URL使用）
  - 依存関係最小化（標準的なライブラリのみ）
  - pandasの強力なデータ処理機能活用
  - Tursoの公式Python SDK使用で将来性確保
  - 開発環境と本番環境で同一DB（Turso）使用可能

- **Trade-offs**:
  - Benefits: シンプル実装、依存関係最小、認証不要、保守性高い
  - Compromises: Spreadsheetが公開設定である必要あり（本システムでは問題なし）

- **Follow-up**: requirements.txtで依存バージョン固定（requests, pandas, libsql-client）、定期的なセキュリティアップデート

### Decision: Docker環境構成（docker-compose + .env）

- **Context**: ローカル開発環境の構築方式
- **Alternatives Considered**:
  1. venv + ローカルPython — Dockerなし、環境依存
  2. Dockerfile単体 — 環境変数管理が煩雑
  3. docker-compose + .env — 環境変数管理容易、再現性高い

- **Selected Approach**: docker-compose.yml + .env
  - Python 3.11ベースイメージ
  - Tursoデータベースに接続（開発環境と本番環境で同一DB）
  - .envファイルで環境変数管理（GitHub Secretsと同一の変数名使用）

- **Rationale**:
  - 開発環境と本番環境で完全に同じデータベース環境を使用
  - `docker-compose up`一発で起動
  - .envファイルで機密情報分離（.gitignore登録）
  - GitHub Secretsと同一の環境変数名により、設定の一貫性を確保

- **Trade-offs**:
  - Benefits: 環境差異なし、依存管理容易、チーム開発対応、設定ミス防止
  - Compromises: Docker学習コスト、初回ビルド時間、Turso接続必須

- **Follow-up**: .env.exampleテンプレート提供（環境変数名を明記）、README.mdでセットアップ手順明記

## Risks & Mitigations

- **Risk 1: Spreadsheetアクセス権限変更** — Proposed mitigation: Spreadsheetが非公開に変更された場合の検知とアラート、CSV取得エラー時の詳細ログ
- **Risk 2: Spreadsheetスキーマ変更** — Proposed mitigation: 動的カラム検出、ALTER TABLE未使用でCREATE TABLE IF NOT EXISTSで対応
- **Risk 3: Turso接続障害** — Proposed mitigation: リトライロジック（最大3回）、エラー通知（GitHub Actions失敗通知）
- **Risk 4: トランザクションタイムアウト** — Proposed mitigation: 各テーブルごとに個別トランザクション、バッチサイズ調整
- **Risk 5: ネットワーク障害（CSV取得失敗）** — Proposed mitigation: HTTPタイムアウト設定、リトライロジック、詳細エラーログ

## References

- [pandas.read_csv — pandas documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) — CSV解析とDataFrame変換
- [Requests: HTTP for Humans](https://requests.readthedocs.io/) — HTTPクライアントライブラリ
- [Python SDK | Turso](https://docs.turso.tech/libsql/client-access/python-sdk) — Turso公式Python SDKドキュメント
- [Batches in SQLite](https://turso.tech/blog/batches-in-sqlite-838e0961) — バッチ挿入パターン
- [Using secrets with GitHub Actions - Docker Build](https://docs.docker.com/build/ci/github-actions/secrets/) — GitHub Actionsシークレット管理
- [Working with Turso | Atlas Guides](https://atlasgo.io/guides/sqlite/turso) — Tursoマイグレーション戦略
