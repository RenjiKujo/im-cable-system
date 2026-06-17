"""Application logger implementation (``app_`` = runtime log output facade).

モジュール名の ``app_`` は、実行時アプリケーションのログ出力窓口であることを示し、
汎用語 ``logger`` や stdlib ``logging`` との混同を避けるため付与している。
内部では stdlib ``logging.Logger`` を ``stdlib_logger`` として保持する。

設計方針:
    YAML 解釈ルートを :class:`Config` に一本化するため、本実装は
    :class:`IConfig` 経由でログ設定を受け取る。``Config.create`` 時点で
    ``logging`` セクションはスキーマ検証済みなので、Logger 側では
    :class:`LogLevel` Enum と書式文字列を attribute アクセスで取り出すだけ。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar

from im_cable_system.engine.shared.config.i_app_config import IConfig
from im_cable_system.engine.shared.config.i_app_logger import ILogger
from im_cable_system.engine.shared.config.schema.logging import LogLevel


class Logger(ILogger):
    """``ILogger`` の具体実装。

    ``Logger.create(config)`` で取得する。同一の ``config.config_file_path``
    に対する ``create`` は同一インスタンスを返し、stdlib Handler の
    二重登録を防ぐ。

    使い方（Runner / conftest）::

        config = Config.create(config_file_path=config_path)
        logger = Logger.create(config)
        pipeline = SomePipeline.create(config=config, logger=logger)
    """

    _instances_by_path: ClassVar[dict[Path, ILogger]] = {}

    def __init__(self, config: IConfig) -> None:
        """構成済み Config に基づき内部ロガーを構成する。

        Args:
            config: 構成済みの :class:`IConfig`。
                ``logging`` / ``project_info`` セクションは ``Config.create``
                 時点でスキーマ検証済み。
        """
        self._config_file_path: Path = config.config_file_path
        self._stdlib_logger: logging.Logger = self._configure_stdlib_logger(
            project_name=config.project_info.project_name,
            log_level=config.logging_config.default_log_level,
            log_format=config.logging_config.default_log_format,
        )

    @classmethod
    def create(cls, config: IConfig) -> ILogger:
        """ログ出力インスタンスを取得するファクトリーメソッド。

        Args:
            config: 構成済みの :class:`IConfig`。

        Returns:
            ILogger: 構成済みログ出力インスタンス。同一の
                ``config.config_file_path`` に対する呼び出しは同一インスタンス
                を返す（stdlib Handler の二重登録を防止）。
        """
        cache_key = config.config_file_path
        cached = cls._instances_by_path.get(cache_key)
        if cached is not None:
            return cached
        instance = cls(config=config)
        cls._instances_by_path[cache_key] = instance
        return instance

    @property
    def config_file_path(self) -> Path:
        """構成時に用いた設定ファイルのパスを返す。"""
        return self._config_file_path

    def info(self, msg: str, *args: object) -> None:
        """INFO レベルでログを出力する。"""
        self._stdlib_logger.info(msg, *args)

    def warning(self, msg: str, *args: object) -> None:
        """WARNING レベルでログを出力する。"""
        self._stdlib_logger.warning(msg, *args)

    def error(self, msg: str, *args: object) -> None:
        """ERROR レベルでログを出力する。"""
        self._stdlib_logger.error(msg, *args)

    def exception(self, msg: str, *args: object) -> None:
        """ERROR レベルでスタックトレース付きログを出力する。

        ``except`` 句の中から呼ぶことを想定する。
        """
        self._stdlib_logger.exception(msg, *args)

    @staticmethod
    def _configure_stdlib_logger(
        *,
        project_name: str,
        log_level: LogLevel,
        log_format: str,
    ) -> logging.Logger:
        """検証済みパラメータから stdlib ``logging.Logger`` を一度だけ構成する。"""
        stdlib_logger = logging.getLogger(project_name)
        stdlib_logger.setLevel(getattr(logging, log_level.value))

        if not stdlib_logger.handlers:
            formatter = logging.Formatter(log_format)
            handler = logging.StreamHandler()
            handler.setLevel(stdlib_logger.level)
            handler.setFormatter(formatter)
            stdlib_logger.addHandler(handler)

        stdlib_logger.propagate = False
        return stdlib_logger
