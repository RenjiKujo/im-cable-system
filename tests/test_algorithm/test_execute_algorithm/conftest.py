"""Execute アルゴリズム層の共通 fixture。

単カゴ / 二重かごの InputDtos 生成は ``fixtures`` パッケージに集約する。
processor 層からの import は行わない（テストポリシー）。

config / logger:
    正規 ``config.yaml`` をそのまま読む plain な ``config`` / ``logger`` を提供する。
    ``build_model`` / ``simulate`` 配下はこれを共有する。別設定が必要な
    ``orchestrate`` / ``validate_itm_dto`` は各サブツリーの conftest で上書きする。
"""

from __future__ import annotations

from pathlib import Path

import pytest

import im_cable_system.engine.shared.config.app_config as app_config_module
from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableSeriesDtos,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_double_cage_im_series_dtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos as make_double_cage_input_im_cable_system_dtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_cable_series_dtos,
    make_single_cage_im_series_dtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos as make_single_cage_input_im_cable_system_dtos,
)


def _default_config_file_path() -> Path:
    """正規 ``config.yaml`` のパスを返す。"""
    return Path(app_config_module.__file__).resolve().parent / "config.yaml"


@pytest.fixture
def config() -> IConfig:
    """正規 ``config.yaml`` から生成した plain な Config フィクスチャ。"""
    return Config.create(config_file_path=_default_config_file_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用の Logger フィクスチャ。"""
    return Logger.create(config)


@pytest.fixture
def single_cage_im_series_dtos() -> list[ImSeriesDto]:
    """単カゴ向け ImSeriesDto リスト fixture。"""
    return make_single_cage_im_series_dtos()


@pytest.fixture
def cable_series_dtos() -> CableSeriesDtos:
    """テスト用の CableSeriesDtos fixture。"""
    return make_cable_series_dtos()


@pytest.fixture
def single_cage_input_im_cable_system_dtos() -> InputDtos:
    """単カゴ向け InputDtos fixture。"""
    return make_single_cage_input_im_cable_system_dtos()


@pytest.fixture
def single_cage_input_im_cable_system_dto(
    single_cage_input_im_cable_system_dtos: InputDtos,
) -> InputDto:
    """単カゴ向けの単一 InputDto fixture。"""
    return single_cage_input_im_cable_system_dtos.get_all()[0]


@pytest.fixture
def double_cage_im_series_dtos() -> list[ImSeriesDto]:
    """二重かご向け ImSeriesDto リスト fixture。"""
    return make_double_cage_im_series_dtos()


@pytest.fixture
def double_cage_input_im_cable_system_dtos() -> InputDtos:
    """二重かご向け InputDtos fixture。"""
    return make_double_cage_input_im_cable_system_dtos()


@pytest.fixture
def double_cage_input_im_cable_system_dto(
    double_cage_input_im_cable_system_dtos: InputDtos,
) -> InputDto:
    """二重かご向けの単一 InputDto fixture。"""
    return double_cage_input_im_cable_system_dtos.get_all()[0]
