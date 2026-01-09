# Technology Stack

## Architecture

**Pattern**: Layered Architecture（3層構造）

- **Data Source Layer**: CSV export URLからのデータ取得
- **Business Logic Layer**: データ検証、変換、同期ロジック
- **Data Persistence Layer**: Tursoへのデータ保存

明確な責任分離により、各層の独立したテストとメンテナンスを実現。

## Core Technologies

- **Language**: Python 3.11+
- **Runtime**: Docker 24+ / docker-compose 2.0+
- **Database**: Turso (libSQL) — 開発・本番環境共通
- **CI/CD**: GitHub Actions — hourly cron (1時間ごと)

## Key Libraries

- **pandas 2.0+**: CSVデータ読み込みと処理（`pd.read_csv()`）
- **requests 2.31+**: CSV URLからのHTTP取得
- **libsql-client 0.3+**: Turso接続とクエリ実行（公式Python SDK、HTTP/WebSocket対応）

## Development Standards

### Database Access Pattern

**Full Truncate-Load**: シンプルさと確実性を優先
```python
# Transaction内で実行
DELETE FROM table;
INSERT INTO table VALUES (...);
```

差分検知や増分同期は実装しない（非目標）。

### Environment Configuration

**Parity Principle**: 開発環境と本番環境の設定名を統一

- **Development**: `.env` ファイル（gitignore済み）
- **Production**: GitHub Secrets
- **Requirement**: 両環境で同一の環境変数名を使用

```bash
# 共通環境変数（.env と GitHub Secrets で同名）
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...
SPREADSHEET_ID=...
LOG_LEVEL=INFO
```

**GID Constants**: シート識別子はコード内にハードコード
- 楽曲シート: `gid=1083871743`
- カードシート: `gid=480354522`
- ブローチシート: `gid=1087762308`

### Testing Approach

**Real Environment Testing**: モックデータ不使用

- Docker環境で実際のSpreadsheet CSV + 実際のTursoを使用
- GitHub Actionsと同じ環境で開発時に確認
- 環境再現性を最優先

### Error Handling

- トランザクション失敗時の完全ロールバック
- 詳細なログ記録（`LOG_LEVEL`で制御）
- エラー時のGitHub Actions通知

## Development Environment

### Required Tools
- Docker 24+
- docker-compose 2.0+
- Python 3.11+ (コンテナ内)
- Tursoアカウントとデータベース

### Common Commands
```bash
# Dev: Docker環境起動と同期実行
docker-compose up

# Test: 手動同期トリガー
docker-compose run sync

# Logs: ログ確認
docker-compose logs -f
```

## Development Tools

### MCP Servers (必須)

**Context7**: ライブラリドキュメント参照

- pandas、requests、libsql-client等のライブラリ情報を取得
- 公式ドキュメントのパターンとベストプラクティスを確認
- 使用例: バージョン固有のAPI仕様、推奨される使用方法

**Serena**: 開発時の必須ツール

- コードベースのセマンティック理解とナビゲーション
- シンボル操作（リネーム、参照検索、依存関係追跡）
- プロジェクトメモリとセッション永続化
- 使用例: 関数リファクタリング、影響範囲分析、プロジェクトコンテキスト維持

**Principle**: 開発時は必ずSerenaを使用し、ライブラリ情報が必要な場合はContext7を活用する。

## Key Technical Decisions

### Turso統一（SQLite不使用）
**Decision**: 開発・本番ともにTursoを使用
**Rationale**: 環境差異排除、本番問題の早期発見

### CSV Export URL（Google Sheets API不使用）
**Decision**: 公開SpreadsheetのCSV export URLを使用
**Rationale**: 認証不要、実装シンプル、Service Account管理不要
**Pattern**: `https://docs.google.com/spreadsheets/d/{id}/export?format=csv&gid={gid}`

### Full Sync（差分検知不使用）
**Decision**: 全削除→全挿入パターン
**Rationale**: 実装シンプル、データ整合性確実、1時間ごとの実行で性能問題なし

---
_Document standards and patterns, not every dependency_
