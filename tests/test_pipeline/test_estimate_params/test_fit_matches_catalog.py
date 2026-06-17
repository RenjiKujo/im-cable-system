"""estimate_params pipeline 結合テスト。

``EstimateParamsPipeline``（Input → Execute → Output）を 1 回の
``run`` で通し、各候補モデルの fit summary（収束成否・残差構造・
終点残差／cost／チャネル別 RMSE）を固定ゴールデン値で検証する。検証思想は
``tests/test_processor/test_all_stage/estimate_params`` と同一だが、pipeline には
入力選択ステップが無いため、少数モデルに展開される brief な統合 TSV を用い、
展開された全モデルに fit summary リグレッションをかける。

正解モデル（真値が bounds 内）は brief に含まれないため、catalog を厳密再現
する slip 曲線一致（all_stage の ``_assert_slip_curve_matches_catalog``）は
対象外とし、fit summary リグレッションで数値退行を検知する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from im_cable_system.engine.pipeline import (
    EstimateParamsPipeline,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
    OutputDtos,
)
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)

# brief 統合 TSV が展開する候補モデル名（少数・全件 fit しても軽量）。
_BRIEF_MODEL_NAMES: tuple[str, ...] = (
    "CurrentDependent03_1_1_1_0_0_0",
    "CurrentDependent03_1_1_2_0_0_0",
    "CurrentDependent03_1_2_1_0_0_0",
    "CurrentDependent03_1_2_2_0_0_0",
)


@dataclass(frozen=True)
class _ExpectedFitRegression:
    """fit summary に対するリグレッション期待値（許容上限・構造の正解）。

    最適化はデータ・設定が固定なら決定的なため、終点残差・cost・チャネル別
    RMSE を「実測値に十分なマージンを足した上限」で固定し、後段リファクタや
    数値処理変更による退行を検知する。``n_*`` は格子・チャネル構造の正解
    （= 厳密一致）として持つ。

    Attributes:
        max_overall_rmse: 終点の重み付き残差 RMS の許容上限。
        max_cost: optimizer cost（0.5*Σr^2）の許容上限。
        max_current_rmse: |I| チャネル RMSE の許容上限 [A]。
        max_power_rmse: 出力電力チャネル RMSE の許容上限 [W]。
        max_power_factor_rmse: 力率チャネル RMSE の許容上限 [-]。
        max_efficiency_rmse: 効率チャネル RMSE の許容上限 [-]。
        n_residual_elements: 終点残差ベクトル長（= 有効点数 × チャネル数）。
        n_valid_curve_points: いずれかのチャネルが観測済みの格子点数。
    """

    max_overall_rmse: float
    max_cost: float
    max_current_rmse: float
    max_power_rmse: float
    max_power_factor_rmse: float
    max_efficiency_rmse: float
    n_residual_elements: int
    n_valid_curve_points: int


# brief 各モデルの実測 fit summary（決定的）に 1〜2 桁のマージンを足した上限。
# 構造（n_residual_elements=164 / n_valid_curve_points=41）は全モデル共通。
_BRIEF_EXPECTED_REGRESSIONS: dict[str, _ExpectedFitRegression] = {
    "CurrentDependent03_1_1_1_0_0_0": _ExpectedFitRegression(
        max_overall_rmse=1.0e-3,
        max_cost=1.0e-4,
        max_current_rmse=1.0e-2,
        max_power_rmse=1.0,
        max_power_factor_rmse=1.0e-3,
        max_efficiency_rmse=1.0e-3,
        n_residual_elements=164,
        n_valid_curve_points=41,
    ),
    "CurrentDependent03_1_1_2_0_0_0": _ExpectedFitRegression(
        max_overall_rmse=1.0e-4,
        max_cost=1.0e-6,
        max_current_rmse=1.0e-3,
        max_power_rmse=1.0e-1,
        max_power_factor_rmse=1.0e-4,
        max_efficiency_rmse=1.0e-4,
        n_residual_elements=164,
        n_valid_curve_points=41,
    ),
    "CurrentDependent03_1_2_1_0_0_0": _ExpectedFitRegression(
        max_overall_rmse=1.0e-3,
        max_cost=1.0e-4,
        max_current_rmse=1.0e-2,
        max_power_rmse=1.0,
        max_power_factor_rmse=1.0e-3,
        max_efficiency_rmse=1.0e-3,
        n_residual_elements=164,
        n_valid_curve_points=41,
    ),
    "CurrentDependent03_1_2_2_0_0_0": _ExpectedFitRegression(
        max_overall_rmse=1.0e-4,
        max_cost=1.0e-6,
        max_current_rmse=1.0e-3,
        max_power_rmse=1.0e-1,
        max_power_factor_rmse=1.0e-4,
        max_efficiency_rmse=1.0e-4,
        n_residual_elements=164,
        n_valid_curve_points=41,
    ),
}


def _make_brief_job_spec(input_files_dir: Path) -> EstimateParamsJobSpec:
    """brief 統合 TSV（少数モデル）を指す JobSpec。"""
    return EstimateParamsJobSpec(
        input_tsv_path=(
            input_files_dir
            / "estimate_params"
            / "input_for_estimate_params_brief.tsv"
        ),
    )


def _get_output_by_name(output_dtos: OutputDtos, name: str) -> OutputDto:
    """OutputDto を名前文字列で取得する。"""
    for dto in output_dtos.get_all():
        if dto.name.get_value() == name:
            return dto
    raise AssertionError(f"OutputDto が見つかりません: {name}")


def _assert_fit_summary_regression(
    output: OutputDto,
    expected: _ExpectedFitRegression,
) -> None:
    """fit summary の終点残差・cost・チャネル別 RMSE・構造を固定値で検証する。

    pipeline は ``ItmDtos`` を外に出さないため、``OutputDto`` に載る
    ``estimate_params_fit_summary`` から検証する（all_stage の ItmDto 経由検証と
    同じ指標を確認する）。

    Args:
        output: 検証対象 OutputDto。
        expected: 許容上限と構造の期待値。

    Raises:
        AssertionError: summary 欠落・最適化失敗、または各指標が許容上限を
            超過した、構造（残差長・有効点数）が期待と異なる場合。
    """
    model_name = output.name.get_value()
    summary = output.estimate_params_fit_summary
    assert summary is not None, (
        f"{model_name} の estimate_params_fit_summary が None です"
    )

    assert summary.optimizer_result.success, (
        f"{model_name} の最適化が success=False で終了しました: "
        f"message={summary.optimizer_result.message}"
    )

    assert summary.n_residual_elements == expected.n_residual_elements, (
        f"{model_name} の残差ベクトル長が変化しました: "
        f"actual={summary.n_residual_elements}, "
        f"expected={expected.n_residual_elements}"
    )
    assert summary.n_valid_curve_points == expected.n_valid_curve_points, (
        f"{model_name} の有効格子点数が変化しました: "
        f"actual={summary.n_valid_curve_points}, "
        f"expected={expected.n_valid_curve_points}"
    )

    metric_checks: tuple[tuple[str, float, float], ...] = (
        (
            "overall_rmse_weighted_residual",
            summary.overall_rmse_weighted_residual,
            expected.max_overall_rmse,
        ),
        (
            "optimizer_cost",
            summary.optimizer_result.cost,
            expected.max_cost,
        ),
        (
            "line_current_rmse",
            summary.line_current.rmse,
            expected.max_current_rmse,
        ),
        (
            "output_power_rmse",
            summary.output_power.rmse,
            expected.max_power_rmse,
        ),
        (
            "power_factor_rmse",
            summary.power_factor.rmse,
            expected.max_power_factor_rmse,
        ),
        (
            "im_efficiency_rmse",
            summary.im_efficiency.rmse,
            expected.max_efficiency_rmse,
        ),
    )
    for label, actual_value, max_value in metric_checks:
        assert np.isfinite(actual_value), (
            f"{model_name} の {label} が有限値ではありません: {actual_value}"
        )
        assert actual_value <= max_value, (
            f"{model_name} の {label} が許容上限を超えています: "
            f"actual={actual_value}, max={max_value}"
        )


@pytest.mark.integration
def test_estimate_params_brief_fit_summary_regression(
    all_stage_estimate_params_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """brief 統合 TSV を ``EstimateParamsPipeline`` で通し fit summary を検証する。

    展開された全候補モデルを Input → Execute → Output まで通し、各モデルの
    出力 DTO が result と fit summary を持ち、収束成否・残差構造・終点残差／
    cost／チャネル別 RMSE が固定ゴールデン上限内かを確認する。
    """
    pytest.importorskip("matplotlib")

    pipeline = EstimateParamsPipeline.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    output_dtos = pipeline.run(
        input=_make_brief_job_spec(input_files_dir),
    )
    outputs = output_dtos.get_all()
    assert {dto.name.get_value() for dto in outputs} == set(_BRIEF_MODEL_NAMES)
    for output in outputs:
        assert isinstance(output, OutputDto)
        assert output.result is not None

    for model_name, expected in _BRIEF_EXPECTED_REGRESSIONS.items():
        _assert_fit_summary_regression(
            _get_output_by_name(output_dtos, model_name),
            expected=expected,
        )
