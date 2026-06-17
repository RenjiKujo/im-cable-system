"""input_stage テスト共通フィクスチャ。

algorithm 層と同じテスト用ベース設定
（``tests/input_files/config/test_base_config.yaml``）を流用し、
カタログ・境界 YAML のパスを ``tests/input_files/`` 配下に統一する。

InputStage の責務は薄いため、本テスト群は IStage 契約の疎通と
モード固有差分（``reference_axes``）のみを検証する。詳細な
ロード・組み立て・検証ロジックは
``tests/test_algorithm/test_input_algorithm/`` に委ねる。
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


def _repo_root() -> Path:
    """リポジトリルート（``tests/`` の親）。"""
    return Path(__file__).resolve().parents[3]


def _input_files_dir() -> Path:
    """テスト入力ファイル群のルート（``tests/input_files``）。"""
    return _repo_root() / "tests" / "input_files"


def _test_base_config_path() -> Path:
    """テスト用ベース設定 YAML のパス。"""
    return _input_files_dir() / "config" / "test_base_config.yaml"


@pytest.fixture
def config() -> IConfig:
    """テスト用ベース設定から生成した :class:`IConfig`。"""
    return Config.create(config_file_path=_test_base_config_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用ベース設定から生成した :class:`ILogger`。"""
    return Logger.create(config)


@pytest.fixture
def input_files_dir() -> Path:
    """テスト入力ファイル群のルート（``tests/input_files``）。"""
    return _input_files_dir()
