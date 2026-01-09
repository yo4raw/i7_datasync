"""ロガー設定モジュール"""

import os
import logging
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON形式でログを出力するFormatter"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # コンテキスト情報があれば追加
        if hasattr(record, "context"):
            log_data["context"] = record.context

        return json.dumps(log_data, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得

    Args:
        name: ロガー名（通常は__name__を使用）

    Returns:
        設定済みロガー
    """
    logger = logging.getLogger(name)

    # 既にハンドラーが設定されている場合はそのまま返す
    if logger.handlers:
        return logger

    # ログレベルを環境変数から取得（デフォルト: INFO）
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # コンソールハンドラー設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # 親ロガーへの伝播を無効化（重複ログ防止）
    logger.propagate = False

    return logger
