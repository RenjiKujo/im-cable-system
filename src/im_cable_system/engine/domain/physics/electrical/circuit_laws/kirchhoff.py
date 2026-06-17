"""キルヒホッフの法則計算ロジック（ドメイン層）。

このモジュールは、キルヒホッフの法則（KVL、KCL）に基づく計算を提供します。

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def solve_kirchhoff_voltage(  # noqa: PLR0912
    solve_for: Literal["remaining", "total"],
    total_voltage: ArrayComplexVoltageDto | None = None,
    remaining_voltages: Sequence[ArrayComplexVoltageDto] | None = None,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """キルヒホッフの電圧則（KVL）を適用して電圧を計算する。

    キルヒホッフの電圧則: ΣV = 0 もしくは ΣV_known + V_unknown = V_total

    Args:
        solve_for: 計算対象を指定
            - "remaining": total_voltage から remaining_voltages の和を引いた
              残りの電圧を計算する。
            - "total": remaining_voltages の和を計算する。
        total_voltage: ループ全体の電圧、あるいは基準となる合計電圧。
            solve_for="remaining" のとき必須。
        remaining_voltages: 既知の電圧DTOのシーケンス。
            solve_for="remaining" および "total" のとき必須。
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 計算された電圧DTO。基本単位（V）で返される。

    Raises:
        ValueError: 配列の形状が一致しない場合、または引数が不正な場合。

    Warns:
        RuntimeWarning: 入力値（電圧）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    # solve_forのバリデーションを最初に実行
    if solve_for not in ("remaining", "total"):
        raise ValueError(
            f"無効なsolve_for値です: {solve_for}. "
            '有効な値: "remaining", "total"'
        )

    remaining_list = list(remaining_voltages) if remaining_voltages else []
    remaining_bases = [v.to_base_unit() for v in remaining_list]

    all_voltages = remaining_bases + (
        [total_voltage.to_base_unit()] if total_voltage is not None else []
    )
    if not all_voltages:
        raise ValueError(
            "少なくとも1つの電圧（total_voltage または remaining_voltages）を"
            "指定してください"
        )

    first_shape = all_voltages[0].value.shape
    for i, voltage in enumerate(all_voltages[1:], start=1):
        if voltage.value.shape != first_shape:
            raise ValueError(
                "電圧配列の形状が一致しません: "
                f"voltage[0] shape={first_shape}, "
                f"voltage[{i}] shape={voltage.value.shape}"
            )

    # 入力値の検証（極小・極大の位置を記録）
    input_extreme_mask = np.zeros(first_shape, dtype=bool)
    for voltage in all_voltages:
        voltage_value = voltage.value
        voltage_magnitude = np.abs(voltage_value)
        voltage_too_small = voltage_magnitude <= eps
        voltage_too_large = ~np.isfinite(voltage_value) | (
            voltage_magnitude >= max_mag
        )
        input_extreme_mask = (
            input_extreme_mask | voltage_too_small | voltage_too_large
        )

    if np.any(input_extreme_mask):
        record_numerical_stability_event(
            event_codes.KIRCHHOFF_VOLTAGE_EXTREME_INPUT,
        )

    if solve_for == "remaining":
        if total_voltage is None:
            raise ValueError(
                'solve_for="remaining" では total_voltage が必須です'
            )
        if not remaining_bases:
            raise ValueError(
                'solve_for="remaining" では remaining_voltages を'
                "少なくとも1つ指定する必要があります"
            )

        total_base = total_voltage.to_base_unit()
        remaining_sum = remaining_bases[0].value
        for v in remaining_bases[1:]:
            remaining_sum = remaining_sum + v.value

        result = total_base.value - remaining_sum
        base_unit = total_base.unit

    elif solve_for == "total":
        if not remaining_bases:
            raise ValueError(
                'solve_for="total" では remaining_voltages を'
                "少なくとも1つ指定する必要があります"
            )

        result = remaining_bases[0].value
        for v in remaining_bases[1:]:
            result = result + v.value
        base_unit = remaining_bases[0].unit

    # 計算結果のクランプ（入力値で極小・極大だった要素に対応）
    if np.any(input_extreme_mask):
        result_magnitude = np.abs(result)
        result_phase = np.angle(result)
        result_magnitude_clamped = np.where(
            input_extreme_mask & (result_magnitude <= eps),
            eps,
            result_magnitude,
        )
        result_magnitude_clamped = np.where(
            input_extreme_mask & (result_magnitude >= max_mag),
            max_mag,
            result_magnitude_clamped,
        )
        result = result_magnitude_clamped * np.exp(1j * result_phase)

    return ArrayComplexVoltageDto(value=result, unit=base_unit)


def solve_kirchhoff_current(  # noqa: PLR0912, PLR0915
    solve_for: Literal[
        "remaining_downstream",
        "remaining_upstream",
        "total_downstream",
        "total_upstream",
    ],
    upstream_currents: (
        list[ArrayComplexCurrentDto] | tuple[ArrayComplexCurrentDto, ...] | None
    ) = None,
    downstream_currents: (
        list[ArrayComplexCurrentDto] | tuple[ArrayComplexCurrentDto, ...] | None
    ) = None,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """キルヒホッフの電流則（KCL）を適用して電流を計算する。

    キルヒホッフの電流則: ΣI_upstream = ΣI_downstream
    上流電流と下流電流のリストを受け取り、指定された未知の電流を計算します。

    Args:
        solve_for: 計算対象を指定
            - "remaining_downstream": 残りの下流電流を計算
              （Σ上流 - Σ既知の下流）
            - "remaining_upstream": 残りの上流電流を計算
              （Σ既知の下流 - Σ既知の上流）
            - "total_downstream": 下流の合計を計算（Σ上流）
            - "total_upstream": 上流の合計を計算（Σ下流）
        upstream_currents: 上流電流DTOのリストまたはタプル（None可）
        downstream_currents: 下流電流DTOのリストまたはタプル（None可）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: 計算された電流DTO。基本単位（A）で返される。

    Raises:
        ValueError: 配列の形状が一致しない場合、または引数が不正な場合

    Warns:
        RuntimeWarning: 入力値（電流）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    # solve_forのバリデーションを最初に実行
    if solve_for not in (
        "remaining_downstream",
        "remaining_upstream",
        "total_downstream",
        "total_upstream",
    ):
        raise ValueError(
            f"無効なsolve_for値です: {solve_for}. "
            "有効な値: 'remaining_downstream', 'remaining_upstream', "
            "'total_downstream', 'total_upstream'"
        )

    # 引数の正規化（Noneの場合は空リストに変換）
    upstream_list = list(upstream_currents) if upstream_currents else []
    downstream_list = list(downstream_currents) if downstream_currents else []

    # すべての電流を基本単位に変換
    upstream_bases = [u.to_base_unit() for u in upstream_list]
    downstream_bases = [d.to_base_unit() for d in downstream_list]

    # 形状の検証（すべての電流が同じ形状であることを確認）
    all_currents = upstream_bases + downstream_bases
    if not all_currents:
        raise ValueError(
            "少なくとも1つの上流電流または下流電流を指定してください"
        )

    first_shape = all_currents[0].value.shape
    for i, current in enumerate(all_currents[1:], start=1):
        if current.value.shape != first_shape:
            raise ValueError(
                f"電流配列の形状が一致しません: "
                f"current[0] shape={first_shape}, "
                f"current[{i}] shape={current.value.shape}"
            )

    # 入力値の検証（極小・極大の位置を記録）
    input_extreme_mask = np.zeros(first_shape, dtype=bool)
    for current in all_currents:
        current_value = current.value
        current_magnitude = np.abs(current_value)
        current_too_small = current_magnitude <= eps
        current_too_large = ~np.isfinite(current_value) | (
            current_magnitude >= max_mag
        )
        input_extreme_mask = (
            input_extreme_mask | current_too_small | current_too_large
        )

    if np.any(input_extreme_mask):
        record_numerical_stability_event(
            event_codes.KIRCHHOFF_CURRENT_EXTREME_INPUT,
        )

    # solve_forに応じて計算
    if solve_for == "remaining_downstream":
        if not upstream_bases:
            raise ValueError(
                "remaining_downstreamを計算するには"
                "少なくとも1つの上流電流が必要です"
            )
        # 上流電流の合計を計算
        upstream_sum = upstream_bases[0].value
        for up in upstream_bases[1:]:
            upstream_sum = upstream_sum + up.value
        # 下流電流の合計を計算（存在する場合）
        if downstream_bases:
            downstream_sum = downstream_bases[0].value
            for down in downstream_bases[1:]:
                downstream_sum = downstream_sum + down.value
        else:
            downstream_sum = np.zeros_like(upstream_sum, dtype=np.complex128)
        result = upstream_sum - downstream_sum
        base_unit = upstream_bases[0].unit

    elif solve_for == "remaining_upstream":
        if not downstream_bases:
            raise ValueError(
                "remaining_upstreamを計算するには"
                "少なくとも1つの下流電流が必要です"
            )
        # 下流電流の合計を計算
        downstream_sum = downstream_bases[0].value
        for down in downstream_bases[1:]:
            downstream_sum = downstream_sum + down.value
        # 上流電流の合計を計算（存在する場合）
        if upstream_bases:
            upstream_sum_remaining = upstream_bases[0].value
            for up in upstream_bases[1:]:
                upstream_sum_remaining = upstream_sum_remaining + up.value
        else:
            upstream_sum_remaining = np.zeros_like(
                downstream_sum, dtype=np.complex128
            )
        result = downstream_sum - upstream_sum_remaining
        base_unit = downstream_bases[0].unit

    elif solve_for == "total_downstream":
        if not upstream_bases:
            raise ValueError(
                "total_downstreamを計算するには"
                "少なくとも1つの上流電流が必要です"
            )
        result = upstream_bases[0].value
        for up in upstream_bases[1:]:
            result = result + up.value
        base_unit = upstream_bases[0].unit

    elif solve_for == "total_upstream":
        if not downstream_bases:
            raise ValueError(
                "total_upstreamを計算するには少なくとも1つの下流電流が必要です"
            )
        result = downstream_bases[0].value
        for down in downstream_bases[1:]:
            result = result + down.value
        base_unit = downstream_bases[0].unit

    # 計算結果のクランプ（入力値で極小・極大だった要素に対応）
    if np.any(input_extreme_mask):
        result_magnitude = np.abs(result)
        result_phase = np.angle(result)
        result_magnitude_clamped = np.where(
            input_extreme_mask & (result_magnitude <= eps),
            eps,
            result_magnitude,
        )
        result_magnitude_clamped = np.where(
            input_extreme_mask & (result_magnitude >= max_mag),
            max_mag,
            result_magnitude_clamped,
        )
        result = result_magnitude_clamped * np.exp(1j * result_phase)

    return ArrayComplexCurrentDto(value=result, unit=base_unit)
