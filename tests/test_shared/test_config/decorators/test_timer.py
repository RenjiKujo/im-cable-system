"""Tests for :func:`timer` decorator.

ロガー解決（明示・``self._logger`` 経由・欠落時例外）、``min_duration`` による
ログ抑制、例外時の INFO ログ（``[abort]``）と再 raise、``line`` 区切り
プレフィックスを担保する。

例外時は ``logger.error`` を呼ばず、メソッド名と経過時間のみを INFO
（``[abort]`` マーカー付き）で出す。エラーログとスタックトレースは最上位
境界（Runner 等）で ``logger.exception`` として 1 度だけ出す方針。
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from im_cable_system.engine.shared.config import Config, Logger, timer

_REPO_ROOT = Path(__file__).resolve().parents[4]
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


class _TimedService:
    """timer 用の最小サービス（``self._logger`` 経由解決の検証）。"""

    def __init__(self, logger: object) -> None:
        self._logger = logger

    @timer(logger=None, line="#", min_duration=0.0)
    def run(self) -> str:
        return "ok"


class TestTimerLoggerResolution:
    """ロガー解決経路の契約。"""

    @pytest.fixture(autouse=True)
    def _clear_instance_cache(self) -> Generator[None, None, None]:
        Logger._instances_by_path.clear()
        yield
        Logger._instances_by_path.clear()

    def test_uses_self_logger(self) -> None:
        config = Config.create(config_file_path=_bundled_config_yaml_path())
        logger = Logger.create(config)
        service = _TimedService(logger=logger)
        assert service.run() == "ok"

    def test_explicit_logger_argument(self) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line="#", min_duration=0.0)
        def sample() -> int:
            return 1

        assert sample() == 1
        # min_duration=0.0 では start / end の両方を出力する。
        assert mock_logger.info.call_count >= 2

    def test_raises_when_logger_missing(self) -> None:
        class NoLogger:
            @timer(logger=None, line="#")
            def run(self) -> None:
                pass

        with pytest.raises(ValueError, match="_logger"):
            NoLogger().run()


class TestTimerLoggingBehavior:
    """min_duration / line / 例外時挙動の契約。"""

    def test_min_duration_suppresses_logs_for_fast_call(self) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line=None, min_duration=10.0)
        def fast() -> int:
            return 0

        assert fast() == 0
        # 10 秒未満の処理は ``info`` ログを出力しない契約。
        assert mock_logger.info.call_count == 0
        assert mock_logger.error.call_count == 0

    def test_min_duration_zero_emits_start_and_end(self) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line=None, min_duration=0.0)
        def quick() -> int:
            return 1

        quick()
        info_messages = [
            call.args[0] for call in mock_logger.info.call_args_list
        ]
        assert any("[start]" in msg for msg in info_messages)
        assert any("[end]" in msg for msg in info_messages)

    def test_line_prefix_is_repeated_character(self) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line="=", min_duration=0.0)
        def with_line() -> None:
            pass

        with_line()
        info_messages = [
            call.args[0] for call in mock_logger.info.call_args_list
        ]
        # ``=`` を 30 回繰り返した区切り文字列がプレフィックスとして付く。
        assert any("=" * 30 in msg for msg in info_messages)

    def test_exception_is_logged_as_abort_and_re_raised(self) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line=None, min_duration=0.0)
        def boom() -> None:
            raise RuntimeError("boom-msg")

        with pytest.raises(RuntimeError, match="boom-msg"):
            boom()
        info_messages = [
            call.args[0] for call in mock_logger.info.call_args_list
        ]
        # 例外時は ``info`` で [abort] を出すこと（min_duration 影響を受けない）。
        # ERROR ログは出さず、最上位境界で logger.exception に集約する方針。
        assert any("[abort]" in msg for msg in info_messages)
        assert mock_logger.error.call_count == 0

    def test_exception_emits_start_log_even_when_below_min_duration(
        self,
    ) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line=None, min_duration=10.0)
        def fast_failure() -> None:
            raise ValueError("fail-msg")

        with pytest.raises(ValueError, match="fail-msg"):
            fast_failure()
        info_messages = [
            call.args[0] for call in mock_logger.info.call_args_list
        ]
        # min_duration>0 でも例外時は start / abort ログが出力される契約。
        assert any("[start]" in msg for msg in info_messages)
        assert any("[abort]" in msg for msg in info_messages)
        assert mock_logger.error.call_count == 0

    def test_exception_message_is_not_included_in_log(self) -> None:
        mock_logger = MagicMock()

        @timer(logger=mock_logger, line=None, min_duration=0.0)
        def boom() -> None:
            raise RuntimeError("secret-detail-do-not-log")

        with pytest.raises(RuntimeError):
            boom()
        info_messages = [
            call.args[0] for call in mock_logger.info.call_args_list
        ]
        # 例外メッセージ自体は @timer では出さない（重複・情報重複防止）。
        # 例外の中身は最上位境界の logger.exception でスタックトレースとして残す。
        assert all(
            "secret-detail-do-not-log" not in msg for msg in info_messages
        )
