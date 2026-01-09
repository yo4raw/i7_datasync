"""パフォーマンステスト - 大量データ処理の検証

このテストは大量データの同期性能を測定します。
目標:
- 処理時間: 30分以内（10,000レコード）
- メモリ使用量: 512MB以内

実行には .env ファイルに以下の環境変数が必要です:
- TURSO_DATABASE_URL
- TURSO_AUTH_TOKEN
- SPREADSHEET_ID
- LOG_LEVEL (オプション)

実行方法:
    docker-compose run --rm sync pytest tests/test_performance.py -v -s
"""

import pytest
import os
import sys
import time
import psutil
import pandas as pd
from typing import Dict, List
import io

sys.path.insert(0, '/Users/yaoko/git/i7_datasync/src')

from csv_fetcher import CSVFetcher
from db_client import DatabaseClient
from schema_manager import SchemaManager
from validators import DataValidator
from transformers import DataTransformer
from orchestrator import SyncOrchestrator
from constants import SONGS_GID
from logger import get_logger

logger = get_logger(__name__)


class TestPerformance:
    """パフォーマンステストクラス"""

    # 性能目標定数
    MAX_PROCESSING_TIME_SECONDS = 30 * 60  # 30分
    MAX_MEMORY_MB = 512  # 512MB

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
            "spreadsheet_id": os.getenv("SPREADSHEET_ID")
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

    @pytest.fixture
    def process(self):
        """現在のプロセス情報"""
        return psutil.Process(os.getpid())

    def generate_large_test_data(self, num_records: int) -> pd.DataFrame:
        """大量テストデータの生成

        Args:
            num_records: 生成するレコード数

        Returns:
            生成されたDataFrame
        """
        data = {
            "id": [f"song_{i:06d}" for i in range(num_records)],
            "title": [f"Test Song {i}" for i in range(num_records)],
            "artist": [f"Test Artist {i % 100}" for i in range(num_records)],
            "difficulty": [i % 5 for i in range(num_records)],
            "notes_count": [100 + (i % 500) for i in range(num_records)],
            "duration_seconds": [180 + (i % 300) for i in range(num_records)],
            "bpm": [120 + (i % 80) for i in range(num_records)]
        }

        return pd.DataFrame(data)

    def measure_memory_usage(self, process) -> float:
        """メモリ使用量測定（MB単位）

        Args:
            process: psutilプロセスオブジェクト

        Returns:
            メモリ使用量（MB）
        """
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        return memory_mb

    def test_large_dataset_csv_parsing(self, components, process):
        """大量データCSV解析パフォーマンステスト"""
        logger.info("=" * 80)
        logger.info("Testing CSV parsing performance with large dataset")
        logger.info("=" * 80)

        # テストデータ生成（10,000レコード）
        test_data = self.generate_large_test_data(10000)
        csv_buffer = io.StringIO()
        test_data.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # メモリ使用量測定開始
        memory_before = self.measure_memory_usage(process)
        logger.info(f"Memory before parsing: {memory_before:.2f} MB")

        # CSV解析時間測定
        start_time = time.time()
        df = pd.read_csv(csv_buffer)
        elapsed_time = time.time() - start_time

        # メモリ使用量測定終了
        memory_after = self.measure_memory_usage(process)
        memory_increase = memory_after - memory_before

        logger.info(f"Parsing completed in {elapsed_time:.2f} seconds")
        logger.info(f"Memory after parsing: {memory_after:.2f} MB")
        logger.info(f"Memory increase: {memory_increase:.2f} MB")
        logger.info(f"Records parsed: {len(df)}")

        # アサーション
        assert len(df) == 10000
        assert elapsed_time < 10.0, f"CSV parsing took too long: {elapsed_time:.2f}s"
        assert memory_increase < 200, f"Memory increase too high: {memory_increase:.2f} MB"

    def test_large_dataset_validation(self, components, process):
        """大量データ検証パフォーマンステスト"""
        logger.info("=" * 80)
        logger.info("Testing data validation performance with large dataset")
        logger.info("=" * 80)

        validator = components["validator"]

        # テストデータ生成（10,000レコード）
        test_data = self.generate_large_test_data(10000)

        # メモリ使用量測定開始
        memory_before = self.measure_memory_usage(process)
        logger.info(f"Memory before validation: {memory_before:.2f} MB")

        # 検証時間測定
        start_time = time.time()
        validated_df, errors = validator.validate_songs_data(test_data)
        elapsed_time = time.time() - start_time

        # メモリ使用量測定終了
        memory_after = self.measure_memory_usage(process)
        memory_increase = memory_after - memory_before

        logger.info(f"Validation completed in {elapsed_time:.2f} seconds")
        logger.info(f"Memory after validation: {memory_after:.2f} MB")
        logger.info(f"Memory increase: {memory_increase:.2f} MB")
        logger.info(f"Valid records: {len(validated_df)}, Errors: {len(errors)}")

        # アサーション
        assert len(validated_df) > 0
        assert elapsed_time < 30.0, f"Validation took too long: {elapsed_time:.2f}s"
        assert memory_increase < 300, f"Memory increase too high: {memory_increase:.2f} MB"

    def test_large_dataset_transformation(self, components, process):
        """大量データ変換パフォーマンステスト"""
        logger.info("=" * 80)
        logger.info("Testing data transformation performance with large dataset")
        logger.info("=" * 80)

        transformer = components["transformer"]

        # テストデータ生成（10,000レコード）
        test_data = self.generate_large_test_data(10000)

        # メモリ使用量測定開始
        memory_before = self.measure_memory_usage(process)
        logger.info(f"Memory before transformation: {memory_before:.2f} MB")

        # 変換時間測定
        start_time = time.time()
        transformed_df = transformer.transform_for_database(test_data)
        elapsed_time = time.time() - start_time

        # メモリ使用量測定終了
        memory_after = self.measure_memory_usage(process)
        memory_increase = memory_after - memory_before

        logger.info(f"Transformation completed in {elapsed_time:.2f} seconds")
        logger.info(f"Memory after transformation: {memory_after:.2f} MB")
        logger.info(f"Memory increase: {memory_increase:.2f} MB")
        logger.info(f"Transformed records: {len(transformed_df)}")

        # アサーション
        assert len(transformed_df) == 10000
        assert elapsed_time < 10.0, f"Transformation took too long: {elapsed_time:.2f}s"
        assert memory_increase < 200, f"Memory increase too high: {memory_increase:.2f} MB"

    def test_large_dataset_batch_insert(self, components, process):
        """大量データバッチ挿入パフォーマンステスト"""
        logger.info("=" * 80)
        logger.info("Testing batch insert performance with large dataset")
        logger.info("=" * 80)

        db_client = components["db_client"]
        schema_manager = components["schema_manager"]

        # テストデータ生成（10,000レコード）
        test_data = self.generate_large_test_data(10000)

        # テストテーブル作成
        test_table = "performance_test_songs"
        schema_manager.ensure_table_exists(test_table, test_data)

        # メモリ使用量測定開始
        memory_before = self.measure_memory_usage(process)
        logger.info(f"Memory before batch insert: {memory_before:.2f} MB")

        # バッチ挿入用のINSERT文生成
        insert_statements = []
        for _, row in test_data.iterrows():
            values = ", ".join([f"'{str(v)}'" if isinstance(v, str) else str(v) for v in row])
            insert_statements.append(f"INSERT INTO {test_table} VALUES ({values})")

        # バッチ挿入時間測定
        start_time = time.time()
        result = db_client.execute_transaction(
            f"DELETE FROM {test_table}",
            insert_statements
        )
        elapsed_time = time.time() - start_time

        # メモリ使用量測定終了
        memory_after = self.measure_memory_usage(process)
        memory_increase = memory_after - memory_before

        logger.info(f"Batch insert completed in {elapsed_time:.2f} seconds")
        logger.info(f"Memory after batch insert: {memory_after:.2f} MB")
        logger.info(f"Memory increase: {memory_increase:.2f} MB")
        logger.info(f"Inserted records: {result['inserted']}")

        # アサーション
        assert result["inserted"] == 10000
        assert elapsed_time < self.MAX_PROCESSING_TIME_SECONDS, \
            f"Batch insert took too long: {elapsed_time:.2f}s (max: {self.MAX_PROCESSING_TIME_SECONDS}s)"
        assert memory_after < self.MAX_MEMORY_MB, \
            f"Memory usage too high: {memory_after:.2f} MB (max: {self.MAX_MEMORY_MB} MB)"

        # クリーンアップ
        db_client.client.execute(f"DROP TABLE {test_table}")
        logger.info(f"Test table {test_table} dropped")

    def test_full_sync_performance(self, components, process):
        """完全同期フローのパフォーマンステスト"""
        logger.info("=" * 80)
        logger.info("Testing full sync workflow performance")
        logger.info("=" * 80)

        orchestrator = components["orchestrator"]
        spreadsheet_id = components["spreadsheet_id"]

        # メモリ使用量測定開始
        memory_before = self.measure_memory_usage(process)
        logger.info(f"Memory before full sync: {memory_before:.2f} MB")

        # 完全同期時間測定（楽曲のみ、実データを使用）
        start_time = time.time()
        result = orchestrator.sync_single_table("songs", SONGS_GID, spreadsheet_id)
        elapsed_time = time.time() - start_time

        # メモリ使用量測定終了
        memory_after = self.measure_memory_usage(process)
        memory_increase = memory_after - memory_before

        logger.info(f"Full sync completed in {elapsed_time:.2f} seconds")
        logger.info(f"Memory after full sync: {memory_after:.2f} MB")
        logger.info(f"Memory increase: {memory_increase:.2f} MB")
        logger.info(f"Sync result: deleted={result.deleted_count}, inserted={result.inserted_count}")

        # アサーション（実データサイズに応じて調整）
        assert result.success is True
        assert elapsed_time < 300.0, f"Full sync took too long: {elapsed_time:.2f}s"
        assert memory_after < self.MAX_MEMORY_MB, \
            f"Memory usage too high: {memory_after:.2f} MB (max: {self.MAX_MEMORY_MB} MB)"

    def test_memory_leak_detection(self, components, process):
        """メモリリーク検出テスト"""
        logger.info("=" * 80)
        logger.info("Testing for memory leaks with repeated operations")
        logger.info("=" * 80)

        orchestrator = components["orchestrator"]
        spreadsheet_id = components["spreadsheet_id"]

        # 初期メモリ使用量
        memory_baseline = self.measure_memory_usage(process)
        logger.info(f"Baseline memory: {memory_baseline:.2f} MB")

        # 同期を10回繰り返し実行
        memory_readings = []
        for i in range(10):
            logger.info(f"Iteration {i + 1}/10")
            result = orchestrator.sync_single_table("songs", SONGS_GID, spreadsheet_id)
            assert result.success is True

            memory_current = self.measure_memory_usage(process)
            memory_readings.append(memory_current)
            logger.info(f"  Memory after iteration {i + 1}: {memory_current:.2f} MB")

        # 最終メモリ使用量
        memory_final = memory_readings[-1]
        memory_growth = memory_final - memory_baseline

        logger.info(f"Final memory: {memory_final:.2f} MB")
        logger.info(f"Total memory growth: {memory_growth:.2f} MB")

        # メモリ成長率の計算
        growth_rate = memory_growth / memory_baseline * 100

        logger.info(f"Memory growth rate: {growth_rate:.2f}%")

        # アサーション（メモリ成長率が50%以下であることを確認）
        assert growth_rate < 50.0, \
            f"Potential memory leak detected: {growth_rate:.2f}% growth over 10 iterations"

    def test_concurrent_operations_memory(self, components, process):
        """並行操作時のメモリ使用量テスト"""
        logger.info("=" * 80)
        logger.info("Testing memory usage with concurrent data processing")
        logger.info("=" * 80)

        validator = components["validator"]
        transformer = components["transformer"]

        # メモリ使用量測定開始
        memory_before = self.measure_memory_usage(process)
        logger.info(f"Memory before concurrent operations: {memory_before:.2f} MB")

        # 3つの大きなデータセットを同時に処理
        datasets = []
        for i in range(3):
            test_data = self.generate_large_test_data(5000)
            datasets.append(test_data)

        # 各データセットを検証・変換
        start_time = time.time()
        for i, data in enumerate(datasets):
            logger.info(f"Processing dataset {i + 1}/3")
            validated_df, errors = validator.validate_songs_data(data)
            transformed_df = transformer.transform_for_database(validated_df)

        elapsed_time = time.time() - start_time

        # メモリ使用量測定終了
        memory_after = self.measure_memory_usage(process)
        memory_peak = memory_after

        logger.info(f"Concurrent processing completed in {elapsed_time:.2f} seconds")
        logger.info(f"Peak memory usage: {memory_peak:.2f} MB")

        # アサーション
        assert memory_peak < self.MAX_MEMORY_MB, \
            f"Peak memory usage too high: {memory_peak:.2f} MB (max: {self.MAX_MEMORY_MB} MB)"
        assert elapsed_time < 120.0, f"Concurrent processing took too long: {elapsed_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
