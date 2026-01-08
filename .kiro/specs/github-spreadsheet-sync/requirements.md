# Requirements Document

## Project Description (Input)
GithubActionでspreadsheetをDBに同期するworkflowの作成。docker環境で構築し、実際に動かしながら開発してください。docker環境ではSqliteを使用し、本番環境はtursoを使う予定です。
このレポジトリはDBのsyncのみを実装し、一時間毎にデータの取り込みをGithubActionで行います。

このデータはアイドリッシュセブンのスコアアタックの計算に使うデータで「楽曲」と「」

### 対象のデータについて
#### 楽曲データ
- **概要**: 楽曲情報のデータ
- **データソース**:
  - https://docs.google.com/spreadsheets/d/1UxM2ekw7KlTTbCfPFMa6ihywrUMTryP5Zrv1DVEUKy4/edit?gid=1083871743#gid=1083871743
- **データ項目**:
  - 基本情報（0-11）
    - ID - 楽曲ID
    - 分類 - 楽曲の分類（ŹOOĻ、IDOLiSH7など）
    - アーティスト名 - アーティスト名
    - 曲名 - 楽曲名
    - 楽曲種類 - 楽曲の種類（イベント楽曲など）
    - 難易度 - 難易度レベル（EXPERT+など）
    - ★ - 星評価
    - Shout割合 - Shout属性の割合（%）
    - Beat割合 - Beat属性の割合（%）
    - Melody割合 - Melody属性の割合（%）
    - ノーツ数 - 総ノーツ数
    - 秒数 - 楽曲の長さ（秒）
  - ノーツ詳細（12-59）
    - 各倍率（×1、×1.1、×1.2、×1.3、×1.5、×2.6、×3）ごとに、属性別（Shout/Beat/Melody）の白ノーツと色ノーツの数：
      - Shout×[倍率]白 - Shout属性の白ノーツ数
      - Shout×[倍率]色 - Shout属性の色ノーツ数
      - Beat×[倍率]白 - Beat属性の白ノーツ数
      - Beat×[倍率]色 - Beat属性の色ノーツ数
      - Melody×[倍率]白 - Melody属性の白ノーツ数
      - Melody×[倍率]色 - Melody属性の色ノーツ数
  - 合計（60-65）
    - Shout白合計 - Shout属性の白ノーツ合計
    - Shout色合計 - Shout属性の色ノーツ合計
    - Beat白合計 - Beat属性の白ノーツ合計
    - Beat色合計 - Beat属性の色ノーツ合計
    - Melody白合計 - Melody属性の白ノーツ合計
    - Melody色合計 - Melody属性の色ノーツ合計

#### カードデータ
- **概要**: カード情報のデータ
- **データソース**:
  - https://docs.google.com/spreadsheets/d/1UxM2ekw7KlTTbCfPFMa6ihywrUMTryP5Zrv1DVEUKy4/edit?gid=480354522#gid=480354522
- **データ項目**:
  - カード基本情報（0-9）
    - ID - カードの一意識別子
    - cardID - カードID
    - cardname - カード名
    - name - キャラクター名
    - name_other - その他の名前情報
    - groupname - グループ名
    - rarity - レアリティ（UR/SSR/SR/R）
    - get_type - 入手方法
    - story - ストーリー情報
    - awakening_item - 覚醒アイテムID
  - ステータス情報（10-16）
    - attribute - 属性（1:Shout, 2:Beat, 3:Melody）
    - shout_min - Shout最小値
    - shout_max - Shout最大値
    - beat_min - Beat最小値
    - beat_max - Beat最大値
    - melody_min - Melody最小値
    - melody_max - Melody最大値
  - スキル情報（17-43）
    - APスキル基本情報
      - ap_skill_type - APスキルタイプ
      - ap_skill_req - APスキル発動条件
      - ap_skill_name - APスキル名
    - APスキルレベル別詳細（レベル1-5）
    - 各レベルごとに以下の4項目：
      - ap_skill_[1-5]_count - 発動回数
      - ap_skill_[1-5]_per - 発動確率（%）
      - ap_skill_[1-5]_value - 効果値
      - ap_skill_[1-5]_rate - 効果率
  - その他のスキル
    - ct_skill - センタースキル
    - comment - コメント
    - sp_time - SPスキル時間
    - sp_value - SPスキル値

#### 固有ブローチデータ
- **概要**: ブローチ情報のデータ
- **データソース**:
  - https://docs.google.com/spreadsheets/d/1UxM2ekw7KlTTbCfPFMa6ihywrUMTryP5Zrv1DVEUKy4/edit?gid=1087762308#gid=1087762308
- **データ項目**:
  - グループカード基本情報（0-4）
    - ID - グループカードの一意識別子
    - cardID - 紐づくカードID
    - cardname - カード名
    - name - グループ名
    - name_other - メンバー情報
  - ステータス情報（5-7）
    - Shout - Shout属性値
    - Beat - Beat属性値
    - Melody - Melody属性値
  - 属性・グループ情報（8-10）
    - 属性 - カードの属性（数値）
    - アイドル - アイドルタイプ
    - グループ - グループタイプ
  - スコア関連情報（11-14）
    - オート - オートスコア値
    - 楽曲 - 楽曲スコア値
    - スコア - 総合スコア値
    - 上限 - スコア上限値
  - ブローチ情報（15）
    - ブローチの種類 - ブローチのタイプ

## Introduction
本システムは、Google Spreadsheetに格納されたアイドリッシュセブンのゲームデータ（楽曲、カード、固有ブローチ）を定期的にデータベースに同期するためのGitHub Actions workflowです。開発環境ではDockerコンテナ内でSQLiteを使用し、本番環境ではTursoデータベースを使用します。1時間ごとの自動実行により、常に最新のデータを維持します。

## Requirements

### Requirement 1: Google Spreadsheet データ取得
**Objective:** システム管理者として、Google Spreadsheetから楽曲、カード、固有ブローチのデータを自動取得したい。これにより、手動でのデータ更新作業を不要にする。

#### Acceptance Criteria

1. When GitHub Actionsワークフローが実行される, the Sync Serviceは楽曲データシート（gid=1083871743）から全列のデータを取得する
2. When GitHub Actionsワークフローが実行される, the Sync Serviceはカードデータシート（gid=480354522）から全列のデータを取得する
3. When GitHub Actionsワークフローが実行される, the Sync Serviceは固有ブローチデータシート（gid=1087762308）から全列のデータを取得する
4. The Sync ServiceはCSVエクスポートURL（公開アクセス可能）を使用してデータにアクセスする（Google Sheets API認証不要）
5. When データ取得に成功する, the Sync Serviceは取得したレコード数をログに記録する

### Requirement 2: データベーススキーマ管理

**Objective:** 開発者として、各データタイプに対応した3つのデータベーステーブルを持ちたい。これにより、Spreadsheetの構造に近い形で構造化されたデータ保存と効率的なクエリを実現する。

#### Acceptance Criteria

1. The Sync Serviceは楽曲データ用のテーブル（songs）を作成し、楽曲データシートの全列（ID、分類、アーティスト名、曲名、楽曲種類、難易度、星評価、属性割合、ノーツ詳細、合計値など）を含む
2. The Sync Serviceはカードデータ用のテーブル（cards）を作成し、カードデータシートの全列（カード基本情報、ステータス情報、APスキル情報、その他スキル）を含む
3. The Sync Serviceは固有ブローチデータ用のテーブル（brooches）を作成し、固有ブローチデータシートの全列（グループカード基本情報、ステータス、属性・グループ、スコア関連、ブローチ種類）を含む
4. The Sync Serviceは各テーブルのカラム名をSpreadsheetのヘッダー行から取得し、可能な限り同じ名前を使用する
5. The Sync Serviceは各テーブルのIDカラムを主キーとして定義する
6. The Sync Serviceは適切なデータ型（INTEGER、TEXT、REALなど）を各カラムに割り当てる
7. The Sync Serviceはデータベーススキーマのマイグレーション機能を提供する

### Requirement 3: データ同期処理

**Objective:** システム管理者として、3つのSpreadsheetシートのデータを対応する3つのデータベーステーブルに定期的に反映したい。これにより、シンプルで確実なデータ同期を実現する。

#### Acceptance Criteria

1. When 同期処理が実行される, the Sync Serviceは楽曲データシート（gid=1083871743）のデータをsongsテーブルに同期する
2. When 同期処理が実行される, the Sync Serviceはカードデータシート（gid=480354522）のデータをcardsテーブルに同期する
3. When 同期処理が実行される, the Sync Serviceは固有ブローチデータシート（gid=1087762308）のデータをbroochesテーブルに同期する
4. When 各テーブルの同期処理が実行される, the Sync Serviceは対象テーブルの全レコードを削除する
5. When 既存データの削除が完了する, the Sync ServiceはSpreadsheetから取得したデータを全件挿入する
6. The Sync Serviceは各テーブルの同期処理に対してトランザクション処理を使用し、削除と挿入の原子性を保証する
7. When トランザクション内でエラーが発生する, the Sync Serviceは該当テーブルの全ての変更をロールバックする
8. When 同期処理が完了する, the Sync Serviceは各テーブルごとに削除されたレコード数と挿入されたレコード数をログに記録する

### Requirement 4: GitHub Actions スケジュール実行

**Objective:** システム管理者として、データ同期を1時間ごとに自動実行したい。これにより、人手を介さずに常に最新のデータを維持する。

#### Acceptance Criteria

1. The GitHub Actions Workflowはcronスケジュール（0 \*/1 \* \* \*）で1時間ごとに実行される
2. The GitHub Actions Workflowは手動トリガー（workflow_dispatch）もサポートする
3. When ワークフローが実行される, the Sync Serviceは3つのテーブル（songs、cards、brooches）に対して完全な同期サイクル（取得、削除、挿入）を実行する
4. When ワークフローが完了する, the GitHub Actions Workflowは実行結果（成功/失敗）とサマリーを記録する

### Requirement 5: Docker開発環境

**Objective:** 開発者として、Docker環境でTursoデータベースを使用してローカルで開発とテストを行いたい。これにより、本番環境と同一のデータベース環境で開発できる。

#### Acceptance Criteria

1. The Development Environmentはdocker-compose.ymlを提供し、すべての必要なサービスを定義する
2. The Development EnvironmentはTursoデータベースを使用する
3. When docker-compose upコマンドを実行する, the Development Environmentはすべての依存関係を含む完全な開発環境を起動する
4. The Development Environmentは同期スクリプトをコンテナ内で実行可能にする
5. The Development Environmentは.envファイルからTURSO_DATABASE_URLとTURSO_AUTH_TOKENを読み込む
6. The Development Environmentは環境変数ファイル（.env）を使用して、設定を管理する

### Requirement 6: 開発環境と本番環境の統一

**Objective:** 運用管理者として、開発環境と本番環境で同じTursoデータベースを使用したい。これにより、環境差異による問題を防ぐ。

#### Acceptance Criteria

1. The Sync ServiceはTurso接続をサポートし、環境変数から接続情報を取得する
2. The Sync Serviceは開発環境（Docker）と本番環境（GitHub Actions）の両方でTursoに接続する
3. When 開発環境を使用する, the Sync Serviceは.envファイルからTURSO_DATABASE_URLとTURSO_AUTH_TOKENを取得する
4. When 本番環境を使用する, the Sync ServiceはGitHub SecretsからTURSO_DATABASE_URLとTURSO_AUTH_TOKENを取得する
5. The Sync ServiceはTurso認証トークン（TURSO_AUTH_TOKEN）を安全に管理する

### Requirement 7: エラーハンドリングとログ記録

**Objective:** システム管理者として、同期処理のエラーと実行状況を把握したい。これにより、問題の迅速な検知と対応を可能にする。

#### Acceptance Criteria

1. When CSVデータのダウンロードが失敗する, the Sync Serviceはエラーメッセージをログに記録し、適切なエラーコードで終了する
2. When データベース接続が失敗する, the Sync Serviceはエラーメッセージをログに記録し、再試行を試みる
3. When データ検証エラーが発生する, the Sync Serviceは該当レコードをスキップし、エラー内容をログに記録する
4. The Sync Serviceは各同期実行の開始時刻、終了時刻、処理時間をログに記録する
5. The Sync Serviceはログレベル（DEBUG、INFO、WARNING、ERROR）を環境変数で制御可能にする
6. When 同期処理が失敗する, the GitHub Actions WorkflowはSlackまたはメールで通知を送信する（オプション）

### Requirement 8: データ検証

**Objective:** データ品質管理者として、Spreadsheetから取得したデータの妥当性を検証したい。これにより、不正なデータがデータベースに格納されることを防ぐ。

#### Acceptance Criteria

1. When 楽曲データを処理する, the Sync ServiceはIDフィールドが空でないことを検証する
2. When カードデータを処理する, the Sync ServiceはIDフィールドとcardIDフィールドが空でないことを検証する
3. When 固有ブローチデータを処理する, the Sync ServiceはIDフィールドとcardIDフィールドが空でないことを検証する
4. When 数値フィールドを処理する, the Sync Serviceは数値型への変換が可能かを検証する
5. When 検証エラーが発生する, the Sync Serviceは該当レコードをスキップし、詳細なエラー情報をログに記録する
6. The Sync Serviceは検証ルールを設定ファイルまたはコードで定義可能にする

### Requirement 9: パフォーマンスと効率性

**Objective:** システム管理者として、大量のデータを効率的に処理したい。これにより、同期処理の実行時間を最小化し、リソース使用を最適化する。

#### Acceptance Criteria

1. The Sync Serviceはバッチ処理を使用して、複数レコードを一度にデータベースに挿入する
2. When 大量のデータを処理する, the Sync Serviceはメモリ使用量を監視し、必要に応じてチャンク処理を行う
3. The Sync Serviceはデータベースインデックスを適切に使用して、クエリパフォーマンスを最適化する
4. When 同期処理が30分以内に完了しない, the Sync Serviceはタイムアウトし、警告をログに記録する

### Requirement 10: セキュリティとアクセス制御

**Objective:** セキュリティ管理者として、認証情報と機密データを安全に管理したい。これにより、不正アクセスとデータ漏洩を防ぐ。

#### Acceptance Criteria

1. The Sync ServiceはTursoの認証トークンをGitHub Secretsまたは環境変数から取得する
2. The Sync Serviceは認証情報（TURSO_AUTH_TOKEN）をログに出力しない
3. The Sync Serviceは認証情報をコード内にハードコードしない
4. The Sync Serviceは最小権限の原則に従い、必要なアクセス権限のみを要求する
5. When 認証情報が無効または期限切れである, the Sync Serviceは明確なエラーメッセージを提供する
6. The Sync ServiceはSpreadsheetに対してCSVエクスポートURL（公開アクセス）を使用するため、Google認証は不要である

### Requirement 11: テスト容易性

**Objective:** 開発者として、Docker環境で本番環境と同じ条件で同期機能を検証したい。これにより、環境差異による問題を防ぎ、コード品質を維持する。

#### Acceptance Criteria

1. The Sync Serviceはユニットテストを含み、主要な関数とモジュールをカバーする
2. The Sync Serviceは統合テストを含み、エンドツーエンドの同期フローを検証する
3. The Development EnvironmentはDocker環境で実際のSpreadsheet CSVエクスポートと実際のTursoデータベースを使用してテストする
4. The Development EnvironmentはGitHub Actionsと同一の環境変数（.env）を使用してテストする
5. When テストが実行される, the Sync Serviceはテストカバレッジレポートを生成する
6. The Development Environmentはdocker-compose upで同期処理を実行し、結果を検証できる

### Requirement 12: ドキュメンテーション

**Objective:** 開発者および運用管理者として、システムのセットアップと運用方法を理解したい。これにより、迅速なオンボーディングとトラブルシューティングを可能にする。

#### Acceptance Criteria

1. The ProjectはREADME.mdを含み、プロジェクトの概要、目的、主要機能を説明する
2. The ProjectはSETUP.mdまたはREADME内にセットアップ手順を含み、ローカル開発環境の構築方法を説明する
3. The Projectは環境変数のリストと説明を含むドキュメントを提供する
4. The Projectはデータベーススキーマのドキュメントを提供する
5. The ProjectはGitHub Actionsワークフローの設定方法を説明するドキュメントを提供する
6. The Projectはトラブルシューティングガイドを含み、一般的な問題と解決方法を説明する

