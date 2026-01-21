"""DataTransformerモジュール - データ変換"""

import pandas as pd

from logger import get_logger

logger = get_logger(__name__)


class DataTransformer:
    """データ変換サービス"""

    def transform_for_database(self, df: pd.DataFrame, table_name: str = None) -> pd.DataFrame:
        """
        SpreadsheetのDataFrameをデータベース挿入用に変換

        Args:
            df: 元のDataFrame

        Returns:
            変換後のDataFrame
        """
        df_copy = df.copy()

        # Unnamed列（空のヘッダー）を削除
        unnamed_cols = [col for col in df_copy.columns if str(col).startswith('Unnamed:')]
        if unnamed_cols:
            logger.info(f"Dropping unnamed columns: {unnamed_cols}")
            df_copy = df_copy.drop(columns=unnamed_cols)

        # カラム名を正規化（文字エンコーディング問題を回避）
        df_copy.columns = [str(col).strip() for col in df_copy.columns]

        # 空文字列をNaNに変換
        df_copy = df_copy.replace('', pd.NA)

        # songsテーブルの場合、Shout/Beat/Melodyノーツ数カラムのnullを0に置き換え
        if table_name == 'songs':
            # カラム名が "カテゴリー_Shout×1白" のような形式になるため、contains + endsで判定
            notes_columns = [col for col in df_copy.columns if
                           ('Shout' in col or 'Beat' in col or 'Melody' in col)
                           and (col.endswith('白') or col.endswith('色'))]

            for col in notes_columns:
                if col in df_copy.columns:
                    df_copy[col] = df_copy[col].fillna(0)
                    logger.debug(f"Filled null values with 0 in column: {col}")

        # データ型の最適化
        for column in df_copy.columns:
            # 数値型の最適化
            if df_copy[column].dtype in ['int64', 'float64']:
                try:
                    if df_copy[column].dtype == 'float64':
                        # 整数に変換できる場合は変換
                        if df_copy[column].dropna().apply(lambda x: x.is_integer()).all():
                            df_copy[column] = df_copy[column].astype('Int64')
                except Exception:
                    pass

        logger.debug(f"Transformed DataFrame with {len(df_copy)} rows and columns: {list(df_copy.columns)}")

        return df_copy
