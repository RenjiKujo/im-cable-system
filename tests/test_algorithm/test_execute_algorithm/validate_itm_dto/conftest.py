"""``validate_itm_dto`` テスト共通フィクスチャ。

下位ディレクトリ（``orchestrate`` / ``validate_energy_conservation`` /
``validate_current_voltage_range``）のテストから共有する config / logger /
正解 ItmDto を提供する。

config はテスト用ベース設定
``tests/input_files/config/test_base_config.yaml`` を直接読む。
NOTE: ベース設定では ``current_voltage_range.severity`` を ``INFO`` に
下げているため、電流電圧レンジ逸脱で raise を確認したいテストは
``override_validation_config(config, cv={"severity": Severity.ERROR})``
で明示的に上書きすること。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from im_cable_system.engine.shared.dto.itm import ItmDto
from tests.test_algorithm.test_execute_algorithm.validate_itm_dto.itm_dto_builders import (  # noqa: E501
    build_valid_itm_dto,
)


def _test_base_config_file_path() -> Path:
    """テスト用ベース設定 YAML のパスを取得する。"""
    repo_root = Path(__file__).resolve().parents[4]
    return (
        repo_root / "tests" / "input_files" / "config" / "test_base_config.yaml"
    )


@pytest.fixture
def config() -> IConfig:
    """テスト用ベース設定から生成した Config フィクスチャ。"""
    return Config.create(config_file_path=_test_base_config_file_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用の Logger フィクスチャ。"""
    return Logger.create(config)


@pytest.fixture
def valid_itm_dto() -> ItmDto:
    """検証を通過する正解 ItmDto（手組み・シミュレーション不実行）。"""
    return build_valid_itm_dto()
