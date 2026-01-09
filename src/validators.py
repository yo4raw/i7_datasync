"""DataValidatorモジュール - データ検証"""

from typing import List, Tuple
import pandas as pd

from logger import get_logger

logger = get_logger(__name__)


class DataValidator:
    """データ検証サービス"""

    VALID_RARITIES = ['UR', 'SSR', 'SR', 'R', 'N']

    def validate_songs_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        楽曲データを検証

        Args:
            df: 楽曲DataFrame

        Returns:
            (有効なDataFrame, エラーメッセージリスト)
        """
        errors = []
        valid_indices = []

        for idx, row in df.iterrows():
            row_errors = []

            # IDフィールドチェック
            if pd.isna(row.get('ID')):
                row_errors.append(f"Row {idx}: Missing ID")

            # 数値フィールドチェック（存在する場合のみ）
            numeric_fields = ['ノーツ数', '秒数']
            for field in numeric_fields:
                if field in row and not pd.isna(row[field]):
                    try:
                        float(row[field])
                    except (ValueError, TypeError):
                        row_errors.append(f"Row {idx}: Invalid numeric value in {field}")

            if row_errors:
                errors.extend(row_errors)
                logger.warning(f"Validation error in songs data: {row_errors}")
            else:
                valid_indices.append(idx)

        return df.loc[valid_indices], errors

    def validate_cards_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        カードデータを検証

        Args:
            df: カードDataFrame

        Returns:
            (有効なDataFrame, エラーメッセージリスト)
        """
        errors = []
        valid_indices = []

        for idx, row in df.iterrows():
            row_errors = []

            # ID・cardIDフィールドチェック
            if pd.isna(row.get('ID')):
                row_errors.append(f"Row {idx}: Missing ID")
            if pd.isna(row.get('cardID')):
                row_errors.append(f"Row {idx}: Missing cardID")

            # rarityチェック
            if 'rarity' in row and not pd.isna(row['rarity']):
                if row['rarity'] not in self.VALID_RARITIES:
                    row_errors.append(f"Row {idx}: Invalid rarity {row['rarity']}")

            if row_errors:
                errors.extend(row_errors)
                logger.warning(f"Validation error in cards data: {row_errors}")
            else:
                valid_indices.append(idx)

        return df.loc[valid_indices], errors

    def validate_brooches_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        固有ブローチデータを検証

        Args:
            df: 固有ブローチDataFrame

        Returns:
            (有効なDataFrame, エラーメッセージリスト)
        """
        errors = []
        valid_indices = []

        for idx, row in df.iterrows():
            row_errors = []

            # ID・cardIDフィールドチェック
            if pd.isna(row.get('ID')):
                row_errors.append(f"Row {idx}: Missing ID")
            if pd.isna(row.get('cardID')):
                row_errors.append(f"Row {idx}: Missing cardID")

            # スコア関連フィールドの非負チェック
            score_fields = ['オート', '楽曲', 'スコア', '上限']
            for field in score_fields:
                if field in row and not pd.isna(row[field]):
                    try:
                        value = float(row[field])
                        if value < 0:
                            row_errors.append(f"Row {idx}: Negative value in {field}")
                    except (ValueError, TypeError):
                        row_errors.append(f"Row {idx}: Invalid numeric value in {field}")

            if row_errors:
                errors.extend(row_errors)
                logger.warning(f"Validation error in brooches data: {row_errors}")
            else:
                valid_indices.append(idx)

        return df.loc[valid_indices], errors
