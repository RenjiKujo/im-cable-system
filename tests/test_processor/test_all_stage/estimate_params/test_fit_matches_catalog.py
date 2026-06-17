"""estimate_params の InputStage → ExecuteStage → OutputStage 結合テスト。

テスト用 fixture ではなく、``tests/input_files/estimate_params`` の統合 TSV
から InputDto を作り、以下の 2 種類を後段へ流す:

- Basic01 単独 + 残差判定（軽量 / integration マーク）
- CurrentDependent03 代表 4 パターン（重め / integration マーク）
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from im_cable_system.engine.processor.execute_stage import (
    EstimateParamsExecuteStage,
)
from im_cable_system.engine.processor.input_stage import (
    EstimateParamsInputStage,
)
from im_cable_system.engine.processor.output_stage import (
    EstimateParamsOutputStage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
)
from im_cable_system.engine.shared.dto.input import InputDto, InputDtos
from im_cable_system.engine.shared.dto.itm import ItmDto, ItmDtos
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
    OutputDtos,
)
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)
from tests.test_processor.test_all_stage.supply_slice_extraction import (
    find_matching_simulated_slip_slice,
    matching_slip_indices,
    normalized_max_abs_error,
)

# ``input_for_estimate_params*.tsv`` 上の候補列番号（1-based）から組み立てた名前。
# 順序は ``loader._build_system_name`` の
# ``{perf}_{primary}_{excitation}_{secondary_single}_{double_outer}_{double_inner}_{cable}``。
# cable_conductor 列: 1=NONE, 2=BASIC, 3=FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
# 4=CURRENT_DEPENDENT_SKIN_EFFECT_V1。
_CURRENT_DEPENDENT03_INPUT_NAMES: tuple[str, ...] = (
    # 1) すべて BASIC + ケーブル無し
    "CurrentDependent03_1_1_1_0_0_1",
    # 2) SLIP_DEPENDENT 系のみ非 BASIC + ケーブル無し
    "CurrentDependent03_1_2_2_0_0_1",
    # 3) 正解モデル（CURRENT_DEPENDENT 系で揃える）+ ケーブル無し
    "CurrentDependent03_3_3_4_0_0_1",
    # 4) すべて BASIC + ケーブル(CURRENT_DEPENDENT_SKIN_EFFECT_V1)
    "CurrentDependent03_1_1_1_0_0_4",
)
_CURRENT_DEPENDENT03_CORRECT_MODEL_NAME = "CurrentDependent03_3_3_4_0_0_1"

# 正解モデルは CurrentDependent03 自身の曲線を生成した等価回路と同一構造のため、
# 真値が bounds 内にある限りモデル結果は性能カーブを厳密に再現する。残差は
# optimizer 収束許容（ftol/xtol/gtol=1e-4）のみで決まり、実測の最大正規化誤差は
# 系列ごとに ≲ 1e-6。マージンを見て 1e-4 を許容上限とする。
_CURRENT_DEPENDENT03_MAX_NORMALIZED_ERROR = 1.0e-4

# Basic01 の正解モデル: すべて BASIC + ケーブル無し。
_BASIC01_CORRECT_MODEL_NAME = "Basic01_1_1_1_0_0_1"

# Basic01 を Basic01 自身の曲線にフィットさせた際の最大正規化誤差。
# 等価回路が同一かつ真値（primary/secondary inductance 1.79e-3 H）が bounds 内に
# あるため、残差は optimizer 収束許容（ftol/xtol/gtol=1e-4）のみで決まり厳密に
# 一致する（実測 ≲ 1e-6）。マージンを見て 1e-4 を許容上限とする。
_BASIC01_MAX_NORMALIZED_ERROR = 1.0e-4


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


# Basic01: 等価回路が同一で線形のため終点残差は収束許容のみで決まり極小。
# 実測 overall_rmse≈1.5e-8 / cost≈1.9e-14 / 各チャネル RMSE ≲ 1.4e-5。
# 1〜2 桁のマージンを足した上限で固定する。
_BASIC01_EXPECTED_REGRESSION = _ExpectedFitRegression(
    max_overall_rmse=1.0e-6,
    max_cost=1.0e-10,
    max_current_rmse=1.0e-5,
    max_power_rmse=1.0e-3,
    max_power_factor_rmse=1.0e-6,
    max_efficiency_rmse=1.0e-7,
    n_residual_elements=164,
    n_valid_curve_points=41,
)

# CurrentDependent03 正解モデル: 真値が bounds 内にあるため厳密再現に近いが、
# 電流依存反復を含むぶん Basic01 より終点残差はやや大きい。
# 実測 overall_rmse≈2.4e-5 / cost≈4.5e-8 / output_power RMSE≈1.4e-2。
_CURRENT_DEPENDENT03_EXPECTED_REGRESSION = _ExpectedFitRegression(
    max_overall_rmse=1.0e-3,
    max_cost=1.0e-5,
    max_current_rmse=1.0e-2,
    max_power_rmse=1.0e-1,
    max_power_factor_rmse=1.0e-3,
    max_efficiency_rmse=1.0e-3,
    n_residual_elements=164,
    n_valid_curve_points=41,
)


def _make_currentdependent03_job_spec(
    input_files_dir: Path,
) -> EstimateParamsJobSpec:
    """CurrentDependent03 用 estimate_params 統合 TSV を指す JobSpec。"""
    return EstimateParamsJobSpec(
        input_tsv_path=(
            input_files_dir
            / "estimate_params"
            / "input_for_estimate_params.tsv"
        ),
    )


def _make_basic01_job_spec(input_files_dir: Path) -> EstimateParamsJobSpec:
    """Basic01 用 estimate_params 統合 TSV を指す JobSpec。"""
    return EstimateParamsJobSpec(
        input_tsv_path=(
            input_files_dir
            / "estimate_params"
            / "input_for_estimate_params_basic01.tsv"
        ),
    )


def _select_inputs_by_name(
    inputs: InputDtos,
    names: tuple[str, ...],
) -> InputDtos:
    """指定名の InputDto だけを指定順で取り出す。"""
    by_name: dict[str, InputDto] = {
        dto.name.get_value(): dto for dto in inputs.get_all()
    }
    missing = [name for name in names if name not in by_name]
    if missing:
        raise AssertionError(f"InputDto が見つかりません: {missing}")
    return InputDtos(objects=[by_name[name] for name in names])


def _get_itm_by_name(itm_dtos: ItmDtos, name: str) -> ItmDto:
    """ItmDto を名前文字列で取得する。"""
    for dto in itm_dtos.get_all():
        if dto.name.get_value() == name:
            return dto
    raise AssertionError(f"ItmDto が見つかりません: {name}")


def _run_input_execute_output(
    config: IConfig,
    logger: ILogger,
    job_spec: EstimateParamsJobSpec,
    input_names: tuple[str, ...],
) -> tuple[ItmDtos, OutputDtos]:
    """指定名の InputDto を Input → Execute → Output まで通して返す。"""
    input_stage = EstimateParamsInputStage.create(
        config=config,
        logger=logger,
    )
    all_inputs = input_stage.process(job_spec)
    selected_inputs = _select_inputs_by_name(all_inputs, input_names)
    assert len(selected_inputs.get_all()) == len(input_names)

    execute_stage = EstimateParamsExecuteStage.create(
        config=config,
        logger=logger,
    )
    itm_dtos = execute_stage.process(selected_inputs)
    assert len(itm_dtos.get_all()) == len(selected_inputs.get_all())

    output_stage = EstimateParamsOutputStage.create(
        config=config,
        logger=logger,
    )
    output_dtos = output_stage.process(itm_dtos)
    assert len(output_dtos.get_all()) == len(selected_inputs.get_all())
    for dto in output_dtos.get_all():
        assert isinstance(dto, OutputDto)
        assert dto.result is not None
    return itm_dtos, output_dtos


def _get_output_by_name(output_dtos: OutputDtos, name: str) -> OutputDto:
    """OutputDto を名前文字列で取得する。"""
    for dto in output_dtos.get_all():
        if dto.name.get_value() == name:
            return dto
    raise AssertionError(f"OutputDto が見つかりません: {name}")


def _assert_slip_curve_matches_catalog(
    output: OutputDto,
    max_normalized_error: float,
) -> None:
    """同じ slip 点で出力・電流・力率・効率が許容誤差内か検証する。"""
    simulated, catalog = find_matching_simulated_slip_slice(output)
    simulated_indices = matching_slip_indices(simulated, catalog)

    series_pairs: tuple[tuple[str, np.ndarray, np.ndarray], ...] = (
        (
            "output_power",
            np.asarray(
                simulated.series.output_power_w,
                dtype=np.float64,
            )[simulated_indices],
            np.asarray(catalog.series.output_power_w, dtype=np.float64),
        ),
        (
            "input_current",
            np.asarray(
                simulated.series.input_current_magnitude_a,
                dtype=np.float64,
            )[simulated_indices],
            np.asarray(
                catalog.series.input_current_magnitude_a,
                dtype=np.float64,
            ),
        ),
        (
            "power_factor",
            np.asarray(
                simulated.series.power_factor,
                dtype=np.float64,
            )[simulated_indices],
            np.asarray(catalog.series.power_factor, dtype=np.float64),
        ),
        (
            "efficiency",
            np.asarray(
                simulated.series.efficiency,
                dtype=np.float64,
            )[simulated_indices],
            np.asarray(catalog.series.efficiency, dtype=np.float64),
        ),
    )

    for label, simulated_values, catalog_values in series_pairs:
        normalized_error = normalized_max_abs_error(
            simulated=simulated_values,
            catalog=catalog_values,
        )
        assert normalized_error <= max_normalized_error, (
            f"{output.name.get_value()} の {label} が許容誤差を超えています: "
            f"normalized_error={normalized_error}, "
            f"tolerance={max_normalized_error}"
        )


def _assert_correct_model_converged(
    itm_dtos: ItmDtos,
    correct_model_name: str,
    estimate_params_max_nfev: int,
) -> None:
    """指定モデルの最適化が打ち切り上限に達せず終わっていることを確認する。"""
    correct_itm = _get_itm_by_name(itm_dtos, correct_model_name)
    summary = correct_itm.estimate_params_fit_summary
    assert summary is not None
    assert summary.optimizer_result.nfev < estimate_params_max_nfev


def _assert_no_parameter_pinned_to_bound(
    summary: EstimateParamsFitSummaryDto,
    model_name: str,
) -> None:
    """非固定パラメータが探索境界に張り付いていないことを確認する。

    正解モデルでは真値が bounds 内部にあるため、フィット結果が下限・上限へ
    張り付くのは退行（bounds 不整合・スケール崩れ・発散）の兆候とみなす。
    """
    pinned = [
        param.path
        for param in summary.fitted_parameters
        if not param.is_fixed
        and (param.is_at_lower_bound or param.is_at_upper_bound)
    ]
    assert not pinned, (
        f"{model_name} のフィット結果が探索境界に張り付いています: {pinned}"
    )


def _assert_fit_summary_regression(
    itm_dtos: ItmDtos,
    model_name: str,
    expected: _ExpectedFitRegression,
) -> None:
    """fit summary の終点残差・cost・チャネル別 RMSE・構造を固定値で検証する。

    曲線リグレッション（catalog 一致）に加え、最適化の「終わり方」自体を
    数値で固定することで、収束品質の退行（残差悪化・関数評価増・チャネル
    バランス崩れ）を検知する。

    Args:
        itm_dtos: Execute ステージ出力。
        model_name: 検証対象モデル名。
        expected: 許容上限と構造の期待値。

    Raises:
        AssertionError: summary 欠落・最適化失敗、または各指標が許容上限を
            超過した、構造（残差長・有効点数）が期待と異なる場合。
    """
    itm = _get_itm_by_name(itm_dtos, model_name)
    summary = itm.estimate_params_fit_summary
    assert summary is not None

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

    _assert_no_parameter_pinned_to_bound(summary=summary, model_name=model_name)


@pytest.mark.integration
def test_estimate_params_basic01_matches_catalog(
    all_stage_estimate_params_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """Basic01 を Basic01 自身の曲線にフィットし残差が十分小さいか検証する。

    BASIC 系のみで構成される Basic01 はモデルが線形で電流依存反復を含まないため、
    解析的にほぼ完全フィットが期待できる。``iteration 回数`` ではなく
    正規化最大絶対誤差で良否を判定する。
    """
    pytest.importorskip("matplotlib")

    itm_dtos, output_dtos = _run_input_execute_output(
        config=all_stage_estimate_params_config,
        logger=logger,
        job_spec=_make_basic01_job_spec(input_files_dir),
        input_names=(_BASIC01_CORRECT_MODEL_NAME,),
    )
    _assert_fit_summary_regression(
        itm_dtos=itm_dtos,
        model_name=_BASIC01_CORRECT_MODEL_NAME,
        expected=_BASIC01_EXPECTED_REGRESSION,
    )
    _assert_slip_curve_matches_catalog(
        _get_output_by_name(output_dtos, _BASIC01_CORRECT_MODEL_NAME),
        max_normalized_error=_BASIC01_MAX_NORMALIZED_ERROR,
    )


@pytest.mark.integration
def test_estimate_params_selected_patterns_match_catalog(
    all_stage_estimate_params_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
    estimate_params_max_nfev: int,
) -> None:
    """CurrentDependent03 の代表 4 パターンを通し、正解モデルが catalog を再現するか検証する。

    Input → Execute → Output まで通し、正解モデルの最適化が打ち切り上限に
    達せず収束し、かつ simulated slip 曲線が catalog 曲線を許容誤差内で
    再現するか（曲線リグレッション）を確認する。
    """
    pytest.importorskip("matplotlib")

    itm_dtos, output_dtos = _run_input_execute_output(
        config=all_stage_estimate_params_config,
        logger=logger,
        job_spec=_make_currentdependent03_job_spec(input_files_dir),
        input_names=_CURRENT_DEPENDENT03_INPUT_NAMES,
    )
    _assert_correct_model_converged(
        itm_dtos=itm_dtos,
        correct_model_name=_CURRENT_DEPENDENT03_CORRECT_MODEL_NAME,
        estimate_params_max_nfev=estimate_params_max_nfev,
    )
    _assert_fit_summary_regression(
        itm_dtos=itm_dtos,
        model_name=_CURRENT_DEPENDENT03_CORRECT_MODEL_NAME,
        expected=_CURRENT_DEPENDENT03_EXPECTED_REGRESSION,
    )
    _assert_slip_curve_matches_catalog(
        _get_output_by_name(
            output_dtos,
            _CURRENT_DEPENDENT03_CORRECT_MODEL_NAME,
        ),
        max_normalized_error=_CURRENT_DEPENDENT03_MAX_NORMALIZED_ERROR,
    )
