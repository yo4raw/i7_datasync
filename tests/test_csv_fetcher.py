"""CSVFetcherのユニットテスト"""

import pytest
import pandas as pd
from unittest.mock import patch, Mock
from io import StringIO
import requests

import sys
sys.path.insert(0, '/Users/yaoko/git/i7_datasync/src')

from csv_fetcher import CSVFetcher, CSVFetchError


class TestCSVFetcher:
    """CSVFetcherクラスのテスト"""

    def test_fetch_csv_as_dataframe_success(self):
        """正常系: CSVデータを正しくDataFrameに変換"""
        fetcher = CSVFetcher()

        # モックCSVデータ
        mock_csv = "ID,name,value\n1,Test,100\n2,Sample,200"

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_csv
            mock_get.return_value = mock_response

            df = fetcher.fetch_csv_as_dataframe("test_spreadsheet_id", 123456)

            assert len(df) == 2
            assert list(df.columns) == ['ID', 'name', 'value']
            assert df['ID'].tolist() == [1, 2]

    def test_fetch_csv_as_dataframe_http_404(self):
        """HTTP 404エラー時に例外発生"""
        fetcher = CSVFetcher()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response

            with pytest.raises(CSVFetchError):
                fetcher.fetch_csv_as_dataframe("test_spreadsheet_id", 123456)

    def test_fetch_csv_as_dataframe_http_500(self):
        """HTTP 500エラー時に例外発生"""
        fetcher = CSVFetcher()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
            mock_get.return_value = mock_response

            with pytest.raises(CSVFetchError):
                fetcher.fetch_csv_as_dataframe("test_spreadsheet_id", 123456)

    def test_fetch_csv_as_dataframe_timeout(self):
        """タイムアウト時に例外発生"""
        fetcher = CSVFetcher()

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Request timeout")

            with pytest.raises(CSVFetchError):
                fetcher.fetch_csv_as_dataframe("test_spreadsheet_id", 123456, timeout=1)

    def test_fetch_csv_as_dataframe_retry_logic(self):
        """リトライロジックのテスト（3回失敗後に例外）"""
        fetcher = CSVFetcher()

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Request timeout")

            with pytest.raises(CSVFetchError):
                fetcher.fetch_csv_as_dataframe("test_spreadsheet_id", 123456)

            # 最大3回リトライされることを確認
            assert mock_get.call_count == 3

    def test_build_csv_url(self):
        """CSV URLが正しく構築される"""
        fetcher = CSVFetcher()
        url = fetcher._build_csv_url("abc123", 456789)
        expected = "https://docs.google.com/spreadsheets/d/abc123/export?format=csv&gid=456789"
        assert url == expected
