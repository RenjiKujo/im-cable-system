"""パラメータ推定オーケストレーターテスト用の共通 fixture。

単一かご・二重かごの軽量テスト DTO を用いてテストする。
config と logger は im_cable_system.engine.shared.config の正規実装をベースとし、
必要に応じて conftest 内で書き換えロジックを記載する。

``_get_overridden_config_path`` では
``estimate_params.optimizer.least_squares.max_nfev`` を 5 に固定し、
実行時間を制限する。
"""

import copy
import tempfile
from pathlib import Path

import pytest
import yaml

import im_cable_system.engine.shared.config.app_config as app_config_module
from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
    load_config,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos as make_input_im_cable_system_dtos_double_cage,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos as make_input_im_cable_system_dtos_single_cage,
)


def _get_config_file_path() -> Path:
    """設定ファイルのパスを取得する。

    im_cable_system.engine.shared.config の正規 config.yaml を使用する。
    """
    return Path(app_config_module.__file__).resolve().parent / "config.yaml"


def _get_overridden_config_path() -> Path:
    """テスト用に書き換えた設定ファイルのパスを取得する。

    正規の config.yaml をベースに、電圧レンジ検証を INFO にし、
    execute が完了するように conftest 内で書き換えた設定を一時ファイルに書き出す。
    """
    base_path = _get_config_file_path()
    config_data = copy.deepcopy(load_config(base_path))

    # NOTE:
    # テストでは config.yaml を一時ファイル（/tmp 配下）へ書き出すため、
    # config.yaml からの相対パス指定（catalog / bounds YAML）が
    # /tmp 基準で解決されないよう、ここで絶対パスへ正規化しておく。
    base_dir = base_path.resolve().parent
    series_catalog = config_data.setdefault(
        "series_catalog_for_forward_simulation",
        {},
    )
    for key in ("im_file_path", "cable_file_path"):
        rel_path = series_catalog.get(key)
        if isinstance(rel_path, str):
            series_catalog[key] = str((base_dir / rel_path).resolve())
    bounds = config_data.setdefault(
        "bounds_and_init_for_estimation_parameters",
        {},
    )
    for key in ("im_file_path", "cable_file_path"):
        rel_path = bounds.get(key)
        if isinstance(rel_path, str):
            bounds[key] = str((base_dir / rel_path).resolve())

    calculation = config_data.setdefault("calculation", {})
    execute = calculation.setdefault("execute", {})
    validation = execute.setdefault("validation", {})
    cvr = validation.setdefault("current_voltage_range", {})
    cvr["severity"] = "INFO"
    # 単体テストの実行時間を抑える（本番 config の 100 回は CI で重い）
    estimate_params = execute.setdefault("estimate_params", {})
    opt = estimate_params.setdefault("optimizer", {})
    if isinstance(opt, dict):
        least_squares = opt.setdefault("least_squares", {})
        if isinstance(least_squares, dict):
            least_squares["max_nfev"] = 5

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        path = Path(f.name)
    path.write_text(
        yaml.dump(config_data, allow_unicode=True), encoding="utf-8"
    )
    return path


@pytest.fixture
def config() -> IConfig:
    """テスト用の Config fixture。

    im_cable_system.engine.shared.config の Config をベースとする。
    正規の config.yaml を読み、電圧レンジ検証の severity を INFO に書き換えた
    設定で Config を生成する（テストデータで execute が完了するようにする）。
    """
    return Config.create(config_file_path=_get_overridden_config_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用の Logger fixture。

    im_cable_system.engine.shared.config の Logger をベースとする。
    必要に応じて、ここで書き換えロジックを記載する。
    """
    return Logger.create(config)


@pytest.fixture
def input_im_cable_system_dtos() -> InputDtos:
    """単一かご・二重かごの代表 InputDtos。"""
    objects: list[InputDto] = []
    objects.extend(make_input_im_cable_system_dtos_single_cage().get_all())
    objects.extend(make_input_im_cable_system_dtos_double_cage().get_all())
    return InputDtos(objects=objects)
