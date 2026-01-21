"""SyncOrchestratorモジュール - 同期処理オーケストレーション"""

from typing import Dict, List
from dataclasses import dataclass
import time

from csv_fetcher import CSVFetcher
from db_client import DatabaseClient
from validators import DataValidator
from transformers import DataTransformer
from schema_manager import SchemaManager
from logger import get_logger

logger = get_logger(__name__)


@dataclass
class SyncResult:
    """同期結果"""
    table_name: str
    deleted_count: int
    inserted_count: int
    skipped_count: int
    success: bool
    error_message: str = ""


class SyncTimeoutError(Exception):
    """同期タイムアウトエラー"""
    pass


class SyncOrchestrator:
    """同期処理オーケストレーター"""

    def __init__(
        self,
        csv_fetcher: CSVFetcher,
        db_client: DatabaseClient,
        validator: DataValidator,
        transformer: DataTransformer,
        timeout_seconds: int = 1800  # 30分
    ):
        self.csv_fetcher = csv_fetcher
        self.db_client = db_client
        self.validator = validator
        self.transformer = transformer
        self.schema_manager = SchemaManager(db_client)
        self.timeout_seconds = timeout_seconds

    def sync_all_tables(
        self,
        spreadsheet_id: str,
        sheet_configs: Dict[str, int]
    ) -> List[SyncResult]:
        """
        全テーブルを同期

        Args:
            spreadsheet_id: SpreadsheetのID
            sheet_configs: {"songs": gid, "cards": gid, "brooches": gid}

        Returns:
            各テーブルの同期結果リスト

        Raises:
            SyncTimeoutError: 30分以内に完了しない場合
        """
        start_time = time.time()
        results = []

        logger.info(f"Starting sync for all tables")

        for table_name, gid in sheet_configs.items():
            # タイムアウトチェック
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                logger.warning(f"Sync timeout after {elapsed:.1f} seconds")
                raise SyncTimeoutError(f"Sync timeout after {elapsed:.1f} seconds")

            result = self.sync_single_table(table_name, gid, spreadsheet_id)
            results.append(result)

        total_elapsed = time.time() - start_time
        logger.info(f"Sync completed in {total_elapsed:.1f} seconds")

        return results

    def sync_single_table(
        self,
        table_name: str,
        gid: int,
        spreadsheet_id: str
    ) -> SyncResult:
        """
        単一テーブルを同期

        Args:
            table_name: テーブル名（songs/cards/brooches）
            gid: シートのgid
            spreadsheet_id: SpreadsheetのID

        Returns:
            同期結果
        """
        try:
            logger.info(f"Syncing table: {table_name}")

            # 1. CSVデータ取得
            # Songs: header=1 (row 2), Cards/Brooches: header=0 (row 1)
            if table_name == 'songs':
                df = self.csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, gid, header=1)
            else:
                df = self.csv_fetcher.fetch_csv_as_dataframe(spreadsheet_id, gid, header=0)

            # 2. データ検証
            if table_name == 'songs':
                valid_df, errors = self.validator.validate_songs_data(df)
            elif table_name == 'cards':
                valid_df, errors = self.validator.validate_cards_data(df)
            elif table_name == 'brooches':
                valid_df, errors = self.validator.validate_brooches_data(df)
            else:
                raise ValueError(f"Unknown table: {table_name}")

            skipped_count = len(df) - len(valid_df)

            # 3. データ変換
            transformed_df = self.transformer.transform_for_database(valid_df, table_name=table_name)

            # 4. テーブル作成（存在しない場合） - 変換後のDataFrameを使用
            self.schema_manager.ensure_table_exists(table_name, transformed_df)

            # 5. データベース同期
            delete_query = f"DELETE FROM {table_name}"
            insert_statements = self._build_insert_statements(table_name, transformed_df)

            result = self.db_client.execute_transaction(delete_query, insert_statements)

            return SyncResult(
                table_name=table_name,
                deleted_count=result['deleted'],
                inserted_count=result['inserted'],
                skipped_count=skipped_count,
                success=True
            )

        except Exception as e:
            logger.error(f"Sync failed for {table_name}: {e}")
            return SyncResult(
                table_name=table_name,
                deleted_count=0,
                inserted_count=0,
                skipped_count=0,
                success=False,
                error_message=str(e)
            )

    def _build_insert_statements(self, table_name: str, df) -> List[str]:
        """INSERT文のリストを構築"""
        import pandas as pd
        import math

        statements = []
        columns = list(df.columns)
        # カラム名をバッククォートで囲む
        quoted_columns = [f'`{col}`' for col in columns]

        for _, row in df.iterrows():
            # 値を適切にエスケープしてSQL文を構築
            values = []
            for col in columns:
                val = row[col]
                if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
                    values.append('NULL')
                elif isinstance(val, (int, float)):
                    # floatの場合、inf/-inf/nanをNULLに変換
                    if math.isinf(val) or math.isnan(val):
                        values.append('NULL')
                    else:
                        values.append(str(val))
                else:
                    # 文字列値をシングルクォートでエスケープ
                    escaped_val = str(val).replace("'", "''")
                    values.append(f"'{escaped_val}'")

            stmt = f"INSERT INTO {table_name} ({', '.join(quoted_columns)}) VALUES ({', '.join(values)})"
            statements.append(stmt)

        return statements
