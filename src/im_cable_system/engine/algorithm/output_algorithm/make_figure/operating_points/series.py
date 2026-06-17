"""operating_points 図の運転点系列を ``OutputDto`` から派生する。

``reference_axes = [SLIP]`` の co-indexed なレイアウトを前提に、運転点
（リスト番号）ごとの特性量（回転数 / 電流 / 電圧 / 周波数 / 出力 / トルク /
効率 / 力率）を 1 次元配列へ平坦化する。描画やレイアウトには関与しない。
``OutputDto.result`` の生量から PF / |I_line| を派生計算する。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto


@dataclass(frozen=True)
class _OperatingPointSeries:
    """運転点（index）ごとの描画用派生系列（すべて長さ N の 1 次元配列）。

    Attributes:
        rotational_speed_rpm: 回転数 [rpm]。
        input_current_magnitude_a: ケーブル入力線電流の大きさ |I_line| [A]。
        voltage_v: 供給線間電圧 [V]。``None`` の場合は軸に存在しない。
        frequency_hz: 供給周波数 [Hz]。``None`` の場合は軸に存在しない。
        output_power_w: IM 出力電力の実部 Pout [W]。
        torque_nm: IM トルク [N·m]。
        efficiency: システム効率 [-]。
        power_factor: 力率 [-]（``Re(S) / |S|``）。
    """

    rotational_speed_rpm: np.ndarray
    input_current_magnitude_a: np.ndarray
    voltage_v: np.ndarray | None
    frequency_hz: np.ndarray | None
    output_power_w: np.ndarray
    torque_nm: np.ndarray
    efficiency: np.ndarray
    power_factor: np.ndarray


def _real_flat(value: object) -> np.ndarray:
    """単位 DTO 値を実数 1 次元 ``float64`` 配列にする。"""
    return np.asarray(np.real(np.asarray(value)), dtype=np.float64).reshape(-1)


def _power_factor_from_complex_power(complex_power: object) -> np.ndarray:
    """複素電力から力率 ``Re(S) / |S|`` を 1 次元配列で返す。"""
    power = np.asarray(complex_power, dtype=np.complex128).reshape(-1)
    magnitude = np.abs(power)
    finite = np.isfinite(power.real) & np.isfinite(power.imag)
    valid = finite & (magnitude > 0.0)
    power_factor = np.zeros(power.shape, dtype=np.float64)
    power_factor[valid] = power.real[valid] / magnitude[valid]
    return power_factor


def _axis_values_or_none(
    output_dto: OutputDto,
    axis: ArrayKey,
) -> np.ndarray | None:
    """array_layout に軸があれば基準単位の 1 次元配列を、なければ ``None`` を返す。"""
    arrays = output_dto.array_layout.arrays
    if axis not in arrays:
        return None
    return _real_flat(arrays[axis].to_base_unit().get_value())


def _operating_point_count(output_dto: OutputDto) -> int:
    """運転点（参照軸直積）の総数を返す。"""
    return output_dto.array_layout.get_reference_total_length()


def _derive_series(output_dto: OutputDto) -> _OperatingPointSeries:
    """OutputDto から運転点ごとの派生系列を作る。"""
    result = output_dto.result
    return _OperatingPointSeries(
        rotational_speed_rpm=_real_flat(
            result.rotational_speed.convert_to_unit("rpm").get_value()
        ),
        input_current_magnitude_a=np.abs(
            np.asarray(
                result.input_line_current.to_base_unit().get_value(),
                dtype=np.complex128,
            ).reshape(-1)
        ),
        voltage_v=_axis_values_or_none(output_dto, ArrayKey.INPUT_LINE_VOLTAGE),
        frequency_hz=_axis_values_or_none(output_dto, ArrayKey.FREQUENCY),
        output_power_w=_real_flat(
            result.output_power.to_base_unit().get_value()
        ),
        torque_nm=_real_flat(result.torque.to_base_unit().get_value()),
        efficiency=_real_flat(
            result.system_efficiency.to_base_unit().get_value()
        ),
        power_factor=_power_factor_from_complex_power(
            result.cable_input_phase_power.to_base_unit().get_value()
        ),
    )
