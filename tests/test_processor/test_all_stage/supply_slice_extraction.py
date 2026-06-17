"""all_stage 結合テスト用の supply_grid スライス抽出ヘルパ。

``OutputDto`` の公開 API（``array_layout`` / ``result`` / ``im_pc_catalogs``）
だけを使い、供給条件 (f, V) ごとの slip 軸シミュレーション系列とカタログ系列を
**独立に** 再構築する。algorithm 層（make_figure/supply_grid）の内部実装に依存
させないことで、描画実装の変更が processor 結合テストを壊さないようにする。

本モジュールは processor 結合テスト専用のため ``tests`` 配下に閉じる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto

_REQUIRED_AXES: tuple[ArrayKey, ...] = (
    ArrayKey.SLIP,
    ArrayKey.FREQUENCY,
    ArrayKey.INPUT_LINE_VOLTAGE,
)
_SUPPLY_KEY_RTOL = 1.0e-6
_SUPPLY_KEY_ATOL = 1.0e-6


@dataclass(frozen=True)
class SupplySeries:
    """1 つの (f, V) 条件に対応する slip 軸系列。"""

    output_power_w: np.ndarray
    input_current_magnitude_a: np.ndarray
    power_factor: np.ndarray
    efficiency: np.ndarray
    torque_nm: np.ndarray
    rotational_speed_rpm: np.ndarray


@dataclass(frozen=True)
class SupplySlice:
    """供給条件 (f, V) を固定したシミュレーション slip スライス。"""

    frequency_hz: float
    voltage_v: float
    slip: np.ndarray
    series: SupplySeries


@dataclass(frozen=True)
class CatalogSlice:
    """1 つのカタログ性能曲線を slip 軸へ正規化したスライス。"""

    frequency_hz: float
    voltage_v: float
    slip: np.ndarray
    series: SupplySeries


def _real_array(values: object) -> np.ndarray:
    """単位 DTO 値を実数 1 次元/多次元 ``float64`` 配列にする。"""
    return np.asarray(np.real(np.asarray(values)), dtype=np.float64)


def _base_array(dto: object) -> np.ndarray:
    """単位付き DTO を基準単位に変換した実数配列で返す。"""
    base = dto.to_base_unit()  # type: ignore[attr-defined]
    return _real_array(base.get_value())


def _base_scalar(dto: object) -> float:
    """スカラ単位 DTO を基準単位の float で返す。"""
    return float(_base_array(dto).reshape(-1)[0])


def _axis_base_values(output: OutputDto, axis: ArrayKey) -> np.ndarray:
    """array_layout の参照軸を基準単位の 1 次元配列で返す。"""
    return _base_array(output.array_layout.arrays[axis]).reshape(-1)


def _power_factor_from_complex(complex_power: object) -> np.ndarray:
    """複素電力から力率 ``Re(S) / |S|`` を返す。"""
    power = np.asarray(complex_power, dtype=np.complex128)
    magnitude = np.abs(power)
    valid = (
        np.isfinite(power.real) & np.isfinite(power.imag) & (magnitude > 0.0)
    )
    power_factor = np.zeros(power.shape, dtype=np.float64)
    power_factor[valid] = power.real[valid] / magnitude[valid]
    return power_factor


def _derive_grid_series(
    output: OutputDto,
    grid_shape: tuple[int, ...],
) -> SupplySeries:
    """OutputDto.result から参照格子形状の派生系列を作る。"""
    result = output.result
    output_power = _real_array(
        result.output_power.to_base_unit().get_value()
    ).reshape(grid_shape)
    line_current = np.asarray(
        result.input_line_current.to_base_unit().get_value(),
        dtype=np.complex128,
    )
    input_current = np.abs(line_current).reshape(grid_shape)
    power_factor = _power_factor_from_complex(
        result.cable_input_phase_power.to_base_unit().get_value()
    ).reshape(grid_shape)
    efficiency = _real_array(
        result.system_efficiency.to_base_unit().get_value()
    ).reshape(grid_shape)
    torque = _real_array(result.torque.to_base_unit().get_value()).reshape(
        grid_shape
    )
    rotational_speed = _real_array(
        result.rotational_speed.convert_to_unit("rpm").get_value()
    ).reshape(grid_shape)
    return SupplySeries(
        output_power_w=output_power,
        input_current_magnitude_a=input_current,
        power_factor=power_factor,
        efficiency=efficiency,
        torque_nm=torque,
        rotational_speed_rpm=rotational_speed,
    )


def _slice_to_slip(
    array: np.ndarray,
    reference_axes: list[ArrayKey],
    *,
    frequency_index: int,
    voltage_index: int,
) -> np.ndarray:
    """参照格子配列から (f, V) を固定した slip 系列を返す。"""
    selector: list[object] = [slice(None)] * len(reference_axes)
    selector[reference_axes.index(ArrayKey.FREQUENCY)] = frequency_index
    selector[reference_axes.index(ArrayKey.INPUT_LINE_VOLTAGE)] = voltage_index
    sliced = array[cast(Any, tuple(selector))]
    return np.asarray(sliced, dtype=np.float64).reshape(-1)


def _slice_series(
    series: SupplySeries,
    reference_axes: list[ArrayKey],
    *,
    frequency_index: int,
    voltage_index: int,
) -> SupplySeries:
    """格子系列を (f, V) 固定の slip 系列へスライスする。"""

    def _take(array: np.ndarray) -> np.ndarray:
        return _slice_to_slip(
            array,
            reference_axes,
            frequency_index=frequency_index,
            voltage_index=voltage_index,
        )

    return SupplySeries(
        output_power_w=_take(series.output_power_w),
        input_current_magnitude_a=_take(series.input_current_magnitude_a),
        power_factor=_take(series.power_factor),
        efficiency=_take(series.efficiency),
        torque_nm=_take(series.torque_nm),
        rotational_speed_rpm=_take(series.rotational_speed_rpm),
    )


def build_simulated_supply_slices(output: OutputDto) -> list[SupplySlice]:
    """OutputDto から (f, V) ごとの slip 軸シミュレーション系列を作る。"""
    layout = output.array_layout
    reference_axes = list(layout.reference_axes)
    if any(axis not in reference_axes for axis in _REQUIRED_AXES):
        return []
    frequency_axis = _axis_base_values(output, ArrayKey.FREQUENCY)
    voltage_axis = _axis_base_values(output, ArrayKey.INPUT_LINE_VOLTAGE)
    slip_axis = _axis_base_values(output, ArrayKey.SLIP)
    grid_shape = tuple(
        _axis_base_values(output, axis).size for axis in reference_axes
    )
    series = _derive_grid_series(output, grid_shape)

    slices: list[SupplySlice] = []
    for frequency_index, frequency_hz in enumerate(frequency_axis):
        for voltage_index, voltage_v in enumerate(voltage_axis):
            slices.append(
                SupplySlice(
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


def _catalog_has_required_series(catalog: object) -> bool:
    """supply_grid 比較に必要なカタログ系列が揃っているか返す。"""
    return all(
        getattr(catalog, name, None) is not None
        for name in (
            "power_series",
            "current_series",
            "power_factor_series",
            "efficiency_series",
        )
    )


def _optional_base_array(dto: object, *, length: int) -> np.ndarray:
    """optional 系列を基準単位配列で返す。無い場合は NaN 配列。"""
    if dto is None:
        return np.full(length, np.nan, dtype=np.float64)
    return _base_array(dto).reshape(-1)


def _catalog_slice(catalog: object) -> CatalogSlice:
    """カタログ DTO 1 件を slip 軸スライスへ正規化する。"""
    slip = _base_array(catalog.slip_series).reshape(-1)  # type: ignore[attr-defined]
    length = int(slip.size)
    return CatalogSlice(
        frequency_hz=_base_scalar(catalog.supply_frequency),  # type: ignore[attr-defined]
        voltage_v=_base_scalar(catalog.supply_voltage),  # type: ignore[attr-defined]
        slip=slip,
        series=SupplySeries(
            output_power_w=_base_array(catalog.power_series).reshape(-1),  # type: ignore[attr-defined]
            input_current_magnitude_a=_base_array(
                catalog.current_series  # type: ignore[attr-defined]
            ).reshape(-1),
            power_factor=_base_array(catalog.power_factor_series).reshape(-1),  # type: ignore[attr-defined]
            efficiency=_base_array(catalog.efficiency_series).reshape(-1),  # type: ignore[attr-defined]
            torque_nm=_optional_base_array(
                getattr(catalog, "torque_series", None), length=length
            ),
            rotational_speed_rpm=_optional_base_array(
                getattr(catalog, "rotational_speed_series", None),
                length=length,
            ),
        ),
    )


def build_catalog_supply_slices(output: OutputDto) -> list[CatalogSlice]:
    """OutputDto のカタログから比較可能な slip 軸スライスを作る。"""
    slices: list[CatalogSlice] = []
    for catalog in output.im_pc_catalogs.get_all():
        if _catalog_has_required_series(catalog):
            slices.append(_catalog_slice(catalog))
    return slices


def find_matching_simulated_slip_slice(
    output: OutputDto,
) -> tuple[SupplySlice, CatalogSlice]:
    """catalog と同じ供給条件の simulated slip スライスを返す。"""
    catalog_slices = build_catalog_supply_slices(output)
    assert len(catalog_slices) == 1, (
        "比較対象のカタログスライスが 1 件ではありません: "
        f"{len(catalog_slices)}"
    )
    catalog = catalog_slices[0]

    for simulated in build_simulated_supply_slices(output):
        if np.isclose(
            simulated.frequency_hz,
            catalog.frequency_hz,
            rtol=_SUPPLY_KEY_RTOL,
            atol=_SUPPLY_KEY_ATOL,
        ) and np.isclose(
            simulated.voltage_v,
            catalog.voltage_v,
            rtol=_SUPPLY_KEY_RTOL,
            atol=_SUPPLY_KEY_ATOL,
        ):
            return simulated, catalog
    raise AssertionError(
        "catalog と同じ供給条件の simulated slip スライスが見つかりません: "
        f"f={catalog.frequency_hz}, V={catalog.voltage_v}"
    )


def matching_slip_indices(
    simulated: SupplySlice,
    catalog: CatalogSlice,
) -> np.ndarray:
    """catalog slip と同じ値を持つ simulated 側 index を返す。"""
    simulated_slip = np.asarray(simulated.slip, dtype=np.float64)
    catalog_slip = np.asarray(catalog.slip, dtype=np.float64)

    indices: list[int] = []
    for slip_value in catalog_slip:
        matches = np.where(
            np.isclose(
                simulated_slip,
                slip_value,
                rtol=1.0e-10,
                atol=1.0e-12,
            )
        )[0]
        if len(matches) != 1:
            raise AssertionError(
                "catalog slip と一致する simulated slip が一意に決まりません: "
                f"slip={slip_value}, matches={matches.tolist()}"
            )
        indices.append(int(matches[0]))
    return np.asarray(indices, dtype=np.int64)


def normalized_max_abs_error(
    simulated: np.ndarray,
    catalog: np.ndarray,
) -> float:
    """系列ごとに正規化した最大絶対誤差を返す。"""
    scale = max(float(np.nanmax(np.abs(catalog))), 1.0e-12)
    return float(np.nanmax(np.abs(simulated - catalog) / scale))
