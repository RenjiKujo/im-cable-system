"""カタログ目標とシミュ予測の共通比較データ（estimate_params 専用）。

``catalogs + ItmDto`` から格子点ごとの目標／予測／有効点マスクを 1 箇所で
抽出する。fit（残差ベクトル）・summary（RMSE 等）の 2 経路が本モジュールの
:func:`extract_curve_fit_comparison_data` を共有入口として利用する。

シミュ側 (|I|, P, PF, η) の取り出しは :func:`_simulated_pred_arrays` で
``ItmDto`` から直接行う（dataclass を介さない）。Output（詳細 CSV・図表）とは
抽出ロジックを共有せず、観測点（ケーブル入力 / IM 入力 / IM 二次）の解釈を
fit/summary 側だけで調整できるようにしている。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)

from .curve_grid_sampling import (
    _as_flat_prefix,
    _axis_scalar_at,
    _catalog_targets_on_layout_grid,
    _slip_fraction_from_axis,
)


def _power_factor_re_over_abs(
    cable_s: np.ndarray | np.generic,
) -> np.ndarray:
    """ケーブル入力相電力（三相複素電力）から力率 Re(S)/|S| を返す。

    Args:
        cable_s: ``input_phase_power`` の複素値（VA 基準単位）。

    Returns:
        力率 [-]。``|S|=0`` または非有限は 0.0。
    """
    cable_s_arr = np.asarray(cable_s, dtype=np.complex128)
    s_mag = np.abs(cable_s_arr)
    np.place(s_mag, s_mag == 0.0, np.nan)
    ratio = np.real(cable_s_arr) / s_mag
    return np.asarray(
        np.where(np.isfinite(ratio), ratio, 0.0),
        dtype=np.float64,
    )


def _simulated_pred_arrays(
    itm: ItmDto,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """``ItmDto`` から予測 (|I|, P, PF, η) を直接取り出す。

    fit/summary 専用の取り出し。図表生成（output 層）とは共有しない。
    どの観測点から取るかを変えたいときは本関数だけを編集する。

    Args:
        itm: シミュレーション済みの IM ケーブルシステム Itm。

    Returns:
        ``(pred_i, pred_p, pred_pf, pred_eta)`` の float64 配列タプル。
        電力・電圧電流・特性のいずれかが無い場合は None。
    """
    sim = itm.simulation_result
    if sim is None or sim.power is None:
        return None
    if sim.voltage_current is None or sim.characteristic is None:
        return None

    power = sim.power
    vc = sim.voltage_current
    ch = sim.characteristic

    pred_p = np.real(
        np.asarray(
            power.im_power.output_power.to_base_unit().get_value(),
            dtype=np.complex128,
        ),
    )
    cable_s = power.cable_power.input_phase_power.to_base_unit().get_value()
    pred_pf = _power_factor_re_over_abs(cable_s)
    pred_eta = np.asarray(
        ch.efficiency.system_efficiency.to_base_unit().get_value(),
        dtype=np.float64,
    )
    i_line = vc.cable_voltage_current.input_line_current.to_base_unit().get_magnitude()
    pred_i = np.asarray(i_line, dtype=np.float64)
    return pred_i, pred_p, pred_pf, pred_eta


@dataclass(frozen=True)
class CurveFitComparisonData:
    """カタログ補間目標とシミュ予測を同一評価格子上で比較可能にしたデータ。

    各目標系列はカタログの観測マスク ``*_series_mask`` を補間元から除外して
    補間済み（:mod:`curve_grid_sampling`）のため、未観測点は ``NaN`` になる。
    ``valid_*`` は **チャネルごとに独立** に ``isfinite(target_*)`` で定義する。

    Attributes:
        slip_fraction: 参照軸直積各点のスリップ無次元分数 [-]。
        target_i: 補間目標 |I| [A]。
        pred_i: 予測 |I|（ケーブル入力線電流の大きさ）[A]。
        valid_i: target_i が有限か（観測あり）の bool 配列。
        target_p: 補間目標出力電力実部 [W]。
        pred_p: 予測出力電力実部 [W]。
        valid_p: target_p が有限かの bool 配列。
        target_pf: 補間目標力率 [-]。
        pred_pf: 予測力率（ケーブル入力相電力に基づく）[-]。
        valid_pf: target_pf が有限かの bool 配列。
        target_eta: 補間目標システム効率 [-]。
        pred_eta: 予測システム効率 [-]。
        valid_eta: target_eta が有限かの bool 配列。
    """

    slip_fraction: np.ndarray
    target_i: np.ndarray
    pred_i: np.ndarray
    valid_i: np.ndarray
    target_p: np.ndarray
    pred_p: np.ndarray
    valid_p: np.ndarray
    target_pf: np.ndarray
    pred_pf: np.ndarray
    valid_pf: np.ndarray
    target_eta: np.ndarray
    pred_eta: np.ndarray
    valid_eta: np.ndarray


def extract_curve_fit_comparison_data(
    catalogs: ImPerformanceCurveCatalogDtos,
    itm: ItmDto,
) -> CurveFitComparisonData | None:
    """カタログ補間目標とシミュ予測の比較データを格子点ごとに返す。

    fit / summary / CSV の 3 経路が共有する唯一の抽出入口。

    Args:
        catalogs: 目標とする性能カーブカタログ。
        itm: シミュレーション結果を含む中間 DTO。

    Returns:
        比較データ。シミュレーション不足時は None。

    Raises:
        ValueError: 参照軸に slip / frequency / input_line_voltage が揃わない場合。
    """
    if itm.simulation_result is None or itm.simulation_result.power is None:
        return None
    if itm.simulation_result.characteristic is None:
        return None

    layout = itm.model.array_layout
    slip_key = ArrayKey.SLIP
    fk = ArrayKey.FREQUENCY
    vk = ArrayKey.INPUT_LINE_VOLTAGE
    for req in (slip_key, fk, vk):
        if req not in layout.reference_axes:
            raise ValueError(
                "残差計算には array_layout.reference_axes に "
                f"slip, frequency, input_line_voltage が必要です: "
                f"{layout.reference_axes}"
            )

    n_grid = layout.get_reference_total_length()
    ref_shape = layout.get_reference_shape()
    cat_list = list(catalogs.get_all())
    target_i, target_p, target_pf, target_eta = _catalog_targets_on_layout_grid(
        layout,
        n_grid=n_grid,
        ref_shape=ref_shape,
        slip_key=slip_key,
        fk=fk,
        vk=vk,
        cat_list=cat_list,
    )

    slip_fraction = np.empty(n_grid, dtype=np.float64)
    for k in range(n_grid):
        midx = tuple(
            int(index) for index in np.unravel_index(k, ref_shape, order="C")
        )
        slip_raw = _axis_scalar_at(layout, slip_key, midx)
        slip_fraction[k] = _slip_fraction_from_axis(layout, slip_key, slip_raw)

    pred = _simulated_pred_arrays(itm)
    if pred is None:
        return None
    pred_i_raw, pred_p_raw, pred_pf_raw, pred_eta_raw = pred

    pred_i = _as_flat_prefix(
        np.asarray(pred_i_raw, dtype=np.float64).ravel(),
        "pred |I_line| (cable input)",
        n_grid,
    )
    pred_p = _as_flat_prefix(
        np.asarray(pred_p_raw, dtype=np.float64).ravel(),
        "pred Pout (IM output)",
        n_grid,
    )
    pred_pf = _as_flat_prefix(
        np.asarray(pred_pf_raw, dtype=np.float64).ravel(),
        "pred PF (cable input phase power)",
        n_grid,
    )
    pred_eta = _as_flat_prefix(
        np.asarray(pred_eta_raw, dtype=np.float64).ravel(),
        "pred system efficiency",
        n_grid,
    )

    valid_i = np.isfinite(target_i)
    valid_p = np.isfinite(target_p)
    valid_pf = np.isfinite(target_pf)
    valid_eta = np.isfinite(target_eta)
    return CurveFitComparisonData(
        slip_fraction=slip_fraction,
        target_i=target_i,
        pred_i=pred_i,
        valid_i=valid_i,
        target_p=target_p,
        pred_p=pred_p,
        valid_p=valid_p,
        target_pf=target_pf,
        pred_pf=pred_pf,
        valid_pf=valid_pf,
        target_eta=target_eta,
        pred_eta=pred_eta,
        valid_eta=valid_eta,
    )
