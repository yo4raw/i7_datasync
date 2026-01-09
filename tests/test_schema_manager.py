"""SchemaManagerのユニットテスト"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, '/Users/yaoko/git/i7_datasync/src')

from schema_manager import SchemaManager


class TestSchemaManager:
    """SchemaManagerクラスのテスト"""

    def test_infer_column_types_basic(self):
        """基本的な型推測"""
        mock_db_client = Mock()
        manager = SchemaManager(mock_db_client)

        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'score': [95.5, 87.3, 92.1]
        })

        column_types = manager.infer_column_types(df)

        assert column_types['id'] == 'INTEGER'
        assert column_types['name'] == 'TEXT'
        assert column_types['score'] == 'REAL'

    def test_ensure_table_exists(self):
        """テーブル作成"""
        mock_db_client = Mock()
        manager = SchemaManager(mock_db_client)

        df = pd.DataFrame({
            'ID': [1, 2],
            'name': ['test1', 'test2']
        })

        manager.ensure_table_exists('test_table', df)

        # CREATE TABLE文が実行されたことを確認
        mock_db_client.execute_query.assert_called_once()
        call_args = mock_db_client.execute_query.call_args[0][0]
        assert 'CREATE TABLE IF NOT EXISTS' in call_args
        assert 'test_table' in call_args
        assert 'ID INTEGER PRIMARY KEY' in call_args
