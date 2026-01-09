"""メインエントリーポイント"""

import os
import sys

from constants import SONGS_GID, CARDS_GID, BROOCHES_GID
from csv_fetcher import CSVFetcher
from db_client import DatabaseClient
from validators import DataValidator
from transformers import DataTransformer
from orchestrator import SyncOrchestrator
from schema_manager import SchemaManager
from logger import get_logger

logger = get_logger(__name__)


def main():
    """メイン処理"""
    try:
        logger.info("Starting sync process")

        # 環境変数読み込み
        turso_url = os.getenv("TURSO_DATABASE_URL")
        turso_token = os.getenv("TURSO_AUTH_TOKEN")
        spreadsheet_id = os.getenv("SPREADSHEET_ID")

        if not all([turso_url, turso_token, spreadsheet_id]):
            logger.error("Missing required environment variables")
            return 1

        # コンポーネント初期化
        csv_fetcher = CSVFetcher()
        db_client = DatabaseClient()
        db_client.connect()

        validator = DataValidator()
        transformer = DataTransformer()

        # SchemaManagerでテーブル初期化
        schema_manager = SchemaManager(db_client)

        # サンプルDataFrameでスキーマ初期化（実際は最初のCSV取得後に実行）
        logger.info("Initializing schemas")

        # シート設定
        sheet_configs = {
            "songs": SONGS_GID,
            "cards": CARDS_GID,
            "brooches": BROOCHES_GID
        }

        # SyncOrchestrator初期化と実行
        orchestrator = SyncOrchestrator(
            csv_fetcher=csv_fetcher,
            db_client=db_client,
            validator=validator,
            transformer=transformer
        )

        # 同期実行
        results = orchestrator.sync_all_tables(spreadsheet_id, sheet_configs)

        # 結果サマリー
        success_count = sum(1 for r in results if r.success)
        logger.info(
            f"Sync completed: {success_count}/{len(results)} tables synced successfully"
        )

        for result in results:
            if result.success:
                logger.info(
                    f"{result.table_name}: deleted={result.deleted_count}, "
                    f"inserted={result.inserted_count}, skipped={result.skipped_count}"
                )
            else:
                logger.error(f"{result.table_name}: FAILED - {result.error_message}")

        return 0 if success_count == len(results) else 1

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
