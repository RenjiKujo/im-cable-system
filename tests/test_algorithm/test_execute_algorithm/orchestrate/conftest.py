"""全体実行オーケストレーターテスト用の共通 fixture。

単カゴ（single cage）用と二重かご（double cage）用の InputDtos を
名前付き fixture で分離する。

設定は config_test_orchestrator.yaml の1つのみ。

電流反復の収束基準（line_current / phase_current / max_over_merged_currents）は
create_config_with_current_estimation_iteration で一時 YAML に書き出して切り替える。
fixture config_current_estimation_convergence_criterion が上記3パターンを param で展開する。
"""

from pathlib import Path

import pytest
import yaml

from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)


def _get_config_file_path() -> Path:
    """設定ファイルのパスを取得する。

    全体実行オーケストレーターの統合テストでは、電流電圧レンジ検証を IGNORE にした
    テスト用設定を使用し、execute が最後まで完了するようにする。
    """
    _this_dir = Path(__file__).resolve().parent
    return _this_dir / "config_test_orchestrator.yaml"


def create_config_with_current_estimation_iteration(
    tmp_path: Path,
    *,
    convergence_criterion: str,
    max_iterations: int = 20,
    convergence_tolerance: float = 1.0e-6,
) -> IConfig:
    """current_estimation.iteration のみ差し替えた Config を一時 YAML から生成する。

    Args:
        tmp_path: 一時ディレクトリ（pytest の tmp_path）。
        convergence_criterion: line_current | phase_current | max_over_merged_currents。
        max_iterations: 反復上限（初回 VC 含む）。
        convergence_tolerance: 相対変化しきい値。

    Returns:
        IConfig: 生成した設定。
    """
    config_path = _get_config_file_path()
    with config_path.open(encoding="utf-8") as file_handle:
        data = yaml.safe_load(file_handle)
    calculation = data.setdefault("calculation", {})
    execute_block = calculation.setdefault("execute", {})
    current_estimation = execute_block.setdefault("current_estimation", {})
    iteration = current_estimation.setdefault("iteration", {})
    iteration["convergence_criterion"] = convergence_criterion
    iteration["max_iterations"] = max_iterations
    iteration["convergence_tolerance"] = convergence_tolerance
    out_path = tmp_path / "config_current_estimation_iteration.yaml"
    with out_path.open("w", encoding="utf-8") as file_handle:
        yaml.safe_dump(data, file_handle, allow_unicode=True, sort_keys=False)
    return Config.create(config_file_path=out_path)


_CURRENT_ESTIMATION_CONVERGENCE_CRITERIA: tuple[str, ...] = (
    "line_current",
    "phase_current",
    "max_over_merged_currents",
)


@pytest.fixture(
    params=_CURRENT_ESTIMATION_CONVERGENCE_CRITERIA,
)
def config_current_estimation_convergence_criterion(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> IConfig:
    """current_estimation.iteration.convergence_criterion を param ごとに切替えた Config。

    config_test_orchestrator.yaml をベースに一時 YAML を生成する。
    同一テストが line_current / phase_current / max_over_merged_currents の
    いずれでも実行される（計3回）。
    """
    criterion: str = request.param
    return create_config_with_current_estimation_iteration(
        tmp_path,
        convergence_criterion=criterion,
    )


@pytest.fixture
def config() -> IConfig:
    """テスト用の Config fixture。"""
    return Config.create(config_file_path=_get_config_file_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用の Logger fixture（orchestrate 用 config）。"""
    return Logger.create(config)
