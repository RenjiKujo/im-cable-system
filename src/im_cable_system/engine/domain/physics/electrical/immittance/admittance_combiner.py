"""アドミタンス合成計算ロジック（ドメイン層）。

このモジュールは、アドミタンスの合成を提供します。
（直列合成、並列合成）

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def combine_admittance_parallel(
    admittance1: ArrayComplexAdmittanceDto,
    admittance2: ArrayComplexAdmittanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """2つのアドミタンスを並列合成する。

    計算式: Y_total = Y1 + Y2

    数値安定性のためのクランプ処理:
        入力値の極小・極大要素を検出し、計算結果の対応する要素をクランプする。
        具体的には以下の3つの条件でクランプを適用する:
        1. 両方のアドミタンスがeps以下の場合: 計算結果をepsにクランプ
        2. どちらかのアドミタンスが極大（max_mag以上またはinf）の場合:
           計算結果をmax_magにクランプ
        3. 合計値の大きさがeps以下の場合: 計算結果をepsにクランプ
        クランプ時は位相を保持し、大きさのみを調整する。

    Args:
        admittance1: 第1のアドミタンスDTO
        admittance2: 第2のアドミタンスDTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: 並列合成されたアドミタンスDTO（単位: S）

    Raises:
        ValueError: 配列の形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（アドミタンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    if admittance1.value.shape != admittance2.value.shape:
        raise ValueError(
            f"アドミタンス配列の形状が一致しません: "
            f"{admittance1.value.shape} vs {admittance2.value.shape}"
        )

    admittance1_base = admittance1.to_base_unit()
    admittance2_base = admittance2.to_base_unit()

    admittance1_value = admittance1_base.value
    admittance2_value = admittance2_base.value

    admittance1_magnitude = np.abs(admittance1_value)
    admittance2_magnitude = np.abs(admittance2_value)
    admittance1_too_small = admittance1_magnitude <= eps
    admittance2_too_small = admittance2_magnitude <= eps
    admittance1_too_large = ~np.isfinite(admittance1_value) | (
        admittance1_magnitude >= max_mag
    )
    admittance2_too_large = ~np.isfinite(admittance2_value) | (
        admittance2_magnitude >= max_mag
    )

    both_small_mask = admittance1_too_small & admittance2_too_small
    either_large_mask = admittance1_too_large | admittance2_too_large

    combined_value = admittance1_value + admittance2_value
    combined_magnitude = np.abs(combined_value)
    sum_small_mask = combined_magnitude <= eps
    if (
        np.any(both_small_mask)
        or np.any(either_large_mask)
        or np.any(sum_small_mask)
    ):
        record_numerical_stability_event(
            event_codes.ADMITTANCE_COMBINER_CLAMP,
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

    return ArrayComplexAdmittanceDto(
        value=combined_value, unit=admittance1_base.get_unit()
    )


def combine_admittance_series(
    admittance1: ArrayComplexAdmittanceDto,
    admittance2: ArrayComplexAdmittanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """2つのアドミタンスを直列合成する。

    計算式: Y_total = 1 / (1/Y1 + 1/Y2) = (Y1 * Y2) / (Y1 + Y2)

    数値安定性のためのクランプ処理:
        入力値の極小・極大要素を検出し、計算結果の対応する要素をクランプする。
        具体的には以下の3つの条件でクランプを適用する:
        1. 両方のアドミタンスがeps以下の場合: 計算結果をepsにクランプ
        2. どちらかのアドミタンスが極大（max_mag以上またはinf）の場合:
           計算結果をmax_magにクランプ
        3. 分母（Y1 + Y2）の大きさがeps以下の場合:
           ゼロ除算を回避するため分母をepsにクランプし、
           計算結果もepsにクランプ
        クランプ時は位相を保持し、大きさのみを調整する。

    Args:
        admittance1: 第1のアドミタンスDTO
        admittance2: 第2のアドミタンスDTO
        eps: 最小閾値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: 直列合成されたアドミタンスDTO（単位: S）

    Raises:
        ValueError: 配列の形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（アドミタンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    if admittance1.value.shape != admittance2.value.shape:
        raise ValueError(
            f"アドミタンス配列の形状が一致しません: "
            f"{admittance1.value.shape} vs {admittance2.value.shape}"
        )

    admittance1_base = admittance1.to_base_unit()
    admittance2_base = admittance2.to_base_unit()

    admittance1_value = admittance1_base.value
    admittance2_value = admittance2_base.value

    admittance1_magnitude = np.abs(admittance1_value)
    admittance2_magnitude = np.abs(admittance2_value)
    admittance1_too_small = admittance1_magnitude <= eps
    admittance2_too_small = admittance2_magnitude <= eps
    admittance1_too_large = ~np.isfinite(admittance1_value) | (
        admittance1_magnitude >= max_mag
    )
    admittance2_too_large = ~np.isfinite(admittance2_value) | (
        admittance2_magnitude >= max_mag
    )

    both_small_mask = admittance1_too_small & admittance2_too_small
    either_large_mask = admittance1_too_large | admittance2_too_large

    numerator = admittance1_value * admittance2_value
    denominator = admittance1_value + admittance2_value

    denominator_magnitude = np.abs(denominator)
    sum_small_mask = denominator_magnitude <= eps
    if (
        np.any(both_small_mask)
        or np.any(either_large_mask)
        or np.any(sum_small_mask)
    ):
        record_numerical_stability_event(
            event_codes.ADMITTANCE_COMBINER_CLAMP,
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
    one_small_one_large_mask = (
        admittance1_too_small & admittance2_too_large
    ) | (admittance1_too_large & admittance2_too_small)

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
        both_large_mask = admittance1_too_large & admittance2_too_large
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

    return ArrayComplexAdmittanceDto(value=combined_value, unit="S")


def combine_admittances_series(
    admittances: list[ArrayComplexAdmittanceDto],
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """複数のアドミタンスを直列合成する。

    計算式: Y_total = 1 / (1/Y1 + 1/Y2 + ... + 1/Yn)
    または、2つずつ合成: Y_total = ((Y1 || Y2) || Y3) || ...

    内部では`combine_admittance_series()`を繰り返し呼び出して合成します。

    Args:
        admittances: アドミタンスDTOのリスト。
            空のリストの場合はValueErrorを発生させます。
        eps: 最小閾値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: 直列合成されたアドミタンスDTO（単位: S）

    Raises:
        ValueError: アドミタンスリストが空の場合、または配列の形状が一致しない場合
    """
    if len(admittances) == 0:
        raise ValueError("アドミタンスリストが空です。")

    if len(admittances) == 1:
        return admittances[0]

    result = admittances[0]
    for y in admittances[1:]:
        result = combine_admittance_series(
            admittance1=result, admittance2=y, eps=eps, max_mag=max_mag
        )

    return result


def combine_admittances_parallel(
    admittances: list[ArrayComplexAdmittanceDto],
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """複数のアドミタンスを並列合成する。

    計算式: Y_total = Y1 + Y2 + ... + Yn

    内部では`combine_admittance_parallel()`を繰り返し呼び出して合成します。

    Args:
        admittances: アドミタンスDTOのリスト。
            空のリストの場合はValueErrorを発生させます。
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: 並列合成されたアドミタンスDTO（単位: S）

    Raises:
        ValueError: アドミタンスリストが空の場合、または配列の形状が一致しない場合
    """
    if len(admittances) == 0:
        raise ValueError("アドミタンスリストが空です。")

    if len(admittances) == 1:
        return admittances[0]

    result = admittances[0]
    for y in admittances[1:]:
        result = combine_admittance_parallel(
            admittance1=result, admittance2=y, eps=eps, max_mag=max_mag
        )

    return result
