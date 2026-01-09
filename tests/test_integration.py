"""統合テスト - 完全同期フローの検証

このテストは実際のSpreadsheet CSVエクスポートと実際のTursoデータベースを使用します。
実行には .env ファイルに以下の環境変数が必要です:
- TURSO_DATABASE_URL
- TURSO_AUTH_TOKEN
- SPREADSHEET_ID
- LOG_LEVEL (オプション)

実行方法:
    docker-compose run --rm sync pytest tests/test_integration.py -v
"""

import pytest
import os
import sys
import pandas as pd
from typing import Dict, List

sys.path.insert(0, '/Users/yaoko/git/i7_datasync/src')

from csv_fetcher import CSVFetcher
from db_client import DatabaseClient
from schema_manager import SchemaManager
from validators import DataValidator
from transformers import DataTransformer
from orchestrator import SyncOrchestrator
from constants import SONGS_GID, CARDS_GID, BROOCHES_GID
from logger import get_logger

logger = get_logger(__name__)


class TestIntegration:
    """統合テストクラス"""

    @pytest.fixture(scope="class")
    def env_vars(self):
        """環境変数の検証"""
        required_vars = ["TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN", "SPREADSHEET_ID"]
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            pytest.skip(f"Missing required environment variables: {', '.join(missing)}")

        return {
            "database_url": os.getenv("TURSO_DATABASE_URL"),
            "auth_token": os.getenv("TURSO_AUTH_TOKEN"),
            "spreadsheet_id": os.getenv("SPREADSHEET_ID"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }

    @pytest.fixture(scope="class")
    def components(self, env_vars):
        """テスト用コンポーネントの初期化"""
        csv_fetcher = CSVFetcher()
        db_client = DatabaseClient(
            database_url=env_vars["database_url"],
            auth_token=env_vars["auth_token"]
        )
        db_client.connect()

        schema_manager = SchemaManager(db_client)
        validator = DataValidator()
        transformer = DataTransformer()

        orchestrator = SyncOrchestrator(
            csv_fetcher=csv_fetcher,
            db_client=db_client,
            validator=validator,
            transformer=transformer
        )

        return {
            "csv_fetcher": csv_fetcher,
            "db_client": db_client,
            "schema_manager": schema_manager,
            "validator": validator,
            "transformer": transformer,
            "orchestrator": orchestrator,
            "spreadsheet_id": env_vars["spreadsheet_id"]
        }

    def test_csv_fetch_from_real_spreadsheet(self, components):
        """実際のSpreadsheetからCSV取得テスト"""
        csv_fetcher = components["csv_fetcher"]
        spreadsheet_id = components["spreadsheet_id"]

        # 楽曲データ取得
        logger.info("Testing CSV fetch for songs sheet")
        songs_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, SONGS_GID)
        assert songs_df is not None
        assert len(songs_df) > 0
        assert "id" in songs_df.columns
        logger.info(f"Songs data fetched: {len(songs_df)} records")

        # カードデータ取得
        logger.info("Testing CSV fetch for cards sheet")
        cards_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, CARDS_GID)
        assert cards_df is not None
        assert len(cards_df) > 0
        assert "id" in cards_df.columns
        logger.info(f"Cards data fetched: {len(cards_df)} records")

        # 固有ブローチデータ取得
        logger.info("Testing CSV fetch for brooches sheet")
        brooches_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, BROOCHES_GID)
        assert brooches_df is not None
        assert len(brooches_df) > 0
        assert "id" in brooches_df.columns
        logger.info(f"Brooches data fetched: {len(brooches_df)} records")

    def test_database_connection(self, components):
        """Tursoデータベース接続テスト"""
        db_client = components["db_client"]

        # 接続確認のため簡単なクエリを実行
        try:
            result = db_client.client.execute("SELECT 1 as test")
            assert result is not None
            logger.info("Database connection test passed")
        except Exception as e:
            pytest.fail(f"Database connection failed: {str(e)}")

    def test_schema_initialization(self, components):
        """スキーマ初期化テスト"""
        schema_manager = components["schema_manager"]
        csv_fetcher = components["csv_fetcher"]
        spreadsheet_id = components["spreadsheet_id"]

        # 各テーブルのスキーマを初期化
        sheets = {
            "songs": SONGS_GID,
            "cards": CARDS_GID,
            "brooches": BROOCHES_GID
        }

        for table_name, gid in sheets.items():
            logger.info(f"Initializing schema for {table_name}")
            df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, gid)
            schema_manager.ensure_table_exists(table_name, df)
            logger.info(f"Schema for {table_name} initialized successfully")

    def test_single_table_sync(self, components):
        """単一テーブル同期テスト（楽曲）"""
        orchestrator = components["orchestrator"]
        spreadsheet_id = components["spreadsheet_id"]

        logger.info("Testing single table sync for songs")
        result = orchestrator.sync_single_table("songs", SONGS_GID, spreadsheet_id)

        assert result is not None
        assert result.success is True
        assert result.table_name == "songs"
        assert result.inserted_count >= 0
        assert result.error_message is None

        logger.info(f"Sync result: deleted={result.deleted_count}, "
                   f"inserted={result.inserted_count}, skipped={result.skipped_count}")

    def test_full_sync_workflow(self, components):
        """完全同期フローテスト（3テーブル全体）"""
        orchestrator = components["orchestrator"]
        spreadsheet_id = components["spreadsheet_id"]

        sheet_configs = {
            "songs": SONGS_GID,
            "cards": CARDS_GID,
            "brooches": BROOCHES_GID
        }

        logger.info("Starting full sync workflow test")
        results = orchestrator.sync_all_tables(spreadsheet_id, sheet_configs)

        assert results is not None
        assert len(results) == 3

        # 各テーブルの同期結果を検証
        for result in results:
            logger.info(f"Table: {result.table_name}, Success: {result.success}, "
                       f"Inserted: {result.inserted_count}, Deleted: {result.deleted_count}, "
                       f"Skipped: {result.skipped_count}")
            assert result.success is True, f"Sync failed for {result.table_name}: {result.error_message}"
            assert result.inserted_count >= 0

        logger.info("Full sync workflow test completed successfully")

    def test_data_validation_during_sync(self, components):
        """同期中のデータ検証テスト"""
        validator = components["validator"]
        csv_fetcher = components["csv_fetcher"]
        spreadsheet_id = components["spreadsheet_id"]

        # 楽曲データの検証
        logger.info("Testing data validation for songs")
        songs_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, SONGS_GID)
        validated_songs, errors = validator.validate_songs_data(songs_df)

        assert validated_songs is not None
        assert len(validated_songs) <= len(songs_df)
        logger.info(f"Songs validation: {len(validated_songs)} valid records, {len(errors)} errors")

        # カードデータの検証
        logger.info("Testing data validation for cards")
        cards_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, CARDS_GID)
        validated_cards, errors = validator.validate_cards_data(cards_df)

        assert validated_cards is not None
        assert len(validated_cards) <= len(cards_df)
        logger.info(f"Cards validation: {len(validated_cards)} valid records, {len(errors)} errors")

        # 固有ブローチデータの検証
        logger.info("Testing data validation for brooches")
        brooches_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, BROOCHES_GID)
        validated_brooches, errors = validator.validate_brooches_data(brooches_df)

        assert validated_brooches is not None
        assert len(validated_brooches) <= len(brooches_df)
        logger.info(f"Brooches validation: {len(validated_brooches)} valid records, {len(errors)} errors")

    def test_data_integrity_after_sync(self, components):
        """同期後のデータ整合性テスト"""
        db_client = components["db_client"]
        csv_fetcher = components["csv_fetcher"]
        spreadsheet_id = components["spreadsheet_id"]

        # 楽曲データの整合性チェック
        logger.info("Testing data integrity for songs table")
        songs_df = csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, SONGS_GID)
        db_result = db_client.client.execute("SELECT COUNT(*) as count FROM songs")
        db_count = db_result.rows[0][0]

        # DBのレコード数がSpreadsheetのレコード数と近いことを確認（検証でスキップされるレコードがある可能性を考慮）
        assert db_count > 0
        assert db_count <= len(songs_df)
        logger.info(f"Songs integrity check: Spreadsheet={len(songs_df)}, Database={db_count}")

    def test_error_handling_and_logging(self, components):
        """エラーハンドリングとログ記録テスト"""
        orchestrator = components["orchestrator"]

        # 無効なGIDでの同期を試行（エラーハンドリングを確認）
        logger.info("Testing error handling with invalid GID")
        result = orchestrator.sync_single_table("test_table", 9999999, "invalid_spreadsheet_id")

        assert result is not None
        assert result.success is False
        assert result.error_message is not None
        logger.info(f"Error handling test completed: {result.error_message}")

    def test_transaction_rollback_on_failure(self, components):
        """トランザクション失敗時のロールバックテスト"""
        db_client = components["db_client"]

        # 意図的に失敗するトランザクションを実行
        logger.info("Testing transaction rollback on failure")

        # まず現在のレコード数を取得
        before_result = db_client.client.execute("SELECT COUNT(*) as count FROM songs")
        before_count = before_result.rows[0][0]

        try:
            # 無効なINSERT文でトランザクション失敗をシミュレート
            db_client.execute_transaction(
                "DELETE FROM songs",
                ["INSERT INTO songs (id, invalid_column) VALUES (1, 'test')"]  # invalid_columnは存在しない
            )
            pytest.fail("Expected DatabaseTransactionError was not raised")
        except Exception as e:
            logger.info(f"Transaction failed as expected: {str(e)}")

        # ロールバック後、レコード数が変わっていないことを確認
        after_result = db_client.client.execute("SELECT COUNT(*) as count FROM songs")
        after_count = after_result.rows[0][0]

        assert before_count == after_count
        logger.info(f"Transaction rollback verified: count remained {after_count}")
