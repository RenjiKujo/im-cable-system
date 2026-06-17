"""supply_grid シミュレーション系列の派生と (f, V) スライス。

``OutputDto.result`` の生量から描画用の派生系列（Pout / |I_line| / PF / η /
トルク / 回転数）を作り、供給条件 (f, V) ごとに slip 軸へスライスする。
slip 横軸・出力比横軸の双方のビルダーが共有する。描画やレイアウトには
関与しない。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid._unit_helpers import (  # noqa: E501
    _as_real_array,
    _to_base_value_array,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto

_REQUIRED_AXES = (
    ArrayKey.SLIP,
    ArrayKey.FREQUENCY,
    ArrayKey.INPUT_LINE_VOLTAGE,
)


@dataclass(frozen=True)
class _SupplyGridSeries:
    """supply_grid 図の描画に使う派生系列。"""

    output_power_w: np.ndarray
    input_current_magnitude_a: np.ndarray
    power_factor: np.ndarray
    efficiency: np.ndarray
    torque_nm: np.ndarray
    rotational_speed_rpm: np.ndarray


@dataclass(frozen=True)
class _SupplySlice:
    """1つの (f, V) 条件に対応する slip 軸サブプロット用データ。"""

    frequency_hz: float
    voltage_v: float
    slip: np.ndarray
    series: _SupplyGridSeries


def _has_required_axes(output_dto: OutputDto) -> bool:
    """supply_grid 図に必要な参照軸が揃っているかを返す。"""
    layout = output_dto.array_layout
    return all(
        axis in layout.reference_axes for axis in _REQUIRED_AXES
    ) and all(axis in layout.axes for axis in _REQUIRED_AXES)


def _axis_values(output_dto: OutputDto, axis: ArrayKey) -> np.ndarray:
    """array_layout から参照軸の基準単位値を返す。"""
    return _as_real_array(
        _to_base_value_array(output_dto.array_layout.arrays[axis])
    )


def _power_factor_from_complex_power(complex_power: np.ndarray) -> np.ndarray:
    """複素電力から力率 ``Re(S) / |S|`` を算出する。"""
    power = np.asarray(complex_power, dtype=np.complex128)
    magnitude = np.abs(power)
    finite = np.isfinite(power.real) & np.isfinite(power.imag)
    valid = finite & (magnitude > 0.0)
    power_factor = np.zeros(power.shape, dtype=np.float64)
    power_factor[valid] = power.real[valid] / magnitude[valid]
    return power_factor


def _derive_series(output_dto: OutputDto) -> _SupplyGridSeries:
    """OutputDto.result から図の生量系列を派生する。"""
    result = output_dto.result
    output_power_w = np.real(
        np.asarray(
            result.output_power.to_base_unit().get_value(),
            dtype=np.complex128,
        )
    )
    cable_input_power = (
        result.cable_input_phase_power.to_base_unit().get_value()
    )
    line_current = result.input_line_current.to_base_unit().get_value()
    efficiency = result.system_efficiency.to_base_unit().get_value()
    torque = result.torque.to_base_unit().get_value()
    rotational_speed = result.rotational_speed.convert_to_unit(
        "rpm"
    ).get_value()
    return _SupplyGridSeries(
        output_power_w=np.asarray(output_power_w, dtype=np.float64),
        input_current_magnitude_a=np.abs(
            np.asarray(line_current, dtype=np.complex128)
        ),
        power_factor=_power_factor_from_complex_power(cable_input_power),
        efficiency=np.asarray(efficiency, dtype=np.float64),
        torque_nm=np.real(np.asarray(torque, dtype=np.float64)),
        rotational_speed_rpm=np.real(
            np.asarray(rotational_speed, dtype=np.float64)
        ),
    )


def _take_axis(array: np.ndarray, axis: int, index: int) -> np.ndarray:
    """指定軸を1点に固定して配列を返す。"""
    return np.take(array, indices=index, axis=axis)


def _slice_to_slip_axis(
    array: np.ndarray,
    reference_axes: list[ArrayKey],
    *,
    frequency_index: int,
    voltage_index: int,
) -> np.ndarray:
    """参照軸配列から (f, V) を固定した slip 系列を返す。"""
    sliced = np.asarray(array)
    axes = list(reference_axes)
    for target_axis, target_index in (
        (ArrayKey.FREQUENCY, frequency_index),
        (ArrayKey.INPUT_LINE_VOLTAGE, voltage_index),
    ):
        axis_index = axes.index(target_axis)
        sliced = _take_axis(sliced, axis_index, target_index)
        axes.pop(axis_index)
    if ArrayKey.SLIP not in axes:
        return np.asarray(sliced, dtype=np.float64).reshape(-1)
    slip_axis_index = axes.index(ArrayKey.SLIP)
    moved = np.moveaxis(sliced, slip_axis_index, 0)
    return np.asarray(moved, dtype=np.float64).reshape(moved.shape[0], -1)[:, 0]


def _slice_series(
    series: _SupplyGridSeries,
    reference_axes: list[ArrayKey],
    *,
    frequency_index: int,
    voltage_index: int,
) -> _SupplyGridSeries:
    """全量系列を (f, V) 固定の slip 系列へスライスする。"""

    def _slice(array: np.ndarray) -> np.ndarray:
        return _slice_to_slip_axis(
            array,
            reference_axes,
            frequency_index=frequency_index,
            voltage_index=voltage_index,
        )

    return _SupplyGridSeries(
        output_power_w=_slice(series.output_power_w),
        input_current_magnitude_a=_slice(series.input_current_magnitude_a),
        power_factor=_slice(series.power_factor),
        efficiency=_slice(series.efficiency),
        torque_nm=_slice(series.torque_nm),
        rotational_speed_rpm=_slice(series.rotational_speed_rpm),
    )


def _build_simulated_slices(output_dto: OutputDto) -> list[_SupplySlice]:
    """OutputDto から (f, V) ごとの slip 軸シミュレーション系列を作る。"""
    layout = output_dto.array_layout
    reference_axes = list(layout.reference_axes)
    frequency_axis = _axis_values(output_dto, ArrayKey.FREQUENCY)
    voltage_axis = _axis_values(output_dto, ArrayKey.INPUT_LINE_VOLTAGE)
    slip_axis = _axis_values(output_dto, ArrayKey.SLIP)
    series = _derive_series(output_dto)
    slices: list[_SupplySlice] = []
    for frequency_index, frequency_hz in enumerate(frequency_axis):
        for voltage_index, voltage_v in enumerate(voltage_axis):
            slices.append(
                _SupplySlice(
                    frequency_hz=float(np.real(frequency_hz)),
                    voltage_v=float(np.real(voltage_v)),
                    slip=slip_axis.copy(),
                    series=_slice_series(
                        series,
                        reference_axes,
                        frequency_index=frequency_index,
                        voltage_index=voltage_index,
                    ),
                )
            )
    return slices
