"""DatabaseClientモジュール - Tursoデータベース接続"""

import os
from typing import List, Dict, Any, Optional
import requests

from logger import get_logger

logger = get_logger(__name__)


class DatabaseConnectionError(Exception):
    """データベース接続エラー"""
    pass


class DatabaseTransactionError(Exception):
    """トランザクションエラー"""
    pass


class DatabaseClient:
    """Tursoデータベースクライアント（HTTP API経由）"""

    def __init__(self):
        """環境変数（TURSO_DATABASE_URL、TURSO_AUTH_TOKEN）から接続情報を取得"""
        database_url = os.getenv("TURSO_DATABASE_URL")
        self.auth_token = os.getenv("TURSO_AUTH_TOKEN")

        if not database_url or not self.auth_token:
            raise ValueError(
                "Environment variables TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are required"
            )

        # libsql:// を https:// に変換してHTTPエンドポイントを構築
        if database_url.startswith("libsql://"):
            host = database_url.replace("libsql://", "")
            self.http_url = f"https://{host}"
        elif database_url.startswith("https://"):
            self.http_url = database_url
        else:
            raise ValueError(f"Invalid database URL format: {database_url}")

    def connect(self) -> None:
        """
        Tursoデータベースに接続（HTTP API使用）

        Raises:
            DatabaseConnectionError: 接続失敗時
        """
        try:
            logger.info("Connecting to Turso database via HTTP API")

            # Turso HTTP APIはステートレスなので接続テストを実行
            response = requests.post(
                self.http_url,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                json={"statements": ["SELECT 1"]},
                timeout=10
            )
            response.raise_for_status()

            logger.info("Successfully connected to Turso database")

        except Exception as e:
            logger.error(f"Failed to connect to Turso: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Turso: {e}")

    def execute_transaction(
        self,
        delete_query: str,
        insert_statements: List[str],
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        トランザクション内で削除とバッチ挿入を実行

        大量のINSERT文をバッチに分割して実行することでタイムアウトを防ぐ

        Args:
            delete_query: DELETE文（例: "DELETE FROM songs"）
            insert_statements: INSERT文のリスト
            batch_size: 1バッチあたりのINSERT文数（デフォルト: 50）

        Returns:
            {"deleted": N, "inserted": M}

        Raises:
            DatabaseTransactionError: トランザクション失敗時
        """
        try:
            logger.info(
                "Executing transaction",
                extra={
                    "context": {
                        "delete_query": delete_query,
                        "insert_count": len(insert_statements),
                        "batch_size": batch_size
                    }
                }
            )

            deleted_count = 0
            inserted_count = 0

            # 1. DELETE実行
            response = requests.post(
                self.http_url,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                json={"statements": [delete_query]},
                timeout=30
            )
            response.raise_for_status()

            delete_result = response.json()
            if isinstance(delete_result, list) and len(delete_result) > 0:
                result = delete_result[0]
                if result and "results" in result and "rows_written" in result["results"]:
                    deleted_count = result["results"]["rows_written"]
                elif result and "error" in result:
                    logger.error(f"DELETE failed: {result['error']}")
                    raise DatabaseTransactionError(f"DELETE failed: {result['error']}")

            logger.info(f"Deleted {deleted_count} rows")

            # 2. INSERT文をバッチに分割して実行
            total_batches = (len(insert_statements) + batch_size - 1) // batch_size

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(insert_statements))
                batch = insert_statements[start_idx:end_idx]

                logger.info(
                    f"Executing batch {batch_idx + 1}/{total_batches}",
                    extra={"context": {"records": f"{start_idx + 1}-{end_idx}"}}
                )

                response = requests.post(
                    self.http_url,
                    headers={
                        "Authorization": f"Bearer {self.auth_token}",
                        "Content-Type": "application/json"
                    },
                    json={"statements": batch},
                    timeout=60
                )
                response.raise_for_status()

                batch_result = response.json()
                if isinstance(batch_result, list):
                    for idx, insert_result in enumerate(batch_result):
                        if insert_result and "results" in insert_result and "rows_written" in insert_result["results"]:
                            inserted_count += insert_result["results"]["rows_written"]
                        elif insert_result and "error" in insert_result:
                            logger.error(f"INSERT failed in batch {batch_idx + 1}, statement {idx + 1}: {insert_result['error']}")
                            raise DatabaseTransactionError(f"INSERT failed: {insert_result['error']}")

            logger.info(
                "Transaction completed successfully",
                extra={
                    "context": {
                        "deleted": deleted_count,
                        "inserted": inserted_count
                    }
                }
            )

            return {
                "deleted": deleted_count,
                "inserted": inserted_count
            }

        except requests.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text if e.response else str(e)}"
            logger.error(
                "Transaction failed",
                extra={"context": {"error": error_msg}}
            )
            raise DatabaseTransactionError(f"Transaction failed: {error_msg}")
        except Exception as e:
            logger.error(
                "Transaction failed",
                extra={"context": {"error": str(e)}}
            )
            raise DatabaseTransactionError(f"Transaction failed: {e}")

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> Any:
        """
        単一クエリを実行

        Args:
            query: SQL文
            params: パラメータ（現在未使用）

        Returns:
            クエリ結果のJSONレスポンス
        """
        try:
            response = requests.post(
                self.http_url,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                json={"statements": [query]},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseTransactionError(f"Query execution failed: {e}")
