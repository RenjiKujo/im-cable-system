"""参照軸直積グリッド上でのカタログ補間サンプリング（estimate_params 専用）。

カタログ系列 (|I|, P, PF, η) を参照軸直積の各点でスリップ補間し、目標配列を
作る共通ヘルパを提供する。目標／予測の組み立ては :mod:`curve_comparison_data`
が本モジュールを用いる（fit の残差ベクトルは :mod:`curve_residual_vector`）。

観測マスク (``*_series_mask``) の扱い:
    各従属系列 (|I|, P, PF, η) は同長の bool 配列 ``*_series_mask`` を伴う
    （``ImPerformanceCurveCatalogDto`` の契約）。``mask == False`` は未観測
    でプレースホルダ 0 が入っている点なので、**スリップ補間の元データから
    除外** する（:func:`_interpolate_masked`）。これにより未観測セルの 0 が
    補間値に混入して目標カーブを歪めることを防ぐ。マスク後の有効点が 2 点
    未満となる系列は、その格子点の目標値を NaN として下流の評価から外す。
    ``rotational_speed_series`` は独立軸で mask を持たないため従来どおり
    全点を補間に用いる。
"""

from __future__ import annotations

import math
from typing import cast

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImPerformanceCurveCatalogDto,
)
from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
)

_FREQ_ABS_TOL = 1e-4
_VOLT_ABS_TOL = 1.0


def _supply_keys_close(
    key_a: tuple[float, float],
    key_b: tuple[float, float],
) -> bool:
    """周波数・電圧（基準単位）が近似的に一致するか。"""
    return bool(
        math.isclose(key_a[0], key_b[0], rel_tol=0.0, abs_tol=_FREQ_ABS_TOL)
        and math.isclose(key_a[1], key_b[1], rel_tol=0.0, abs_tol=_VOLT_ABS_TOL)
    )


def _slip_fraction_from_axis(
    layout: ArrayLayoutDto, slip_key: ArrayKey, s_raw: float
) -> float:
    """レイアウト上のスリップスカラーを無次元分数 [-] に揃える。"""
    slip_dto = layout.arrays[slip_key]
    unit = slip_dto.get_unit()
    if unit == "-":
        return float(s_raw)
    if unit == "%":
        return float(s_raw) / 100.0
    raise ValueError(f"未対応のスリップ単位: {unit}")


def _slip_fraction_catalog(cat: ImPerformanceCurveCatalogDto) -> np.ndarray:
    """カタログ slip 系列を無次元分数に揃えたコピーを返す。"""
    arr = np.asarray(
        cat.slip_series.to_base_unit().get_value(),
        dtype=np.float64,
    )
    return arr.copy()


def _one_dimensional_series_base_values(dto: IArrayWithUnitDto) -> np.ndarray:
    """物理量配列 DTO を SI 基本単位に直した 1 次元 ``float64`` 配列で返す。"""
    return np.asarray(dto.to_base_unit().get_value(), dtype=np.float64)


def _interpolate_real(
    x_query: float,
    xp: np.ndarray,
    fp: np.ndarray,
) -> float:
    """xp が単調でなくてもソートして 1 次元補間する。"""
    order = np.argsort(xp)
    xs = xp[order]
    ys = fp[order]
    return float(np.interp(x_query, xs, ys, left=np.nan, right=np.nan))


def _series_mask_bool(mask: np.ndarray | None, length: int) -> np.ndarray:
    """系列マスクを長さ ``length`` の bool 配列へ正規化する。

    ``ImPerformanceCurveCatalogDto`` の契約では ``*_series is not None`` の
    とき ``*_series_mask`` は非 ``None`` だが、防御的に ``None`` を全点
    ``True``（＝全点観測）として扱う。

    Args:
        mask: カタログ系列の観測マスク。``None`` は全点観測とみなす。
        length: 系列長（``slip_series`` と同じ）。

    Returns:
        長さ ``length`` の bool 配列。
    """
    if mask is None:
        return np.ones(length, dtype=bool)
    return np.asarray(mask, dtype=bool)


def _interpolate_masked(
    x_query: float,
    xp: np.ndarray,
    fp: np.ndarray,
    series_mask: np.ndarray,
) -> float:
    """観測マスク ``True`` の点だけを用いてスリップ補間する。

    ``series_mask == False``（未観測のプレースホルダ点）を補間元 ``(xp, fp)``
    から除外してから :func:`_interpolate_real` で補間する。マスク後の有効点
    が 2 点未満の場合は補間できないため ``NaN`` を返す（下流で評価対象外と
    なる）。

    Args:
        x_query: 補間したいスリップ無次元分数 [-]。
        xp: カタログのスリップ無次元分数配列 [-]。
        fp: ``xp`` と同長のカタログ従属系列値（SI 基本単位）。
        series_mask: ``xp`` / ``fp`` と同長の観測マスク（bool）。

    Returns:
        マスク適用後に補間したスカラー値。範囲外・有効点不足は ``NaN``。
    """
    sel = np.asarray(series_mask, dtype=bool)
    xs = np.asarray(xp, dtype=np.float64)[sel]
    ys = np.asarray(fp, dtype=np.float64)[sel]
    if xs.size < 2:
        return float("nan")
    return _interpolate_real(x_query, xs, ys)


def _catalog_for_supply(
    catalogs: list[ImPerformanceCurveCatalogDto],
    f_hz: float,
    v_v: float,
) -> ImPerformanceCurveCatalogDto | None:
    """(f, V) が一致するカタログ（残差に必要な系列が揃ったもの）を返す。

    残差ベクトルは (|I|, P, PF, η) の 4 チャネルで構成されるため、
    ``current_series`` / ``power_series`` / ``power_factor_series`` /
    ``efficiency_series`` のどれかが ``None`` のカタログは
    （Forward 経由で部分列のみ供給されたケース等）対象外として
    silent に skip する。
    """
    key = (float(f_hz), float(v_v))
    for cat in catalogs:
        if (
            cat.current_series is None
            or cat.power_series is None
            or cat.power_factor_series is None
            or cat.efficiency_series is None
        ):
            continue
        cf = float(cat.supply_frequency.to_base_unit().get_value())
        cv = float(cat.supply_voltage.to_base_unit().get_value())
        if _supply_keys_close(key, (cf, cv)):
            return cat
    return None


def _axis_scalar_at(
    layout: ArrayLayoutDto,
    axis_name: ArrayKey,
    multi_idx: tuple[int, ...],
) -> float:
    """参照軸直積の 1 点における 1 次元軸のスカラー値（実部）。"""
    dim = layout.reference_axes.index(axis_name)
    pos = int(multi_idx[dim])
    raw = layout.arrays[axis_name].get_value()
    arr = np.asarray(raw)
    return float(np.real(arr.flat[pos]))


def _catalog_targets_on_layout_grid(
    layout: ArrayLayoutDto,
    *,
    n_grid: int,
    ref_shape: tuple[int, ...],
    slip_key: ArrayKey,
    fk: ArrayKey,
    vk: ArrayKey,
    cat_list: list[ImPerformanceCurveCatalogDto],
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """各直積点についてカタログ補間値 (|I|, P, PF, η) を埋めた配列を返す。

    各系列は対応する観測マスク ``*_series_mask`` を補間元から除外したうえで
    スリップ補間する（:func:`_interpolate_masked`）。マスク後の有効点が
    2 点未満となる系列・対応カタログ行が無い点は ``NaN``。チャネルごとに
    独立した mask が効くため、ある系列だけ未観測でも他系列は評価される。
    """
    target_i = np.full(n_grid, np.nan, dtype=np.float64)
    target_p = np.full(n_grid, np.nan, dtype=np.float64)
    target_pf = np.full(n_grid, np.nan, dtype=np.float64)
    target_eta = np.full(n_grid, np.nan, dtype=np.float64)
    for k in range(n_grid):
        midx = tuple(
            int(index) for index in np.unravel_index(k, ref_shape, order="C")
        )
        f_hz = _axis_scalar_at(layout, fk, midx)
        v_v = _axis_scalar_at(layout, vk, midx)
        slip_raw = _axis_scalar_at(layout, slip_key, midx)
        s_frac = _slip_fraction_from_axis(layout, slip_key, slip_raw)
        cat = _catalog_for_supply(cat_list, f_hz, v_v)
        if cat is None:
            continue
        xp = _slip_fraction_catalog(cat)
        n_series = int(xp.size)
        p_series = _one_dimensional_series_base_values(
            cast(IArrayWithUnitDto, cat.power_series)
        )
        i_series = _one_dimensional_series_base_values(
            cast(IArrayWithUnitDto, cat.current_series)
        )
        pf_series = _one_dimensional_series_base_values(
            cast(IArrayWithUnitDto, cat.power_factor_series),
        )
        eta_series = _one_dimensional_series_base_values(
            cast(IArrayWithUnitDto, cat.efficiency_series),
        )
        p_mask = _series_mask_bool(cat.power_series_mask, n_series)
        i_mask = _series_mask_bool(cat.current_series_mask, n_series)
        pf_mask = _series_mask_bool(cat.power_factor_series_mask, n_series)
        eta_mask = _series_mask_bool(cat.efficiency_series_mask, n_series)
        target_p[k] = _interpolate_masked(s_frac, xp, p_series, p_mask)
        target_i[k] = _interpolate_masked(s_frac, xp, i_series, i_mask)
        target_pf[k] = _interpolate_masked(s_frac, xp, pf_series, pf_mask)
        target_eta[k] = _interpolate_masked(s_frac, xp, eta_series, eta_mask)
    return target_i, target_p, target_pf, target_eta


def _as_flat_prefix(value: np.ndarray, label: str, n_grid: int) -> np.ndarray:
    flat = np.asarray(value).ravel()
    if flat.size < n_grid:
        raise ValueError(
            f"{label} の要素数が参照軸直積より少ないです: "
            f"size={flat.size}, n_grid={n_grid}"
        )
    return flat[:n_grid]
