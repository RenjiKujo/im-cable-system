"""estimate_params レポート向けシミュレーション曲線行の組み立て。

詳細レポートではカタログ（マッチング対象）とシミュレーション結果を同じ単位で
並べる: slip[-], rpm, P[W], I[A], PF[-], η[-], τ[N·m]。
"""

from __future__ import annotations

import math

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.curve_sampling import (  # noqa: E501
    build_catalog_vs_sim_curve_data,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
)


def nameplate_power_current_w_a_for_estimate_params_table(
    output_dto: OutputDto,
) -> tuple[float, float]:
    """テーブル・曲線正規化用の名板 P[W]・I[A]。"""
    im = output_dto.im.im_series
    p_w = float(np.real(im.nameplate_power.to_base_unit().get_value()))
    i_a = float(np.real(im.nameplate_current.to_base_unit().get_value()))
    if p_w <= 0.0 or not np.isfinite(p_w):
        msg = "nameplate_power が正の有限値である必要があります。"
        raise ValueError(msg)
    if i_a <= 0.0 or not np.isfinite(i_a):
        msg = "nameplate_current が正の有限値である必要があります。"
        raise ValueError(msg)
    return p_w, i_a


def _torque_nm_from_power_w_and_rpm(p_w: float, rpm: float) -> float:
    """機械出力 P[W] と回転速度 [rpm] から τ[N·m] を返す（P = τ·ω）。"""
    omega = 2.0 * math.pi * float(rpm) / 60.0
    if not np.isfinite(p_w) or not np.isfinite(rpm) or omega <= 1e-15:
        return float("nan")
    return float(p_w / omega)


def build_simulated_curve_rows_matching_input_estimate_params_csv(
    output_dto: OutputDto,
) -> tuple[list[list[float]], int] | None:
    """シミュレーションとカタログ補間を同じ slip 格子で並べた曲線行を返す。

    各行は
    slip[-], rotational_speed(sim)[rpm], P(sim)[W], P(catalog)[W],
    I(sim)[A], I(catalog)[A], PF(sim)[-], PF(catalog)[-],
    η(sim)[-], η(catalog)[-], τ(sim)[N·m], τ(catalog)[N·m]。

    Returns:
        (rows, n_points)。必要な参照軸（SLIP）欠如時は None。
    """
    layout = output_dto.array_layout
    if ArrayKey.SLIP not in layout.reference_axes:
        return None

    data = build_catalog_vs_sim_curve_data(output_dto)
    if data is None:
        return None

    n_grid = layout.get_reference_total_length()

    result = output_dto.result
    # rotational_speed は convert ステップで rpm 換算済み。
    rpm_sim = np.asarray(
        result.rotational_speed.get_value(),
        dtype=np.float64,
    ).ravel()[:n_grid]

    torque_nm = result.torque.to_base_unit()
    tau_sim = np.asarray(torque_nm.get_value(), dtype=np.float64).ravel()[
        :n_grid
    ]

    rows: list[list[float]] = []
    for k in range(n_grid):
        p_cat = float(data.target_p[k])
        rpm_c = float(data.catalog_rpm[k])
        tau_c = _torque_nm_from_power_w_and_rpm(p_cat, rpm_c)
        rows.append(
            [
                float(data.slip_fraction[k]),
                float(rpm_sim[k]),
                float(data.pred_p[k]),
                p_cat,
                float(data.pred_i[k]),
                float(data.target_i[k]),
                float(data.pred_pf[k]),
                float(data.target_pf[k]),
                float(data.pred_eta[k]),
                float(data.target_eta[k]),
                float(tau_sim[k]),
                tau_c,
            ]
        )
    return rows, n_grid
