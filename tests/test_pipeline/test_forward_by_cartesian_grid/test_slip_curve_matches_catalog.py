"""forward_by_cartesian_grid pipeline 結合テスト。

``ForwardByCartesianGridPipeline``（Input → Execute → Output）を 1 回の
``run`` で通し、simulated slip 曲線が catalog 曲線を許容誤差内で
再現するか（曲線リグレッション）を検証する。検証内容は
``tests/test_processor/test_all_stage/forward_by_cartesian_grid`` と同一で、
ステージ個別呼び出しの代わりに pipeline 経由で実行する点だけが異なる。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from im_cable_system.engine.pipeline import (
    ForwardByCartesianGridPipeline,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
)
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
    ForwardJobSpecs,
)
from tests.test_processor.test_all_stage.supply_slice_extraction import (
    find_matching_simulated_slip_slice,
    matching_slip_indices,
    normalized_max_abs_error,
)

_BASIC01_MAX_NORMALIZED_ERROR = 0.06
_CURRENT_DEPENDENT03_MAX_NORMALIZED_ERROR = 1.0e-10

# catalog 一致（相対誤差）だけでは catalog 自体が変わると追従してしまうため、
# simulated 曲線の代表スカラ（slip 点数・各系列の最大値）を絶対ゴールデン値で
# 固定し、forward パイプラインの数値退行を独立に検知する。値は決定的なので
# 相対許容 1e-6 で照合する。
_SIMULATED_SERIES_GOLDEN_RTOL = 1.0e-6


class _ExpectedSimulatedSeries:
    """simulated slip 曲線の代表スカラ・ゴールデン値。"""

    def __init__(
        self,
        n_slip: int,
        max_output_power: float,
        max_input_current: float,
        max_power_factor: float,
        max_efficiency: float,
        max_torque: float,
    ) -> None:
        """ゴールデン値を保持する。"""
        self.n_slip = n_slip
        self.max_output_power = max_output_power
        self.max_input_current = max_input_current
        self.max_power_factor = max_power_factor
        self.max_efficiency = max_efficiency
        self.max_torque = max_torque


_BASIC01_SIMULATED_GOLDEN = _ExpectedSimulatedSeries(
    n_slip=155,
    max_output_power=9597.871305056822,
    max_input_current=90.80189892196103,
    max_power_factor=0.9073331175858215,
    max_efficiency=0.8936438208902928,
    max_torque=80.01305643072335,
)
_CURRENT_DEPENDENT03_SIMULATED_GOLDEN = _ExpectedSimulatedSeries(
    n_slip=155,
    max_output_power=9273.71339357011,
    max_input_current=87.92487289090093,
    max_power_factor=0.918335842154689,
    max_efficiency=0.8833098382355307,
    max_torque=77.99440538002007,
)


def _make_job_specs(input_files_dir: Path) -> ForwardJobSpecs:
    """Basic01 と CurrentDependent03 の CartesianGrid 用 JobSpecs。"""
    return ForwardJobSpecs(
        specs=(
            ForwardJobSpec(
                series_selection_path=(
                    input_files_dir / "series_forward" / "basic01_nocable.tsv"
                ),
                axes_path=(
                    input_files_dir
                    / "axes_forward_by_cartesian_grid"
                    / "cartesian_grid_v1.tsv"
                ),
                performance_curve_path=(
                    input_files_dir
                    / "im_performance_curve"
                    / "currentdependent03_50Hz_115V.tsv"
                ),
            ),
            ForwardJobSpec(
                series_selection_path=(
                    input_files_dir
                    / "series_forward"
                    / "currentdependent03_nocable.tsv"
                ),
                axes_path=(
                    input_files_dir
                    / "axes_forward_by_cartesian_grid"
                    / "cartesian_grid_v1.tsv"
                ),
                performance_curve_path=(
                    input_files_dir
                    / "im_performance_curve"
                    / "currentdependent03_50Hz_115V.tsv"
                ),
            ),
        ),
    )


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


def _assert_simulated_series_golden(
    output: OutputDto,
    expected: _ExpectedSimulatedSeries,
) -> None:
    """simulated slip 曲線の代表スカラが固定ゴールデン値と一致するか検証する。

    catalog と同じ供給条件の simulated スライスを取り、slip 点数と各系列の
    最大値を絶対値で照合する。catalog 依存の相対比較とは独立に forward 計算の
    退行を捉える。

    Args:
        output: 検証対象 OutputDto。
        expected: simulated 系列のゴールデン値。

    Raises:
        AssertionError: slip 点数が異なる、または最大値が相対許容を超えて
            ずれた場合。
    """
    simulated, _ = find_matching_simulated_slip_slice(output)
    name = output.name.get_value()

    slip_values = np.asarray(simulated.slip, dtype=np.float64)
    assert slip_values.size == expected.n_slip, (
        f"{name} の simulated slip 点数が変化しました: "
        f"actual={slip_values.size}, expected={expected.n_slip}"
    )

    golden_checks: tuple[tuple[str, np.ndarray, float], ...] = (
        (
            "max_output_power",
            np.asarray(simulated.series.output_power_w, dtype=np.float64),
            expected.max_output_power,
        ),
        (
            "max_input_current",
            np.asarray(
                simulated.series.input_current_magnitude_a,
                dtype=np.float64,
            ),
            expected.max_input_current,
        ),
        (
            "max_power_factor",
            np.asarray(simulated.series.power_factor, dtype=np.float64),
            expected.max_power_factor,
        ),
        (
            "max_efficiency",
            np.asarray(simulated.series.efficiency, dtype=np.float64),
            expected.max_efficiency,
        ),
        (
            "max_torque",
            np.asarray(simulated.series.torque_nm, dtype=np.float64),
            expected.max_torque,
        ),
    )
    for label, series_values, golden_value in golden_checks:
        actual_value = float(np.nanmax(series_values))
        assert np.isclose(
            actual_value,
            golden_value,
            rtol=_SIMULATED_SERIES_GOLDEN_RTOL,
            atol=0.0,
        ), (
            f"{name} の {label} がゴールデン値からずれています: "
            f"actual={actual_value}, expected={golden_value}, "
            f"rtol={_SIMULATED_SERIES_GOLDEN_RTOL}"
        )


@pytest.mark.integration
def test_cartesian_grid_matches_catalog(
    all_stage_cartesian_grid_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """Basic01 と CurrentDependent03 の simulated slip 曲線が catalog と一致するか検証する。

    ``ForwardByCartesianGridPipeline`` を通し、同じ供給条件・slip 点で出力・
    電流・力率・効率が許容誤差内かを系列ごとに確認する。加えて、simulated
    曲線の代表スカラ（slip 点数・各系列の最大値）を絶対ゴールデン値で固定し、
    catalog 依存の比較とは独立に forward 計算の退行も検知する。
    """
    pytest.importorskip("matplotlib")

    job_specs = _make_job_specs(input_files_dir)
    pipeline = ForwardByCartesianGridPipeline.create(
        config=all_stage_cartesian_grid_config,
        logger=logger,
    )
    output_dtos = pipeline.run(input=job_specs)
    assert len(output_dtos.get_all()) == len(job_specs.specs)
    outputs = {dto.name.get_value(): dto for dto in output_dtos.get_all()}
    assert set(outputs) == {
        "Basic01_NoCable",
        "CurrentDependent03_NoCable",
    }
    for output in outputs.values():
        assert isinstance(output, OutputDto)
        assert output.result is not None

    _assert_slip_curve_matches_catalog(
        outputs["Basic01_NoCable"],
        max_normalized_error=_BASIC01_MAX_NORMALIZED_ERROR,
    )
    _assert_slip_curve_matches_catalog(
        outputs["CurrentDependent03_NoCable"],
        max_normalized_error=_CURRENT_DEPENDENT03_MAX_NORMALIZED_ERROR,
    )
    _assert_simulated_series_golden(
        outputs["Basic01_NoCable"],
        expected=_BASIC01_SIMULATED_GOLDEN,
    )
    _assert_simulated_series_golden(
        outputs["CurrentDependent03_NoCable"],
        expected=_CURRENT_DEPENDENT03_SIMULATED_GOLDEN,
    )
