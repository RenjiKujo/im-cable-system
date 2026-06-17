"""forward_by_operating_points pipeline 結合テスト。

``ForwardByOperatingPointsPipeline``（Input → Execute → Output）を 1 回の
``run`` で通し、変換後の各 OutputDto が result を持ち、形状・主要
系列の代表値が固定ゴールデン値と一致するかを検証する。検証内容は
``tests/test_processor/test_all_stage/forward_by_operating_points`` と同一で、
ステージ個別呼び出しの代わりに pipeline 経由で実行する点だけが異なる。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from im_cable_system.engine.pipeline import (
    ForwardByOperatingPointsPipeline,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
    ForwardJobSpecs,
)

_EXPECTED_OPERATING_POINT_COUNT = 30
_SIMULATED_SERIES_GOLDEN_RTOL = 1.0e-6
_EXPECTED_MAX_OUTPUT_POWER_W = 2100.8402484133862
_EXPECTED_MAX_INPUT_CURRENT_A = 9.3162804869164
_EXPECTED_MAX_EFFICIENCY = 0.8862805999239819
_EXPECTED_MAX_TORQUE_NM = 13.569152280133359
_EXPECTED_MIN_SPEED_RPM = 1186.8
_EXPECTED_MAX_SPEED_RPM = 2053.8
_EXPECTED_MAX_POWER_FACTOR = 0.8806490162491425


def _make_job_specs(input_files_dir: Path) -> ForwardJobSpecs:
    """CurrentDependent03 の OperatingPoints 用 JobSpecs。"""
    return ForwardJobSpecs(
        specs=(
            ForwardJobSpec(
                series_selection_path=(
                    input_files_dir
                    / "series_forward"
                    / "currentdependent03_nocable.tsv"
                ),
                axes_path=(
                    input_files_dir
                    / "axes_forward_by_operating_points"
                    / "operating_points_v1.tsv"
                ),
                performance_curve_path=(
                    input_files_dir
                    / "im_performance_curve"
                    / "currentdependent03_50Hz_115V.tsv"
                ),
            ),
        ),
    )


def _flat_real(value: object) -> np.ndarray:
    """値を実数 1 次元 ``float64`` 配列にする。"""
    return np.asarray(np.real(np.asarray(value)), dtype=np.float64).reshape(-1)


def _power_factor(complex_power: object) -> np.ndarray:
    """複素電力から力率 ``Re(S) / |S|`` を 1 次元配列で返す。"""
    power = np.asarray(complex_power, dtype=np.complex128).reshape(-1)
    magnitude = np.abs(power)
    valid = (
        np.isfinite(power.real) & np.isfinite(power.imag) & (magnitude > 0.0)
    )
    power_factor = np.zeros(power.shape, dtype=np.float64)
    power_factor[valid] = power.real[valid] / magnitude[valid]
    return power_factor


def _assert_finite_series(label: str, values: np.ndarray) -> None:
    """系列が有限値のみを持つことを確認する。"""
    assert np.all(np.isfinite(values)), f"{label} に非有限値が含まれています"


def _assert_operating_points_output_regression(output: OutputDto) -> None:
    """OperatingPoints 出力 DTO の形状・主要系列の代表値を固定する。"""
    layout = output.array_layout
    assert layout.reference_axes == [ArrayKey.SLIP]
    assert (
        layout.get_reference_total_length() == _EXPECTED_OPERATING_POINT_COUNT
    )

    for axis in (
        ArrayKey.SLIP,
        ArrayKey.INPUT_LINE_VOLTAGE,
        ArrayKey.FREQUENCY,
    ):
        assert axis in layout.arrays
        axis_values = _flat_real(layout.arrays[axis].to_base_unit().get_value())
        assert axis_values.size == _EXPECTED_OPERATING_POINT_COUNT
        _assert_finite_series(axis.name, axis_values)

    result = output.result
    output_power_w = _flat_real(result.output_power.to_base_unit().get_value())
    input_current_a = np.abs(
        np.asarray(
            result.input_line_current.to_base_unit().get_value(),
            dtype=np.complex128,
        ).reshape(-1)
    )
    efficiency = _flat_real(result.system_efficiency.to_base_unit().get_value())
    torque_nm = _flat_real(result.torque.to_base_unit().get_value())
    speed_rpm = _flat_real(
        result.rotational_speed.convert_to_unit("rpm").get_value()
    )
    power_factor = _power_factor(
        result.cable_input_phase_power.to_base_unit().get_value()
    )

    series_checks: tuple[tuple[str, np.ndarray], ...] = (
        ("output_power_w", output_power_w),
        ("input_current_a", input_current_a),
        ("efficiency", efficiency),
        ("torque_nm", torque_nm),
        ("speed_rpm", speed_rpm),
        ("power_factor", power_factor),
    )
    for label, values in series_checks:
        assert values.size == _EXPECTED_OPERATING_POINT_COUNT
        _assert_finite_series(label=label, values=values)

    golden_checks: tuple[tuple[str, float, float], ...] = (
        (
            "max_output_power_w",
            float(np.nanmax(output_power_w)),
            _EXPECTED_MAX_OUTPUT_POWER_W,
        ),
        (
            "max_input_current_a",
            float(np.nanmax(input_current_a)),
            _EXPECTED_MAX_INPUT_CURRENT_A,
        ),
        (
            "max_efficiency",
            float(np.nanmax(efficiency)),
            _EXPECTED_MAX_EFFICIENCY,
        ),
        ("max_torque_nm", float(np.nanmax(torque_nm)), _EXPECTED_MAX_TORQUE_NM),
        ("min_speed_rpm", float(np.nanmin(speed_rpm)), _EXPECTED_MIN_SPEED_RPM),
        ("max_speed_rpm", float(np.nanmax(speed_rpm)), _EXPECTED_MAX_SPEED_RPM),
        (
            "max_power_factor",
            float(np.nanmax(power_factor)),
            _EXPECTED_MAX_POWER_FACTOR,
        ),
    )
    for label, actual_value, expected_value in golden_checks:
        assert np.isclose(
            actual_value,
            expected_value,
            rtol=_SIMULATED_SERIES_GOLDEN_RTOL,
            atol=0.0,
        ), (
            f"{label} がゴールデン値からずれています: "
            f"actual={actual_value}, expected={expected_value}"
        )


@pytest.mark.integration
def test_operating_points_runs_through_output(
    all_stage_operating_points_config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """CurrentDependent03 を ``ForwardByOperatingPointsPipeline`` で通せるか確認する。

    出力件数がジョブ数と保たれ、各 OutputDto が result を持ち、形状・主要
    系列の代表値が固定ゴールデン値と一致するかを検証する。
    """
    job_specs = _make_job_specs(input_files_dir)
    pipeline = ForwardByOperatingPointsPipeline.create(
        config=all_stage_operating_points_config,
        logger=logger,
    )
    output_dtos = pipeline.run(input=job_specs)
    assert len(output_dtos.get_all()) == len(job_specs.specs)
    for output in output_dtos.get_all():
        assert isinstance(output, OutputDto)
        assert output.result is not None
        _assert_operating_points_output_regression(output)
