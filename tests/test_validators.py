"""DataValidatorのユニットテスト"""

import pytest
import pandas as pd

import sys
sys.path.insert(0, '/Users/yaoko/git/i7_datasync/src')

from validators import DataValidator


class TestDataValidator:
    """DataValidatorクラスのテスト"""

    def test_validate_songs_data_valid(self):
        """楽曲データ検証 - 正常系"""
        validator = DataValidator()
        df = pd.DataFrame({
            'ID': [1, 2, 3],
            'name': ['Song1', 'Song2', 'Song3'],
            'notes_count': [100, 200, 300]
        })

        valid_df, errors = validator.validate_songs_data(df)

        assert len(valid_df) == 3
        assert len(errors) == 0

    def test_validate_songs_data_missing_id(self):
        """楽曲データ検証 - ID欠損"""
        validator = DataValidator()
        df = pd.DataFrame({
            'ID': [1, None, 3],
            'name': ['Song1', 'Song2', 'Song3']
        })

        valid_df, errors = validator.validate_songs_data(df)

        assert len(valid_df) == 2
        assert len(errors) == 1

    def test_validate_cards_data_valid(self):
        """カードデータ検証 - 正常系"""
        validator = DataValidator()
        df = pd.DataFrame({
            'ID': [1, 2],
            'cardID': ['C001', 'C002'],
            'rarity': ['UR', 'SSR']
        })

        valid_df, errors = validator.validate_cards_data(df)

        assert len(valid_df) == 2
        assert len(errors) == 0

    def test_validate_cards_data_invalid_rarity(self):
        """カードデータ検証 - rarity不正"""
        validator = DataValidator()
        df = pd.DataFrame({
            'ID': [1, 2],
            'cardID': ['C001', 'C002'],
            'rarity': ['UR', 'INVALID']
        })

        valid_df, errors = validator.validate_cards_data(df)

        assert len(valid_df) == 1
        assert len(errors) == 1

    def test_validate_brooches_data_valid(self):
        """ブローチデータ検証 - 正常系"""
        validator = DataValidator()
        df = pd.DataFrame({
            'ID': [1, 2],
            'cardID': ['C001', 'C002'],
            'score': [100, 200]
        })

        valid_df, errors = validator.validate_brooches_data(df)

        assert len(valid_df) == 2
        assert len(errors) == 0
