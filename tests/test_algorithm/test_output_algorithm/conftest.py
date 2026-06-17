"""output_algorithm テスト共通フィクスチャ。

設計方針:
    - 本テスト群はテスト用ベース設定
      ``tests/input_files/config/test_base_config.yaml`` を直接読む。
    - dump 関連はテストでは原則使わないため、``dump_base_dir`` は
      渡さない（``test_base_config.yaml`` 側にも書かない）。
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


def repo_root() -> Path:
    """リポジトリルート（``tests/`` の親）。"""
    return Path(__file__).resolve().parents[3]


def input_files_dir() -> Path:
    """テスト入力ファイル群のルート（``tests/input_files``）。"""
    return repo_root() / "tests" / "input_files"


def test_base_config_path() -> Path:
    """テスト用ベース設定 YAML のパス。"""
    return input_files_dir() / "config" / "test_base_config.yaml"


@pytest.fixture
def config() -> IConfig:
    """テスト用ベース設定から生成した :class:`IConfig`。"""
    return Config.create(config_file_path=test_base_config_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用 :class:`ILogger`（同 YAML から構築）。"""
    return Logger.create(config)


@pytest.fixture
def dump_config(tmp_path: Path) -> IConfig:
    """dump 先を ``tmp_path`` にしたテスト用 :class:`IConfig`。"""
    return Config.create(
        config_file_path=test_base_config_path(),
        dump_base_dir=tmp_path,
    )
