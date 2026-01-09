"""CSVFetcherモジュール - Google Spreadsheet CSV取得"""

import pandas as pd
import requests
from io import StringIO
from typing import Optional
import time

from constants import CSV_EXPORT_URL_TEMPLATE
from logger import get_logger

logger = get_logger(__name__)


class CSVFetchError(Exception):
    """CSV取得エラー"""
    pass


class DataFrameParseError(Exception):
    """DataFrame解析エラー"""
    pass


class CSVFetcher:
    """Google SpreadsheetsのCSVエクスポートからデータを取得するクライアント"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Args:
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def fetch_csv_as_dataframe(
        self,
        spreadsheet_id: str,
        gid: int,
        timeout: int = 30,
        header: int = 0
    ) -> pd.DataFrame:
        """
        指定されたSpreadsheetシートをCSVエクスポートURLから取得してDataFrameに変換

        Args:
            spreadsheet_id: SpreadsheetのID
            gid: シートのgid
            timeout: HTTPリクエストタイムアウト（秒）
            header: ヘッダー行の位置（0-indexed）。デフォルトは0（1行目）

        Returns:
            pandas DataFrame

        Raises:
            CSVFetchError: CSV取得失敗時（HTTP エラー、タイムアウト等）
            DataFrameParseError: CSV解析失敗時
        """
        url = self._build_csv_url(spreadsheet_id, gid)

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Fetching CSV from Spreadsheet",
                    extra={
                        "context": {
                            "spreadsheet_id": spreadsheet_id,
                            "gid": gid,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries
                        }
                    }
                )

                response = requests.get(url, timeout=timeout)
                response.raise_for_status()

                # UTF-8エンコーディングを明示的に設定
                response.encoding = 'utf-8'

                # DataFrameに変換
                try:
                    df = pd.read_csv(StringIO(response.text), header=header)

                    logger.info(
                        f"Successfully fetched CSV",
                        extra={
                            "context": {
                                "spreadsheet_id": spreadsheet_id,
                                "gid": gid,
                                "record_count": len(df)
                            }
                        }
                    )
                    return df

                except Exception as e:
                    raise DataFrameParseError(f"Failed to parse CSV to DataFrame: {e}")

            except requests.HTTPError as e:
                logger.error(
                    f"HTTP error fetching CSV",
                    extra={
                        "context": {
                            "spreadsheet_id": spreadsheet_id,
                            "gid": gid,
                            "status_code": e.response.status_code if e.response else None,
                            "error": str(e)
                        }
                    }
                )
                raise CSVFetchError(f"HTTP error: {e}")

            except requests.Timeout as e:
                logger.warning(
                    f"Timeout fetching CSV (attempt {attempt + 1}/{self.max_retries})",
                    extra={
                        "context": {
                            "spreadsheet_id": spreadsheet_id,
                            "gid": gid,
                            "timeout": timeout
                        }
                    }
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise CSVFetchError(f"Timeout after {self.max_retries} attempts: {e}")

            except requests.RequestException as e:
                logger.error(
                    f"Request error fetching CSV",
                    extra={
                        "context": {
                            "spreadsheet_id": spreadsheet_id,
                            "gid": gid,
                            "error": str(e)
                        }
                    }
                )
                raise CSVFetchError(f"Request error: {e}")

    def _build_csv_url(self, spreadsheet_id: str, gid: int) -> str:
        """CSVエクスポートURLを構築"""
        return CSV_EXPORT_URL_TEMPLATE.format(
            spreadsheet_id=spreadsheet_id,
            gid=gid
        )
