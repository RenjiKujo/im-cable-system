"""インピーダンス合成計算ロジック（ドメイン層）。

このモジュールは、インピーダンスの合成を提供します。
（直列合成、並列合成）

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexImpedanceDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def combine_impedance_series(
    impedance1: ArrayComplexImpedanceDto,
    impedance2: ArrayComplexImpedanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """2つのインピーダンスを直列合成する。

    計算式: Z_total = Z1 + Z2

    数値安定性のためのクランプ処理:
        入力値の極小・極大要素を検出し、計算結果の対応する要素をクランプする。
        具体的には以下の3つの条件でクランプを適用する:
        1. 両方のインピーダンスがeps以下の場合: 計算結果をepsにクランプ
        2. どちらかのインピーダンスが極大（max_mag以上またはinf）の場合:
           計算結果をmax_magにクランプ
        3. 合計値の大きさがeps以下の場合: 計算結果をepsにクランプ
        クランプ時は位相を保持し、大きさのみを調整する。

    Args:
        impedance1: 第1のインピーダンスDTO
        impedance2: 第2のインピーダンスDTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: 直列合成されたインピーダンスDTO（単位: Ω）

    Raises:
        ValueError: 配列の形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（インピーダンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    if impedance1.value.shape != impedance2.value.shape:
        raise ValueError(
            f"インピーダンス配列の形状が一致しません: "
            f"{impedance1.value.shape} vs {impedance2.value.shape}"
        )

    impedance1_base = impedance1.to_base_unit()
    impedance2_base = impedance2.to_base_unit()

    impedance1_value = impedance1_base.value
    impedance2_value = impedance2_base.value

    impedance1_magnitude = np.abs(impedance1_value)
    impedance2_magnitude = np.abs(impedance2_value)
    impedance1_too_small = impedance1_magnitude <= eps
    impedance2_too_small = impedance2_magnitude <= eps
    impedance1_too_large = ~np.isfinite(impedance1_value) | (
        impedance1_magnitude >= max_mag
    )
    impedance2_too_large = ~np.isfinite(impedance2_value) | (
        impedance2_magnitude >= max_mag
    )

    both_small_mask = impedance1_too_small & impedance2_too_small
    either_large_mask = impedance1_too_large | impedance2_too_large

    combined_value = impedance1_value + impedance2_value
    combined_magnitude = np.abs(combined_value)
    sum_small_mask = combined_magnitude <= eps
    if (
        np.any(both_small_mask)
        or np.any(either_large_mask)
        or np.any(sum_small_mask)
    ):
        record_numerical_stability_event(
            event_codes.IMPEDANCE_COMBINER_CLAMP,
        )

    combined_phase = np.angle(combined_value)
    combined_magnitude_clamped = combined_magnitude.copy()

    if np.any(both_small_mask):
        combined_magnitude_clamped = np.where(
            both_small_mask,
            eps,
            combined_magnitude_clamped,
        )

    if np.any(either_large_mask):
        combined_magnitude_clamped = np.where(
            either_large_mask,
            max_mag,
            combined_magnitude_clamped,
        )

    if np.any(sum_small_mask):
        combined_magnitude_clamped = np.where(
            sum_small_mask,
            eps,
            combined_magnitude_clamped,
        )

    combined_value = combined_magnitude_clamped * np.exp(1j * combined_phase)

    return ArrayComplexImpedanceDto(value=combined_value, unit="Ω")


def combine_impedance_parallel(
    impedance1: ArrayComplexImpedanceDto,
    impedance2: ArrayComplexImpedanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """2つのインピーダンスを並列合成する。

    計算式: Z_total = (Z1 * Z2) / (Z1 + Z2)

    数値安定性のためのクランプ処理:
        入力値の極小・極大要素を検出し、計算結果の対応する要素をクランプする。
        具体的には以下の3つの条件でクランプを適用する:
        1. 両方のインピーダンスがeps以下の場合: 計算結果をepsにクランプ
        2. どちらかのインピーダンスが極大（max_mag以上またはinf）の場合:
           計算結果をmax_magにクランプ
        3. 分母（Z1 + Z2）の大きさがeps以下の場合:
           ゼロ除算を回避するため分母をepsにクランプし、
           計算結果もepsにクランプ
        クランプ時は位相を保持し、大きさのみを調整する。

    Args:
        impedance1: 第1のインピーダンスDTO
        impedance2: 第2のインピーダンスDTO
        eps: 最小閾値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: 並列合成されたインピーダンスDTO（単位: Ω）

    Raises:
        ValueError: 配列の形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（インピーダンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    if impedance1.value.shape != impedance2.value.shape:
        raise ValueError(
            f"インピーダンス配列の形状が一致しません: "
            f"{impedance1.value.shape} vs {impedance2.value.shape}"
        )

    impedance1_base = impedance1.to_base_unit()
    impedance2_base = impedance2.to_base_unit()

    impedance1_value = impedance1_base.value
    impedance2_value = impedance2_base.value

    impedance1_magnitude = np.abs(impedance1_value)
    impedance2_magnitude = np.abs(impedance2_value)
    impedance1_too_small = impedance1_magnitude <= eps
    impedance2_too_small = impedance2_magnitude <= eps
    impedance1_too_large = ~np.isfinite(impedance1_value) | (
        impedance1_magnitude >= max_mag
    )
    impedance2_too_large = ~np.isfinite(impedance2_value) | (
        impedance2_magnitude >= max_mag
    )

    both_small_mask = impedance1_too_small & impedance2_too_small
    either_large_mask = impedance1_too_large | impedance2_too_large

    numerator = impedance1_value * impedance2_value
    denominator = impedance1_value + impedance2_value

    denominator_magnitude = np.abs(denominator)
    sum_small_mask = denominator_magnitude <= eps
    if (
        np.any(both_small_mask)
        or np.any(either_large_mask)
        or np.any(sum_small_mask)
    ):
        record_numerical_stability_event(
            event_codes.IMPEDANCE_COMBINER_CLAMP,
        )

    denominator_safe = np.where(
        sum_small_mask,
        eps * np.sign(denominator),
        denominator,
    )

    combined_value = numerator / denominator_safe

    combined_magnitude = np.abs(combined_value)
    combined_phase = np.angle(combined_value)
    combined_magnitude_clamped = combined_magnitude.copy()

    # 極小と極大が混在する場合の処理
    # 極小 × 極大 / (極小 + 極大) ≈ 極小（極小が支配的）
    one_small_one_large_mask = (impedance1_too_small & impedance2_too_large) | (
        impedance1_too_large & impedance2_too_small
    )

    if np.any(both_small_mask):
        combined_magnitude_clamped = np.where(
            both_small_mask,
            eps,
            combined_magnitude_clamped,
        )

    if np.any(one_small_one_large_mask):
        combined_magnitude_clamped = np.where(
            one_small_one_large_mask,
            eps,
            combined_magnitude_clamped,
        )

    if np.any(either_large_mask):
        # 両方が極大の場合のみmax_magにクランプ
        both_large_mask = impedance1_too_large & impedance2_too_large
        combined_magnitude_clamped = np.where(
            both_large_mask,
            max_mag,
            combined_magnitude_clamped,
        )

    if np.any(sum_small_mask):
        combined_magnitude_clamped = np.where(
            sum_small_mask,
            eps,
            combined_magnitude_clamped,
        )

    combined_value = combined_magnitude_clamped * np.exp(1j * combined_phase)

    return ArrayComplexImpedanceDto(value=combined_value, unit="Ω")


def combine_impedances_series(
    impedances: list[ArrayComplexImpedanceDto],
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """複数のインピーダンスを直列合成する。

    計算式: Z_total = Z1 + Z2 + ... + Zn

    内部では`combine_impedance_series()`を繰り返し呼び出して合成します。

    Args:
        impedances: インピーダンスDTOのリスト。
            空のリストの場合はValueErrorを発生させます。
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: 直列合成されたインピーダンスDTO（単位: Ω）

    Raises:
        ValueError: インピーダンスリストが空の場合、または配列の形状が一致しない場合
    """
    if len(impedances) == 0:
        raise ValueError("インピーダンスリストが空です。")

    if len(impedances) == 1:
        return impedances[0]

    result = impedances[0]
    for z in impedances[1:]:
        result = combine_impedance_series(
            impedance1=result, impedance2=z, eps=eps, max_mag=max_mag
        )

    return result


def combine_impedances_parallel(
    impedances: list[ArrayComplexImpedanceDto],
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """複数のインピーダンスを並列合成する。

    計算式: Z_total = 1 / (1/Z1 + 1/Z2 + ... + 1/Zn)
    または、2つずつ合成: Z_total = ((Z1 || Z2) || Z3) || ...

    内部では`combine_impedance_parallel()`を繰り返し呼び出して合成します。

    Args:
        impedances: インピーダンスDTOのリスト。
            空のリストの場合はValueErrorを発生させます。
        eps: 最小閾値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: 並列合成されたインピーダンスDTO（単位: Ω）

    Raises:
        ValueError: インピーダンスリストが空の場合、または配列の形状が一致しない場合
    """
    if len(impedances) == 0:
        raise ValueError("インピーダンスリストが空です。")

    if len(impedances) == 1:
        return impedances[0]

    result = impedances[0]
    for z in impedances[1:]:
        result = combine_impedance_parallel(
            impedance1=result, impedance2=z, eps=eps, max_mag=max_mag
        )

    return result
