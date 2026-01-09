# トラブルシューティングガイド

## 一般的な問題と解決方法

### 環境変数エラー

#### エラー: `Environment variables TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are required`

**原因**: 必要な環境変数が設定されていません。

**解決方法**:

1. `.env`ファイルが存在することを確認:

   ```bash
   ls -la .env
   ```

2. `.env`ファイルに必要な変数が含まれているか確認:

   ```bash
   cat .env
   ```

   以下の形式で設定されている必要があります:

   ```bash
   TURSO_DATABASE_URL=libsql://your-database.turso.io
   TURSO_AUTH_TOKEN=your-auth-token
   SPREADSHEET_ID=your-spreadsheet-id
   ```

3. Docker Composeを使用している場合、`docker-compose.yml`で`.env`ファイルが正しくロードされているか確認

### データベース接続エラー

#### エラー: `Failed to connect to Turso`

**原因**: Tursoデータベースへの接続に失敗しました。

**解決方法**:

1. **認証情報の確認**:
   - `TURSO_DATABASE_URL`が正しい形式か確認（`libsql://`で始まる）
   - `TURSO_AUTH_TOKEN`が有効か確認

2. **ネットワーク接続の確認**:

   ```bash
   curl -I https://your-database.turso.io
   ```

3. **Tursoダッシュボードで確認**:
   - データベースが稼働中か確認
   - 認証トークンが期限切れでないか確認

#### エラー: `Transaction failed: ...`

**原因**: データベーストランザクションが失敗しました。

**解決方法**:

1. **ログレベルをDEBUGに設定**して詳細を確認:

   ```bash
   LOG_LEVEL=DEBUG python src/main.py
   ```

2. **テーブルスキーマの確認**:
   - Tursoダッシュボードでテーブルが存在するか確認
   - カラム名とデータ型が一致しているか確認

3. **接続数の確認**:
   - Tursoの接続数制限に達していないか確認

### CSV取得エラー

#### エラー: `CSV fetch failed: HTTP 404`

**原因**: Google SpreadsheetのCSVエクスポートURLが見つかりません。

**解決方法**:

1. **SPREADSHEET_IDの確認**:
   - SpreadsheetのURLから正しいIDをコピー
   - `https://docs.google.com/spreadsheets/d/[ここがID]/edit`

2. **Spreadsheetの公開設定確認**:
   - Spreadsheetが「リンクを知っている全員」に共有されているか確認
   - 各シートのGIDが正しいか確認（`constants.py`）

3. **GID定数の確認**:

   ```python
   # src/constants.py
   SONGS_GID = 1083871743
   CARDS_GID = 480354522
   BROOCHES_GID = 1087762308
   ```

#### エラー: `CSV fetch failed: Request timeout`

**原因**: ネットワークタイムアウトが発生しました。

**解決方法**:

1. **ネットワーク接続の確認**:

   ```bash
   ping docs.google.com
   ```

2. **タイムアウト値の調整**（必要に応じて`csv_fetcher.py`を編集）

3. **リトライ回数の確認**: デフォルトで3回リトライされます

### データ検証エラー

#### エラー: `Data validation failed: ...`

**原因**: Spreadsheetのデータが検証ルールに違反しています。

**解決方法**:

1. **ログで具体的なエラーを確認**:

   ```bash
   docker-compose logs | grep "validation error"
   ```

2. **楽曲データの検証ルール**:
   - `ID`カラムが空でないこと
   - 数値カラムが適切な型であること

3. **カードデータの検証ルール**:
   - `ID`と`cardID`が空でないこと
   - `rarity`が`UR`, `SSR`, `SR`, `R`のいずれかであること

4. **ブローチデータの検証ルール**:
   - `ID`と`cardID`が空でないこと
   - `score`が非負の数値であること

5. **Spreadsheetのデータを修正**して再実行

### Docker関連の問題

#### エラー: `docker: Cannot connect to the Docker daemon`

**原因**: Dockerデーモンが起動していません。

**解決方法**:

1. **Dockerを起動**:
   - Docker Desktopを起動（Mac/Windows）
   - Linuxの場合: `sudo systemctl start docker`

2. **Dockerの状態確認**:

   ```bash
   docker ps
   ```

#### エラー: `docker-compose: command not found`

**原因**: docker-composeがインストールされていません。

**解決方法**:

1. **Docker Composeのインストール確認**:

   ```bash
   docker compose version
   ```

   または

   ```bash
   docker-compose version
   ```

2. Docker Compose V2を使用している場合は、スペースで区切ってください:

   ```bash
   docker compose up  # V2
   # vs
   docker-compose up  # V1
   ```

### GitHub Actions関連の問題

#### エラー: `Sync failed in GitHub Actions`

**原因**: GitHub Actionsでの同期が失敗しました。

**解決方法**:

1. **GitHub Secretsの確認**:
   - Settings > Secrets and variables > Actions
   - 必要なSecrets（`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `SPREADSHEET_ID`）が設定されているか確認

2. **ワークフローログの確認**:
   - Actions タブでワークフローの詳細ログを確認
   - エラーメッセージを特定

3. **手動トリガーでテスト**:
   - Actions > Sync Spreadsheet to Database > Run workflow
   - 手動実行で問題を特定

## デバッグ方法

### ログレベルの調整

より詳細なログを出力するには、`LOG_LEVEL`を`DEBUG`に設定:

```bash
LOG_LEVEL=DEBUG docker-compose up
```

### ローカルでのテスト実行

本番環境にデプロイする前に、ローカルでテスト:

```bash
# ユニットテストの実行
docker run --rm i7-datasync-test python -m pytest tests/ -v

# 実際のデータを使用した統合テスト
docker-compose run sync
```

### 特定のテーブルのみ同期

`src/main.py`を一時的に編集して、特定のテーブルのみ同期:

```python
# デバッグ用: songsテーブルのみ同期
sheet_configs = {
    "songs": SONGS_GID,
    # "cards": CARDS_GID,  # コメントアウト
    # "brooches": BROOCHES_GID,  # コメントアウト
}
```

### データベースの直接確認

Turso CLIを使用してデータを直接確認:

```bash
# Turso CLIのインストール（未インストールの場合）
brew install tursodatabase/tap/turso  # Mac
# または
curl -sSfL https://get.tur.so/install.sh | bash  # Linux

# データベースに接続
turso db shell your-database-name

# テーブルの確認
sqlite> .tables

# データの確認
sqlite> SELECT COUNT(*) FROM songs;
sqlite> SELECT * FROM cards LIMIT 5;
```

## よくある質問

### Q: 同期が1時間ごとに実行されない

**A**: GitHub Actionsのcron実行は保証されたタイミングではありません。負荷が高い時間帯は遅延する可能性があります。手動トリガーを使用するか、より頻繁なスケジュール（例: 30分ごと）を設定してください。

### Q: 一部のデータのみ更新したい

**A**: 現在の実装は全削除→全挿入パターンです。特定のデータのみ更新する場合は、コードの修正が必要です。または、Spreadsheet側でデータを管理し、完全同期を利用してください。

### Q: 大量のデータでタイムアウトが発生する

**A**: `orchestrator.py`のタイムアウト設定（デフォルト30分）を調整するか、データを分割して同期してください。

### Q: Docker環境でのパフォーマンスが悪い

**A**:
1. Dockerに割り当てられているリソース（CPU、メモリ）を増やす
2. Docker Desktopの設定で「Use gRPC FUSE for file sharing」を有効化（Mac）
3. ボリュームマウントを最小限にする

## サポート

問題が解決しない場合：

1. **GitHubでIssueを作成**: 詳細なエラーメッセージとログを含めてください
2. **ログを添付**: `LOG_LEVEL=DEBUG`で実行したログ全体を添付
3. **環境情報を提供**:
   - OS/プラットフォーム
   - Docker/Python バージョン
   - エラーが発生した状況

## Sources

Web search results were used to identify alternative Turso Python clients:
- [turso-python · PyPI](https://pypi.org/project/turso-python/)
- [libsql-client-py · GitHub](https://github.com/tursodatabase/libsql-client-py)
- [Bring Your Own SDK with Turso's HTTP API](https://turso.tech/blog/bring-your-own-sdk-with-tursos-http-api-ff4ccbed)
