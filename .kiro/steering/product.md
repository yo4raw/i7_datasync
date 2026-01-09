# Product Overview

アイドリッシュセブンのゲームデータ（楽曲、カード、固有ブローチ）をGoogle SpreadsheetからTursoデータベースへ自動同期するGitHub Actionsワークフロー。

## Core Capabilities

- **CSV Export Access**: Google Spreadsheetの公開CSVエクスポートURLから3種類のゲームデータを取得
- **Full Sync Pattern**: シンプルで確実な全削除→全挿入パターンによるデータ同期
- **Automated Scheduling**: GitHub Actionsで1時間ごとに自動実行
- **Environment Parity**: Docker環境（開発）と本番環境でTursoを統一使用
- **Data Transformation**: Spreadsheet構造からデータベーステーブルへの変換とバリデーション

## Target Use Cases

- **Score Calculation Backend**: スコアアタック計算システムのデータソース提供
- **Hands-off Data Pipeline**: 手動介入なしの定期的なデータ更新
- **Development Testing**: Docker環境での実際のSpreadsheet・Tursoを使用したテスト

## Value Proposition

- **Simplicity First**: 差分同期ではなく全削除→全挿入により実装を単純化
- **No Authentication Complexity**: 公開SpreadsheetのCSVエクスポートURLを利用し、Google Service Account不要
- **Production-Dev Consistency**: Docker開発環境と本番環境で同じTursoデータベースを使用し、環境差異を排除
- **Single Responsibility**: データ同期のみに特化（スコア計算やWebUIは別システム）

---
_Focus on patterns and purpose, not exhaustive feature lists_
