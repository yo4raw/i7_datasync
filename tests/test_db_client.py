"""DatabaseClientのユニットテスト"""

import pytest
import os
from unittest.mock import patch, Mock, MagicMock

import sys
sys.path.insert(0, '/Users/yaoko/git/i7_datasync/src')

from db_client import DatabaseClient, DatabaseConnectionError, DatabaseTransactionError


class TestDatabaseClient:
    """DatabaseClientクラスのテスト"""

    def test_init_with_env_variables(self):
        """環境変数から接続情報を取得"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io',
            'TURSO_AUTH_TOKEN': 'test_token'
        }):
            client = DatabaseClient()
            assert client.database_url == 'libsql://test.turso.io'
            assert client.auth_token == 'test_token'

    def test_init_without_env_variables(self):
        """環境変数未設定時にエラー"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                DatabaseClient()

    @patch('libsql_client.create_client_sync')
    def test_connect_success(self, mock_create_client):
        """接続成功"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io',
            'TURSO_AUTH_TOKEN': 'test_token'
        }):
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            client = DatabaseClient()
            client.connect()

            assert client.client is not None
            mock_create_client.assert_called_once()

    @patch('libsql_client.create_client_sync')
    def test_execute_transaction_success(self, mock_create_client):
        """トランザクション成功"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io',
            'TURSO_AUTH_TOKEN': 'test_token'
        }):
            mock_client = Mock()

            # batch()結果のモック
            mock_delete_result = Mock()
            mock_delete_result.rows_affected = 10

            mock_insert_result1 = Mock()
            mock_insert_result1.rows_affected = 1

            mock_insert_result2 = Mock()
            mock_insert_result2.rows_affected = 1

            # batch()の戻り値を設定
            mock_client.batch.return_value = [mock_delete_result, mock_insert_result1, mock_insert_result2]
            mock_create_client.return_value = mock_client

            client = DatabaseClient()
            client.connect()

            delete_query = "DELETE FROM test_table"
            insert_statements = ["INSERT INTO test_table VALUES (1)", "INSERT INTO test_table VALUES (2)"]

            result = client.execute_transaction(delete_query, insert_statements)

            assert result['deleted'] == 10
            assert result['inserted'] == 2

    @patch('libsql_client.create_client_sync')
    def test_execute_transaction_failure_rollback(self, mock_create_client):
        """トランザクション失敗時のロールバック"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io',
            'TURSO_AUTH_TOKEN': 'test_token'
        }):
            mock_client = Mock()
            mock_client.batch.side_effect = Exception("Transaction error")
            mock_create_client.return_value = mock_client

            client = DatabaseClient()
            client.connect()

            delete_query = "DELETE FROM test_table"
            insert_statements = ["INSERT INTO test_table VALUES (1)"]

            with pytest.raises(DatabaseTransactionError):
                client.execute_transaction(delete_query, insert_statements)
