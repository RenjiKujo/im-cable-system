"""estimate_params レポート向けのカタログ補間・シミュ予測サンプリング。

カタログ（目標）を参照軸直積グリッドへスリップ補間し、シミュレーション予測
(|I|, P, PF, η) と同じ格子で突き合わせた比較データを組み立てる。

NOTE: 同種の抽出・補間は estimate_params（execute 層）の ``support.curve_eval``
    にも存在するが、**意図的に共有せず複製している**。レポート（output）と
    fit/summary（execute）で観測点（ケーブル入力 / IM 入力 / IM 二次）の解釈や
    行整形を独立に調整できるようにするため。execute 層への依存を持たせない。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
)

_FREQ_ABS_TOL = 1e-4
_VOLT_ABS_TOL = 1.0
_RAD_S_TO_RPM = 60.0 / (2.0 * math.pi)


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
    """系列マスクを長さ ``length`` の bool 配列へ正規化する（None は全点観測）。"""
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

    マスク後の有効点が 2 点未満の場合は ``NaN`` を返す（下流で評価対象外）。
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
    """(f, V) が一致するカタログ（必要系列が揃ったもの）を返す。"""
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


def _as_flat_prefix(value: np.ndarray, label: str, n_grid: int) -> np.ndarray:
    """1 次元化して先頭 ``n_grid`` 要素を返す（不足はエラー）。"""
    flat = np.asarray(value).ravel()
    if flat.size < n_grid:
        raise ValueError(
            f"{label} の要素数が参照軸直積より少ないです: "
            f"size={flat.size}, n_grid={n_grid}"
        )
    return flat[:n_grid]


def _catalog_targets_on_layout_grid(
    layout: ArrayLayoutDto,
    *,
    n_grid: int,
    ref_shape: tuple[int, ...],
    slip_key: ArrayKey,
    fk: ArrayKey,
    vk: ArrayKey,
    cat_list: list[ImPerformanceCurveCatalogDto],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """各直積点についてカタログ補間値 (|I|, P, PF, η) を埋めた配列を返す。

    各系列は観測マスクを補間元から除外してスリップ補間する。有効点 2 点未満・
    対応カタログ行が無い点は ``NaN``。
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
            cast(IArrayWithUnitDto, cat.power_factor_series)
        )
        eta_series = _one_dimensional_series_base_values(
            cast(IArrayWithUnitDto, cat.efficiency_series)
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


def _catalog_rpm_on_layout_grid(
    layout: ArrayLayoutDto,
    *,
    n_grid: int,
    ref_shape: tuple[int, ...],
    slip_key: ArrayKey,
    fk: ArrayKey,
    vk: ArrayKey,
    cat_list: list[ImPerformanceCurveCatalogDto],
) -> np.ndarray:
    """各直積点でカタログ回転速度をスリップ補間し [rpm] で返す。

    対応カタログ行が無い点・回転速度系列が無い点は ``NaN``。
    """
    out = np.full(n_grid, np.nan, dtype=np.float64)
    for k in range(n_grid):
        midx = tuple(
            int(index) for index in np.unravel_index(k, ref_shape, order="C")
        )
        f_hz = _axis_scalar_at(layout, fk, midx)
        v_v = _axis_scalar_at(layout, vk, midx)
        slip_raw = _axis_scalar_at(layout, slip_key, midx)
        s_frac = _slip_fraction_from_axis(layout, slip_key, slip_raw)
        cat = _catalog_for_supply(cat_list, f_hz, v_v)
        if cat is None or cat.rotational_speed_series is None:
            continue
        xp = _slip_fraction_catalog(cat)
        omega_series = _one_dimensional_series_base_values(
            cat.rotational_speed_series,
        )
        omega = _interpolate_real(s_frac, xp, omega_series)
        out[k] = omega * _RAD_S_TO_RPM if np.isfinite(omega) else np.nan
    return out


def _slip_fraction_grid(
    layout: ArrayLayoutDto,
    *,
    slip_key: ArrayKey,
    n_grid: int,
    ref_shape: tuple[int, ...],
) -> np.ndarray:
    """参照軸直積の線形順序に沿ったスリップ無次元分数 [-] の配列。"""
    out = np.empty(n_grid, dtype=np.float64)
    for k in range(n_grid):
        midx = tuple(
            int(index) for index in np.unravel_index(k, ref_shape, order="C")
        )
        slip_raw = _axis_scalar_at(layout, slip_key, midx)
        out[k] = _slip_fraction_from_axis(layout, slip_key, slip_raw)
    return out


def _power_factor_re_over_abs(
    cable_s: np.ndarray | np.generic,
) -> np.ndarray:
    """ケーブル入力相電力（三相複素電力）から力率 Re(S)/|S| を返す。"""
    cable_s_arr = np.asarray(cable_s, dtype=np.complex128)
    s_mag = np.abs(cable_s_arr)
    np.place(s_mag, s_mag == 0.0, np.nan)
    ratio = np.real(cable_s_arr) / s_mag
    return np.asarray(
        np.where(np.isfinite(ratio), ratio, 0.0),
        dtype=np.float64,
    )


def _simulated_pred_arrays(
    output_dto: OutputDto,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """``OutputDto`` の結果生量から予測 (|I|, P, PF, η) を取り出す。

    どの観測点から取るかを変えたいときは本関数だけを編集する（レポート専用）。

    Returns:
        ``(pred_i, pred_p, pred_pf, pred_eta)``。
    """
    result = output_dto.result
    pred_p = np.real(
        np.asarray(
            result.output_power.to_base_unit().get_value(),
            dtype=np.complex128,
        ),
    )
    cable_s = result.cable_input_phase_power.to_base_unit().get_value()
    pred_pf = _power_factor_re_over_abs(cable_s)
    pred_eta = np.asarray(
        result.system_efficiency.to_base_unit().get_value(),
        dtype=np.float64,
    )
    i_line = result.input_line_current.to_base_unit().get_magnitude()
    pred_i = np.asarray(i_line, dtype=np.float64)
    return pred_i, pred_p, pred_pf, pred_eta


@dataclass(frozen=True)
class CatalogVsSimCurveData:
    """レポート行整形向けの、カタログ補間目標とシミュ予測の同一格子比較データ。

    Attributes:
        slip_fraction: 参照軸直積各点のスリップ無次元分数 [-]。
        target_i: 補間目標 |I| [A]。
        target_p: 補間目標出力電力実部 [W]。
        target_pf: 補間目標力率 [-]。
        target_eta: 補間目標効率 [-]。
        catalog_rpm: 補間目標の回転速度 [rpm]。
        pred_i: 予測 |I|（ケーブル入力線電流の大きさ）[A]。
        pred_p: 予測出力電力実部 [W]。
        pred_pf: 予測力率（ケーブル入力相電力に基づく）[-]。
        pred_eta: 予測システム効率 [-]。
    """

    slip_fraction: np.ndarray
    target_i: np.ndarray
    target_p: np.ndarray
    target_pf: np.ndarray
    target_eta: np.ndarray
    catalog_rpm: np.ndarray
    pred_i: np.ndarray
    pred_p: np.ndarray
    pred_pf: np.ndarray
    pred_eta: np.ndarray


def build_catalog_vs_sim_curve_data(
    output_dto: OutputDto,
) -> CatalogVsSimCurveData | None:
    """レポート用にカタログ補間目標とシミュ予測を同一格子で組み立てる。

    Args:
        output_dto: 出力トップ DTO（完全計算済みの結果生量を保持）。

    Returns:
        比較データ。必要な参照軸欠如時は None。
    """
    layout = output_dto.array_layout
    slip_key = ArrayKey.SLIP
    fk = ArrayKey.FREQUENCY
    vk = ArrayKey.INPUT_LINE_VOLTAGE
    for req in (slip_key, fk, vk):
        if req not in layout.reference_axes:
            return None

    n_grid = layout.get_reference_total_length()
    ref_shape = layout.get_reference_shape()
    cat_list = list(output_dto.im_pc_catalogs.get_all())

    target_i, target_p, target_pf, target_eta = _catalog_targets_on_layout_grid(
        layout,
        n_grid=n_grid,
        ref_shape=ref_shape,
        slip_key=slip_key,
        fk=fk,
        vk=vk,
        cat_list=cat_list,
    )
    catalog_rpm = _catalog_rpm_on_layout_grid(
        layout,
        n_grid=n_grid,
        ref_shape=ref_shape,
        slip_key=slip_key,
        fk=fk,
        vk=vk,
        cat_list=cat_list,
    )
    slip_fraction = _slip_fraction_grid(
        layout,
        slip_key=slip_key,
        n_grid=n_grid,
        ref_shape=ref_shape,
    )

    pred_i_raw, pred_p_raw, pred_pf_raw, pred_eta_raw = _simulated_pred_arrays(
        output_dto,
    )
    pred_i = _as_flat_prefix(pred_i_raw, "pred |I_line|", n_grid)
    pred_p = _as_flat_prefix(pred_p_raw, "pred Pout", n_grid)
    pred_pf = _as_flat_prefix(pred_pf_raw, "pred PF", n_grid)
    pred_eta = _as_flat_prefix(pred_eta_raw, "pred system efficiency", n_grid)

    return CatalogVsSimCurveData(
        slip_fraction=slip_fraction,
        target_i=target_i,
        target_p=target_p,
        target_pf=target_pf,
        target_eta=target_eta,
        catalog_rpm=catalog_rpm,
        pred_i=pred_i,
        pred_p=pred_p,
        pred_pf=pred_pf,
        pred_eta=pred_eta,
    )
