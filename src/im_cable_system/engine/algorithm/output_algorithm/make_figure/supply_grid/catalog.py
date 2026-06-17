"""supply_grid 参照カタログの描画用正規化と供給条件マッチ。

``OutputDto.im_pc_catalogs`` の性能カーブカタログを、シミュレーション系列と
同じ :class:`_SupplyGridSeries` 形式へ正規化し、供給条件 (f, V) でシミュレーション
スライスと突き合わせる。slip 横軸・出力比横軸の双方のビルダーが共有する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid._unit_helpers import (  # noqa: E501
    _ratio_to_base_unit,
    _scalar_base_value,
    _to_base_value_array,
    _to_unit_value_array,
    _UnitValueLike,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501
    _SupplyGridSeries,
    _SupplySlice,
)
from im_cable_system.engine.shared.dto.output import OutputDto

_SUPPLY_KEY_RTOL = 1.0e-6
_SUPPLY_KEY_ATOL = 1.0e-6


class _CatalogLike(Protocol):
    """性能カーブカタログのうち、supply_grid 図が使う最小契約。"""

    supply_frequency: _UnitValueLike
    supply_voltage: _UnitValueLike
    slip_series: _UnitValueLike
    rotational_speed_series: _UnitValueLike | None
    power_series: _UnitValueLike | None
    current_series: _UnitValueLike | None
    power_factor_series: _UnitValueLike | None
    efficiency_series: _UnitValueLike | None
    torque_series: _UnitValueLike | None


@dataclass(frozen=True)
class _CatalogSlice:
    """1つのカタログ性能曲線を描画用に正規化したデータ。"""

    frequency_hz: float
    voltage_v: float
    slip: np.ndarray
    series: _SupplyGridSeries


def _catalog_has_required_series(catalog: _CatalogLike) -> bool:
    """supply_grid 図に必要なカタログ系列が揃っているかを返す。"""
    return (
        getattr(catalog, "power_series", None) is not None
        and getattr(catalog, "current_series", None) is not None
        and getattr(catalog, "power_factor_series", None) is not None
        and getattr(catalog, "efficiency_series", None) is not None
    )


def _catalog_torque_nm(
    catalog: _CatalogLike,
    *,
    length: int,
) -> np.ndarray:
    """カタログのトルク系列を返す。無い場合は NaN 配列を返す。

    トルク系列は optional のため、欠落時は描画・凡例から除外できるよう
    全 NaN の配列で表現する。
    """
    torque_series = getattr(catalog, "torque_series", None)
    if torque_series is None:
        return np.full(length, np.nan, dtype=np.float64)
    return np.asarray(
        np.real(_to_base_value_array(cast(_UnitValueLike, torque_series))),
        dtype=np.float64,
    ).reshape(-1)


def _catalog_rotational_speed_rpm(
    catalog: _CatalogLike,
    *,
    length: int,
) -> np.ndarray:
    """カタログの回転数系列を rpm で返す。無い場合は NaN 配列を返す。"""
    rotational_speed_series = getattr(catalog, "rotational_speed_series", None)
    if rotational_speed_series is None:
        return np.full(length, np.nan, dtype=np.float64)
    return np.asarray(
        np.real(
            _to_unit_value_array(
                cast(_UnitValueLike, rotational_speed_series),
                target_unit="rpm",
            )
        ),
        dtype=np.float64,
    ).reshape(-1)


def _catalog_slice(catalog: _CatalogLike) -> _CatalogSlice:
    """カタログ DTO 1件を描画用データに変換する。"""
    power_series = cast(_UnitValueLike, catalog.power_series)
    current_series = cast(_UnitValueLike, catalog.current_series)
    power_factor_series = cast(_UnitValueLike, catalog.power_factor_series)
    efficiency_series = cast(_UnitValueLike, catalog.efficiency_series)
    slip = _ratio_to_base_unit(catalog.slip_series).reshape(-1)
    return _CatalogSlice(
        frequency_hz=_scalar_base_value(catalog.supply_frequency),
        voltage_v=_scalar_base_value(catalog.supply_voltage),
        slip=slip,
        series=_SupplyGridSeries(
            output_power_w=np.asarray(
                np.real(_to_base_value_array(power_series)),
                dtype=np.float64,
            ).reshape(-1),
            input_current_magnitude_a=np.asarray(
                np.real(_to_base_value_array(current_series)),
                dtype=np.float64,
            ).reshape(-1),
            power_factor=_ratio_to_base_unit(power_factor_series).reshape(-1),
            efficiency=_ratio_to_base_unit(efficiency_series).reshape(-1),
            torque_nm=_catalog_torque_nm(catalog, length=int(slip.size)),
            rotational_speed_rpm=_catalog_rotational_speed_rpm(
                catalog, length=int(slip.size)
            ),
        ),
    )


def _build_catalog_slices(output_dto: OutputDto) -> list[_CatalogSlice]:
    """OutputDto のカタログから描画可能な slip 軸系列を作る。"""
    catalog_slices: list[_CatalogSlice] = []
    for raw_catalog in output_dto.im_pc_catalogs.get_all():
        catalog = cast(_CatalogLike, raw_catalog)
        if _catalog_has_required_series(catalog):
            catalog_slices.append(_catalog_slice(catalog))
    return catalog_slices


def _supply_keys_close(
    left_frequency: float,
    left_voltage: float,
    right_frequency: float,
    right_voltage: float,
) -> bool:
    """(f, V) のキーが同一供給条件とみなせるかを返す。"""
    return bool(
        np.isclose(
            left_frequency,
            right_frequency,
            rtol=_SUPPLY_KEY_RTOL,
            atol=_SUPPLY_KEY_ATOL,
        )
        and np.isclose(
            left_voltage,
            right_voltage,
            rtol=_SUPPLY_KEY_RTOL,
            atol=_SUPPLY_KEY_ATOL,
        )
    )


def _match_catalog(
    simulated: _SupplySlice,
    catalogs: list[_CatalogSlice],
) -> _CatalogSlice | None:
    """シミュレーション系列と同じ (f, V) のカタログ系列を返す。"""
    for catalog in catalogs:
        if _supply_keys_close(
            simulated.frequency_hz,
            simulated.voltage_v,
            catalog.frequency_hz,
            catalog.voltage_v,
        ):
            return catalog
    return None
