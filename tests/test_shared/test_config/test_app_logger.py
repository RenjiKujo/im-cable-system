"""Tests for :class:`Logger` (application logger facade).

``Logger`` は :class:`IConfig` を受け取って構成する（YAML 解釈ルートを
``Config`` に一本化）。本テストでは、ファクトリのキャッシュ・Handler 二重
登録防止・stdlib logger の構成（レベル・propagate）・``info`` /
``warning`` / ``error`` / ``exception`` の伝搬を担保する。

不正な ``logging.default_log_level`` は ``Config.create`` 時点で
``ValueError`` として弾かれる（fail-fast）ことも合わせて検証する。
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

import pytest

from im_cable_system.engine.shared.config import Config, ILogger, Logger

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BUNDLED_CONFIG_YAML = (
    _REPO_ROOT
    / "src"
    / "im_cable_system"
    / "engine"
    / "shared"
    / "config"
    / "config.yaml"
)


def _bundled_config_yaml_path() -> Path:
    return _BUNDLED_CONFIG_YAML


def _bundled_config() -> Config:
    return Config.create(config_file_path=_bundled_config_yaml_path())  # type: ignore[return-value]


def _write_yaml(path: Path, project_name: str, level: str) -> Path:
    path.write_text(
        "project_info:\n"
        f"  project_name: {project_name}\n"
        "logging:\n"
        f"  default_log_level: {level}\n",
        encoding="utf-8",
    )
    return path


class TestLoggerFactoryCache:
    """Logger.create の契約（キャッシュと型）。"""

    @pytest.fixture(autouse=True)
    def _clear_instance_cache(self) -> Generator[None, None, None]:
        Logger._instances_by_path.clear()
        yield
        Logger._instances_by_path.clear()

    def test_create_returns_ilogger(self) -> None:
        logger = Logger.create(_bundled_config())
        assert isinstance(logger, ILogger)

    def test_create_same_path_returns_same_instance(self) -> None:
        first = Logger.create(_bundled_config())
        # 別 Config インスタンスでも config_file_path が同一ならキャッシュヒット。
        second = Logger.create(_bundled_config())
        assert first is second

    def test_config_file_path_property(self) -> None:
        config = _bundled_config()
        logger = Logger.create(config)
        assert logger.config_file_path == config.config_file_path


class TestLoggerStdlibConfiguration:
    """生成された stdlib ``logging.Logger`` の構成。"""

    @pytest.fixture(autouse=True)
    def _clear_instance_cache(self) -> Generator[None, None, None]:
        Logger._instances_by_path.clear()
        yield
        Logger._instances_by_path.clear()

    def test_create_does_not_duplicate_handlers(self) -> None:
        Logger.create(_bundled_config())
        Logger.create(_bundled_config())

        stdlib_logger = logging.getLogger("im_cable_system")
        # pytest はログ捕捉用に ``LogCaptureHandler``(StreamHandler の
        # サブクラス) を同じ logger に足すため、全 handler 数では環境依存に
        # なる。アプリが追加した素の ``StreamHandler`` だけを厳密一致で数える。
        app_handlers = [
            handler
            for handler in stdlib_logger.handlers
            if type(handler) is logging.StreamHandler
        ]
        assert len(app_handlers) == 1

    def test_log_level_reflects_yaml(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path / "debug.yaml", "test_proj_debug", "DEBUG")
        Logger.create(Config.create(config_file_path=path))
        stdlib_logger = logging.getLogger("test_proj_debug")
        assert stdlib_logger.level == logging.DEBUG
        assert stdlib_logger.handlers
        assert stdlib_logger.handlers[0].level == logging.DEBUG

    def test_unknown_level_raises_value_error_at_config(
        self, tmp_path: Path
    ) -> None:
        """不正なログレベルは Config.create でスキーマ検証エラー（fail-fast）。"""
        path = _write_yaml(
            tmp_path / "unknown.yaml", "test_proj_unknown", "NOT_A_LEVEL"
        )
        with pytest.raises(ValueError, match="logging.default_log_level"):
            Config.create(config_file_path=path)

    def test_propagate_is_disabled(self, tmp_path: Path) -> None:
        path = _write_yaml(tmp_path / "p.yaml", "test_proj_propagate", "INFO")
        Logger.create(Config.create(config_file_path=path))
        stdlib_logger = logging.getLogger("test_proj_propagate")
        assert stdlib_logger.propagate is False


class TestLoggerEmission:
    """info / warning / error / exception の伝搬。"""

    @pytest.fixture(autouse=True)
    def _clear_instance_cache(self) -> Generator[None, None, None]:
        Logger._instances_by_path.clear()
        yield
        Logger._instances_by_path.clear()

    def test_emits_records_at_each_level(self, tmp_path: Path) -> None:
        # ``Logger`` は propagate=False のためルート経由の caplog では捕捉できない。
        # stdlib logger に直接 list handler を付け、各レベルが伝搬することを検証する。
        path = _write_yaml(tmp_path / "emit.yaml", "test_proj_emit", "DEBUG")
        logger = Logger.create(Config.create(config_file_path=path))
        stdlib_logger = logging.getLogger("test_proj_emit")
        records: list[logging.LogRecord] = []

        class _CaptureHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        handler = _CaptureHandler(level=logging.DEBUG)
        stdlib_logger.addHandler(handler)
        try:
            logger.info("info-msg")
            logger.warning("warn-msg")
            logger.error("error-msg")
        finally:
            stdlib_logger.removeHandler(handler)

        messages = [record.getMessage() for record in records]
        levels = [record.levelno for record in records]
        assert messages == ["info-msg", "warn-msg", "error-msg"]
        assert levels == [logging.INFO, logging.WARNING, logging.ERROR]

    def test_exception_records_traceback(self, tmp_path: Path) -> None:
        # logger.exception は except 句内で呼び、現在の例外スタックトレースを
        # ERROR レベルで残す契約。
        path = _write_yaml(
            tmp_path / "exc.yaml", "test_proj_exception", "DEBUG"
        )
        logger = Logger.create(Config.create(config_file_path=path))
        stdlib_logger = logging.getLogger("test_proj_exception")
        records: list[logging.LogRecord] = []

        class _CaptureHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        handler = _CaptureHandler(level=logging.DEBUG)
        stdlib_logger.addHandler(handler)
        try:
            try:
                raise RuntimeError("boom-detail")
            except RuntimeError:
                logger.exception("unexpected error: %s", "ctx-info")
        finally:
            stdlib_logger.removeHandler(handler)

        assert len(records) == 1
        record = records[0]
        assert record.levelno == logging.ERROR
        assert record.getMessage() == "unexpected error: ctx-info"
        assert record.exc_info is not None
        assert record.exc_info[0] is RuntimeError
