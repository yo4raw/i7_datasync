"""SchemaManagerモジュール - データベーススキーマ管理"""

import re
from typing import Dict
import pandas as pd

from db_client import DatabaseClient
from logger import get_logger

logger = get_logger(__name__)


class SchemaCreationError(Exception):
    """スキーマ作成エラー"""
    pass


class SchemaManager:
    """スキーマ管理サービス"""

    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client

    def ensure_table_exists(self, table_name: str, df: pd.DataFrame) -> None:
        """
        テーブルが存在しない場合は作成（既存の場合は削除して再作成）

        Args:
            table_name: テーブル名
            df: スキーマ推測用のDataFrame

        Raises:
            SchemaCreationError: テーブル作成失敗時
        """
        try:
            logger.info(f"Ensuring table exists: {table_name}")

            column_types = self.infer_column_types(df)
            columns_def = []

            for column_name, sql_type in column_types.items():
                # カラム名をバッククォートで囲む
                quoted_name = f"`{column_name}`"

                if column_name == 'ID':
                    columns_def.append(f"{quoted_name} {sql_type} PRIMARY KEY")
                else:
                    columns_def.append(f"{quoted_name} {sql_type}")

            # 既存のテーブルを削除して再作成（スキーマ変更を反映）
            drop_table_sql = f"DROP TABLE IF EXISTS {table_name}"
            self.db_client.execute_query(drop_table_sql)
            logger.info(f"Dropped existing table {table_name} if it existed")

            create_table_sql = f"""
            CREATE TABLE {table_name} (
                {', '.join(columns_def)}
            )
            """

            self.db_client.execute_query(create_table_sql)

            logger.info(f"Table {table_name} created successfully")

        except Exception as e:
            logger.error(f"Failed to ensure table {table_name}: {e}")
            raise SchemaCreationError(f"Failed to ensure table {table_name}: {e}")

    def infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        DataFrameからカラム型を推測

        Args:
            df: DataFrame

        Returns:
            {"column_name": "SQL_TYPE"}（例: {"ID": "INTEGER", "name": "TEXT"}）
        """
        type_mapping = {
            'int64': 'INTEGER',
            'int32': 'INTEGER',
            'float64': 'REAL',
            'float32': 'REAL',
            'object': 'TEXT',
            'bool': 'INTEGER',
            'datetime64[ns]': 'TEXT'
        }

        column_types = {}
        for column in df.columns:
            dtype_str = str(df[column].dtype)
            sql_type = type_mapping.get(dtype_str, 'TEXT')
            column_types[column] = sql_type

        return column_types

    def _sanitize_column_name(self, column_name: str) -> str:
        """
        カラム名をサニタイズ（SQLインジェクション防止）

        Args:
            column_name: 元のカラム名

        Returns:
            サニタイズされたカラム名
        """
        # アルファベット、数字、アンダースコア、日本語文字のみ許可
        # それ以外は削除
        sanitized = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '_', column_name)
        return sanitized
