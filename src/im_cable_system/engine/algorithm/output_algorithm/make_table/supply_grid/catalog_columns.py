"""supply_grid 表へ重ねるカタログ参照列の抽出とマッチング。

``OutputDto.im_pc_catalogs``（供給条件ごとの slip 軸性能カーブ）を、make_table
が組む long 形式表の各行 ``(voltage_v, frequency_hz, slip)`` と突き合わせ、
一致する行へカタログ実測値を埋めた列群を返す。一致しない行・未観測点
（mask=False）・カタログに無い系列は NaN とする。

本モジュールは make_table/supply_grid の内部実装であり、層外向け窓口ではない。
``make_figure.supply_grid`` の catalog 正規化とは責務ツリーが異なるため共有せず、
表に必要な最小限の取り出しのみを持つ。
"""

from __future__ import annotations

from typing import Protocol, cast

import numpy as np

from im_cable_system.engine.shared.dto.output import OutputDto

# 供給条件 (f, V) のマッチ許容（make_figure 側の supply key と整合させる）。
_SUPPLY_KEY_RTOL = 1.0e-6
_SUPPLY_KEY_ATOL = 1.0e-6
# slip のマッチ許容（catalog slip と simulated slip の同一視）。
_SLIP_RTOL = 1.0e-10
_SLIP_ATOL = 1.0e-12

# 値の取り出し方法（単位変換）の種別。
_KIND_BASE = "base"
_KIND_RATIO = "ratio"
_KIND_RPM = "rpm"


class _UnitDtoLike(Protocol):
    """カタログ系列の単位付き DTO が満たす最小契約。"""

    def get_value(self) -> object:
        """値を返す。"""
        ...

    def get_unit(self) -> str:
        """単位文字列を返す。"""
        ...

    def to_base_unit(self) -> _UnitDtoLike:
        """基準単位へ変換した DTO を返す。"""
        ...

    def convert_to_unit(self, target_unit: str) -> _UnitDtoLike:
        """指定単位へ変換した DTO を返す。"""
        ...


class _CatalogLike(Protocol):
    """性能カーブカタログのうち、表に重ねる際に使う最小契約。"""

    supply_frequency: _UnitDtoLike
    supply_voltage: _UnitDtoLike
    slip_series: _UnitDtoLike
    rotational_speed_series: _UnitDtoLike | None
    power_series: _UnitDtoLike | None
    power_series_mask: np.ndarray | None
    current_series: _UnitDtoLike | None
    current_series_mask: np.ndarray | None
    power_factor_series: _UnitDtoLike | None
    power_factor_series_mask: np.ndarray | None
    efficiency_series: _UnitDtoLike | None
    efficiency_series_mask: np.ndarray | None
    torque_series: _UnitDtoLike | None
    torque_series_mask: np.ndarray | None


# (列名, 系列属性名, mask 属性名, 取り出し種別)。simulated 列と揃えた列名に
# ``catalog_`` を付けて重ねる。mask を持たない rotational_speed は mask=None。
_CATALOG_SERIES_SPECS: tuple[tuple[str, str, str | None, str], ...] = (
    ("catalog_output_power_w", "power_series", "power_series_mask", _KIND_BASE),
    (
        "catalog_input_current_magnitude_a",
        "current_series",
        "current_series_mask",
        _KIND_BASE,
    ),
    (
        "catalog_power_factor",
        "power_factor_series",
        "power_factor_series_mask",
        _KIND_RATIO,
    ),
    (
        "catalog_efficiency",
        "efficiency_series",
        "efficiency_series_mask",
        _KIND_RATIO,
    ),
    ("catalog_torque_nm", "torque_series", "torque_series_mask", _KIND_BASE),
    (
        "catalog_rotational_speed_rpm",
        "rotational_speed_series",
        None,
        _KIND_RPM,
    ),
)


def build_catalog_columns(
    output_dto: OutputDto,
    *,
    voltage_v: np.ndarray,
    frequency_hz: np.ndarray,
    slip: np.ndarray,
) -> dict[str, np.ndarray]:
    """表の各行に対応するカタログ参照列を返す。

    行は ``(voltage_v, frequency_hz, slip)`` で識別し、供給条件と slip が一致する
    カタログ点の値を埋める。一致行が無い・未観測点・対象系列が欠落の場合は NaN。
    カタログにその系列が 1 件も無い列は返り値に含めない（全 NaN 列を作らない）。

    Args:
        output_dto: 出力データ DTO（``im_pc_catalogs`` を参照する）。
        voltage_v: 各行の供給線間電圧 [V]（表本体と同じ並び・長さ）。
        frequency_hz: 各行の供給周波数 [Hz]（同上）。
        slip: 各行の slip [-]（同上）。

    Returns:
        dict[str, np.ndarray]: ``catalog_`` 接頭の列名 → 行数ぶんの値配列。
            重ねるカタログが無い場合は空 dict。
    """
    n_rows = int(slip.size)
    columns = {
        name: np.full(n_rows, np.nan, dtype=np.float64)
        for name, *_ in _CATALOG_SERIES_SPECS
    }
    present: set[str] = set()
    for raw_catalog in output_dto.im_pc_catalogs.get_all():
        _fill_from_catalog(
            cast(_CatalogLike, raw_catalog),
            columns,
            present,
            voltage_v=voltage_v,
            frequency_hz=frequency_hz,
            slip=slip,
        )
    return {
        name: columns[name]
        for name, *_ in _CATALOG_SERIES_SPECS
        if name in present
    }


def _fill_from_catalog(
    catalog: _CatalogLike,
    columns: dict[str, np.ndarray],
    present: set[str],
    *,
    voltage_v: np.ndarray,
    frequency_hz: np.ndarray,
    slip: np.ndarray,
) -> None:
    """1件のカタログを対応行へ埋め、出現した列名を ``present`` に記録する。"""
    supply_match = _supply_match(
        voltage_v=voltage_v,
        frequency_hz=frequency_hz,
        catalog_voltage=_scalar_base_value(catalog.supply_voltage),
        catalog_frequency=_scalar_base_value(catalog.supply_frequency),
    )
    if not bool(supply_match.any()):
        return
    catalog_slip = _value_array(catalog.slip_series, _KIND_RATIO)
    for column_name, series_attr, mask_attr, kind in _CATALOG_SERIES_SPECS:
        series = getattr(catalog, series_attr, None)
        if series is None:
            continue
        present.add(column_name)
        valid = _series_mask(catalog, mask_attr, length=int(catalog_slip.size))
        _assign_matched(
            columns[column_name],
            supply_match=supply_match,
            row_slip=slip,
            catalog_slip=catalog_slip,
            values=_value_array(cast(_UnitDtoLike, series), kind),
            valid=valid,
        )


def _assign_matched(
    column: np.ndarray,
    *,
    supply_match: np.ndarray,
    row_slip: np.ndarray,
    catalog_slip: np.ndarray,
    values: np.ndarray,
    valid: np.ndarray,
) -> None:
    """観測済みカタログ点を slip 一致行へ代入する。"""
    for index in range(int(catalog_slip.size)):
        if not bool(valid[index]):
            continue
        row_match = supply_match & np.isclose(
            row_slip,
            catalog_slip[index],
            rtol=_SLIP_RTOL,
            atol=_SLIP_ATOL,
        )
        column[row_match] = values[index]


def _supply_match(
    *,
    voltage_v: np.ndarray,
    frequency_hz: np.ndarray,
    catalog_voltage: float,
    catalog_frequency: float,
) -> np.ndarray:
    """供給条件 (f, V) が一致する行の bool マスクを返す。"""
    return np.isclose(
        voltage_v,
        catalog_voltage,
        rtol=_SUPPLY_KEY_RTOL,
        atol=_SUPPLY_KEY_ATOL,
    ) & np.isclose(
        frequency_hz,
        catalog_frequency,
        rtol=_SUPPLY_KEY_RTOL,
        atol=_SUPPLY_KEY_ATOL,
    )


def _series_mask(
    catalog: _CatalogLike,
    mask_attr: str | None,
    *,
    length: int,
) -> np.ndarray:
    """系列の有効点 mask を返す。mask を持たない系列は全 True とする。"""
    if mask_attr is None:
        return np.ones(length, dtype=bool)
    mask = getattr(catalog, mask_attr, None)
    if mask is None:
        return np.ones(length, dtype=bool)
    return np.asarray(mask, dtype=bool).reshape(-1)


def _value_array(dto: _UnitDtoLike, kind: str) -> np.ndarray:
    """単位付き系列 DTO を実数 1 次元 ``float64`` 配列にする。"""
    if kind == _KIND_RATIO:
        values = np.asarray(dto.get_value(), dtype=np.float64).reshape(-1)
        return values / 100.0 if dto.get_unit() == "%" else values
    if kind == _KIND_RPM:
        return np.asarray(
            np.real(np.asarray(dto.convert_to_unit("rpm").get_value())),
            dtype=np.float64,
        ).reshape(-1)
    return np.asarray(
        np.real(np.asarray(dto.to_base_unit().get_value())),
        dtype=np.float64,
    ).reshape(-1)


def _scalar_base_value(dto: _UnitDtoLike) -> float:
    """スカラー DTO を基準単位の実数 float として返す。"""
    value = np.asarray(dto.to_base_unit().get_value()).reshape(-1)[0]
    return float(np.real(value))
