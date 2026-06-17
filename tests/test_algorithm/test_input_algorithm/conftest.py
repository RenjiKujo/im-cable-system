"""input_algorithm テスト共通フィクスチャ。

設計方針:
    - 本テスト群はテスト用ベース設定
      ``tests/input_files/config/test_base_config.yaml`` を直接読む。
      カタログ・境界 YAML のパスは、当該 ``test_base_config.yaml`` の
      親ディレクトリ基準で ``tests/input_files/{catalog,bounds_and_init}/``
      に解決される（同梱 ``src/.../catalog`` には依存しない）。
    - dump 関連はテストでは原則使わないため、``dump_base_dir`` は
      渡さない（``test_base_config.yaml`` 側にも書かない）。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    test_base_config_path,
)


@pytest.fixture
def config() -> IConfig:
    """テスト用ベース設定から生成した :class:`IConfig`。

    カタログ・境界 YAML のパスは ``test_base_config.yaml`` 内で
    ``tests/input_files/{catalog,bounds_and_init}/`` を指している。
    """
    return Config.create(config_file_path=test_base_config_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用 :class:`ILogger`（同 YAML から構築）。"""
    return Logger.create(config)
