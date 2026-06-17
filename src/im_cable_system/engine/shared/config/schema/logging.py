"""``logging`` セクションのスキーマと factory。

YAML キー: ``logging``
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
    parse_enum,
    parse_required_str,
)

_DEFAULT_LOG_LEVEL_NAME = "INFO"
_DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class LogLevel(str, Enum):
    """ログレベル（stdlib ``logging`` のレベル名に対応）。"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class LoggingConfig:
    """ログ設定。"""

    default_log_level: LogLevel
    default_log_format: str


class LoggingConfigFactory:
    """``logging`` ブロックを :class:`LoggingConfig` に変換する。"""

    @staticmethod
    def create(raw: Any) -> LoggingConfig:
        """YAML 由来の dict から :class:`LoggingConfig` を組み立てる。

        Args:
            raw: ``logging`` セクションの生 dict（``None`` 可）。

        Returns:
            LoggingConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または ``default_log_level`` が
                :class:`LogLevel` のメンバ外だった場合。
        """
        block = parse_dict(raw, key_path="logging")
        return LoggingConfig(
            default_log_level=parse_enum(
                block.get("default_log_level"),
                LogLevel,
                key_path="logging.default_log_level",
                default=LogLevel(_DEFAULT_LOG_LEVEL_NAME),
            ),
            default_log_format=parse_required_str(
                block.get("default_log_format"),
                key_path="logging.default_log_format",
                default=_DEFAULT_LOG_FORMAT,
            ),
        )
