"""戦略C（摩擦・風損＋漂遊負荷損）の効果検証。

``input_for_estimate_params_mechanical_loss.tsv``（合成教師曲線、正解モデルは
``SlipDependentShaftDeduction01`` = SlipDependent01 と同一の R/L・一次/励磁/二次
モデルに ``k_friction_windage=0.02`` / ``k_stray_load=0.01`` を加えたもの）を
``im_friction_windage`` / ``im_stray_load`` の NONE × 数式 2 候補ずつ、
計 4 パターンで fit する。

検証の本題（4_test_strategy.md の方針どおり、収束そのものではなく残差契約
で書く）:
    - 両方 ``CONSTANT_V1`` / ``CURRENT_DEPENDENT_QUADRATIC_V1`` で fit した方が、
      両方 ``NONE`` で fit するより η チャネル RMSE が小さい
      （＝ 軸出力控除を電気損失モデルへ無理やり吸収させていない）。
    - 両方有効時、推定 R1（primary_resistance）・R2（secondary_resistance）・
      Rm（excitation_resistance）が真値からの相対偏差の許容内に収まる。
    - 両方有効時、``k_friction_windage`` / ``k_stray_load`` が真値近傍に戻る。

力率重みは 0.1 に下げる（``docs/estimate_params_curve_fitting_consistency.md``
戦略C: 力率は電気損モデルの第 4 自由度を生まないため参考値扱いとする方針、
かつローカル実測での知見「記載力率が外れ値」と同じ理由）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.processor.execute_stage import (
    EstimateParamsExecuteStage,
)
from im_cable_system.engine.processor.input_stage import (
    EstimateParamsInputStage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
)
from im_cable_system.engine.shared.dto.itm import ItmDto, ItmDtos
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)

# 正解モデル（SlipDependentShaftDeduction01）の真値。
# src/im_cable_system/catalog/im_series_catalog.yaml を正とする。
_TRUE_PRIMARY_RESISTANCE = 0.4
_TRUE_SECONDARY_RESISTANCE = 0.3398
_TRUE_EXCITATION_RESISTANCE = 235.2941176
_TRUE_K_FRICTION_WINDAGE = 0.02
_TRUE_K_STRAY_LOAD = 0.01

# 8 インデックス命名: {perf}_{p}_{e}_{ss}_{sdo}_{sdi}_{fw}_{sl}_{c}。
# p=e=ss=1（SLIP_DEPENDENT 系のみを候補にしているため常に 1）、sdo=sdi=0
# （単一かごのため不採用）、c=0（cable_conductor_model 行を省略したため不採用）。
_NAME_BOTH_NONE = "SlipDependentShaftDeduction01_1_1_1_0_0_1_1_0"
_NAME_STRAY_ONLY = "SlipDependentShaftDeduction01_1_1_1_0_0_1_2_0"
_NAME_FRICTION_ONLY = "SlipDependentShaftDeduction01_1_1_1_0_0_2_1_0"
_NAME_BOTH_ENABLED = "SlipDependentShaftDeduction01_1_1_1_0_0_2_2_0"

# 両方有効時の R1/R2/Rm・軸出力控除係数の相対偏差許容上限。
# 力率重み 0.1・既定の optimizer 設定（ftol/xtol/gtol=1e-4, max_nfev=120）での
# 実測値: primary_resistance ≈ +0.6%, secondary_resistance ≈ -0.6%,
# excitation_resistance ≈ -0.4%, k_friction_windage ≈ +0.2%,
# k_stray_load ≈ -5.0%。1〜数倍のマージンを見て固定する。
_MAX_RELATIVE_DEVIATION_RL = 0.05
_MAX_RELATIVE_DEVIATION_DEDUCTION_COEFF = 0.20

# 両方 NONE の η チャネル RMSE 実測値 ≈ 9.9e-4。両方有効時は ≈ 5.3e-7 まで
# 3 桁以上小さくなる。退行検知のため上限を固定する
# （「小さくなる」ことが本題なので、両方 NONE 比の相対値でも検証する）。
_MAX_EFFICIENCY_RMSE_BOTH_NONE = 5.0e-3
_MAX_EFFICIENCY_RMSE_BOTH_ENABLED = 1.0e-4


@pytest.fixture
def estimate_params_residual_weights() -> dict[str, float]:
    """力率重みを 0.1 に下げる（戦略C の検証方針。モジュール docstring 参照）。"""
    return {
        "current": 1.0,
        "power": 1.0,
        "power_factor": 0.1,
        "efficiency": 1.0,
    }


def _make_shaft_output_deduction_job_spec(
    input_files_dir: Path,
) -> EstimateParamsJobSpec:
    """摩擦・風損＋漂遊負荷損 4 パターン用 estimate_params 統合 TSV。"""
    return EstimateParamsJobSpec(
        input_tsv_path=(
            input_files_dir
            / "estimate_params"
            / "input_for_estimate_params_mechanical_loss.tsv"
        ),
    )


def _get_itm_by_name(itm_dtos: ItmDtos, name: str) -> ItmDto:
    for dto in itm_dtos.get_all():
        if dto.name.get_value() == name:
            return dto
    raise AssertionError(f"ItmDto が見つかりません: {name}")


def _summary_of(itm_dtos: ItmDtos, name: str) -> EstimateParamsFitSummaryDto:
    itm = _get_itm_by_name(itm_dtos, name)
    summary = itm.estimate_params_fit_summary
    assert summary is not None, (
        f"{name} の estimate_params_fit_summary が None です"
    )
    assert summary.optimizer_result.success, (
        f"{name} の最適化が success=False で終了しました: "
        f"message={summary.optimizer_result.message}"
    )
    return summary


def _fitted_value(summary: EstimateParamsFitSummaryDto, path: str) -> float:
    for param in summary.fitted_parameters:
        if param.path == path:
            return param.fitted_value
    raise AssertionError(f"記述子 path が見つかりません: {path}")


def _relative_deviation(actual: float, true_value: float) -> float:
    return abs(actual - true_value) / abs(true_value)


@pytest.mark.integration
def test_shaft_output_deduction_reduces_efficiency_rmse(
    all_stage_estimate_params_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """両方有効の fit は両方 NONE の fit より η チャネル RMSE が小さい。

    ＝ 軸出力控除を考慮しないと、モデルは η 残差を R1/R2/Rm へ無理やり吸収する。
    """
    input_stage = EstimateParamsInputStage.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    all_inputs = input_stage.process(
        _make_shaft_output_deduction_job_spec(input_files_dir)
    )
    execute_stage = EstimateParamsExecuteStage.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    itm_dtos = execute_stage.process(all_inputs)
    assert len(itm_dtos.get_all()) == 4

    both_none = _summary_of(itm_dtos, _NAME_BOTH_NONE)
    both_enabled = _summary_of(itm_dtos, _NAME_BOTH_ENABLED)

    assert both_none.im_efficiency.rmse <= _MAX_EFFICIENCY_RMSE_BOTH_NONE
    assert both_enabled.im_efficiency.rmse <= _MAX_EFFICIENCY_RMSE_BOTH_ENABLED
    # 本題: 両方有効の方が η RMSE が明確に小さい。
    assert both_enabled.im_efficiency.rmse < both_none.im_efficiency.rmse


@pytest.mark.integration
def test_shaft_output_deduction_enabled_recovers_true_rl_and_coefficients(
    all_stage_estimate_params_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """両方有効時、R1/R2/Rm と軸出力控除係数が真値近傍に戻る。

    ＝ 損失を R が吸収せず、軸出力控除モデル自身が損失を説明できている。
    """
    input_stage = EstimateParamsInputStage.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    all_inputs = input_stage.process(
        _make_shaft_output_deduction_job_spec(input_files_dir)
    )
    execute_stage = EstimateParamsExecuteStage.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    itm_dtos = execute_stage.process(all_inputs)

    summary = _summary_of(itm_dtos, _NAME_BOTH_ENABLED)

    r1 = _fitted_value(summary, "im.primary_resistance")
    r2 = _fitted_value(summary, "im.secondary_resistance.SINGLE")
    rm = _fitted_value(summary, "im.excitation_resistance")
    k_fw = _fitted_value(
        summary, "im.friction_windage_model.params.k_friction_windage"
    )
    k_sl = _fitted_value(summary, "im.stray_load_model.params.k_stray_load")

    assert (
        _relative_deviation(r1, _TRUE_PRIMARY_RESISTANCE)
        <= _MAX_RELATIVE_DEVIATION_RL
    ), (
        f"R1 が真値から乖離しています: fitted={r1}, true={_TRUE_PRIMARY_RESISTANCE}"
    )
    assert (
        _relative_deviation(r2, _TRUE_SECONDARY_RESISTANCE)
        <= _MAX_RELATIVE_DEVIATION_RL
    ), (
        f"R2 が真値から乖離しています: fitted={r2}, true={_TRUE_SECONDARY_RESISTANCE}"
    )
    assert (
        _relative_deviation(rm, _TRUE_EXCITATION_RESISTANCE)
        <= _MAX_RELATIVE_DEVIATION_RL
    ), (
        f"Rm が真値から乖離しています: fitted={rm}, true={_TRUE_EXCITATION_RESISTANCE}"
    )
    assert (
        _relative_deviation(k_fw, _TRUE_K_FRICTION_WINDAGE)
        <= _MAX_RELATIVE_DEVIATION_DEDUCTION_COEFF
    ), (
        f"k_friction_windage が真値から乖離しています: "
        f"fitted={k_fw}, true={_TRUE_K_FRICTION_WINDAGE}"
    )
    assert (
        _relative_deviation(k_sl, _TRUE_K_STRAY_LOAD)
        <= _MAX_RELATIVE_DEVIATION_DEDUCTION_COEFF
    ), (
        f"k_stray_load が真値から乖離しています: fitted={k_sl}, true={_TRUE_K_STRAY_LOAD}"
    )


@pytest.mark.integration
def test_friction_windage_only_and_stray_load_only_do_not_crash(
    all_stage_estimate_params_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """片側だけ有効な 2 パターンも fit が正常終了する（切り分け用の回帰スモーク）。"""
    input_stage = EstimateParamsInputStage.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    all_inputs = input_stage.process(
        _make_shaft_output_deduction_job_spec(input_files_dir)
    )
    execute_stage = EstimateParamsExecuteStage.create(
        config=all_stage_estimate_params_config,
        logger=logger,
    )
    itm_dtos = execute_stage.process(all_inputs)

    for name in (_NAME_STRAY_ONLY, _NAME_FRICTION_ONLY):
        summary = _summary_of(itm_dtos, name)
        assert summary.im_efficiency.rmse < _MAX_EFFICIENCY_RMSE_BOTH_NONE
