"""インピーダンス変換計算ロジック（ドメイン層）。

このモジュールは、インピーダンスの変換を提供します。
（抵抗値からインピーダンス、アドミタンスからインピーダンス、
インダクタンス+周波数からインピーダンス、キャパシタンス+周波数からインピーダンス）

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    CAPACITANCE_FACTORS,
    INDUCTANCE_FACTORS,
    RESISTANCE_FACTORS,
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatCapacitanceDto,
    FloatInductanceDto,
    FloatResistanceDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def impedance_from_admittance(
    admittance: ArrayComplexAdmittanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """アドミタンス値からインピーダンスDTOを生成する。

    アドミタンス Y からインピーダンス Z を計算します。
    計算式: Z = 1 / Y

    入力値が極大極小の要素は計算から除外され、戻り値の前にクランプされます。

    Args:
        admittance: アドミタンスDTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: インピーダンスDTO（単位: Ω）

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    admittance_base = admittance.to_base_unit().value

    # 入力値の極大極小を検出
    # その前の段階（生成・合成）でクランプされているが、
    # 計算過程で極小・極大値が生成される可能性があるため、検出する
    too_small = np.abs(admittance_base) <= eps
    too_large = ~np.isfinite(admittance_base) | (
        np.abs(admittance_base) >= max_mag
    )

    if np.any(too_small):
        record_numerical_stability_event(
            event_codes.ADMITTANCE_TOO_SMALL_FOR_IMPEDANCE,
        )
    if np.any(too_large):
        record_numerical_stability_event(
            event_codes.ADMITTANCE_TOO_LARGE_FOR_IMPEDANCE,
        )

    # 極小値は位相を保持して大きさをepsに正規化
    # これにより、Z=1/Yの関係が物理的に正しく保たれる
    admittance_magnitude = np.abs(admittance_base)
    admittance_phase = np.angle(admittance_base)
    # 極小値の場合、位相を保持して大きさをepsに正規化
    safe_magnitude = np.where(too_small, eps, admittance_magnitude)
    # 極大値の場合、位相を保持して大きさをmax_magに正規化
    safe_magnitude = np.where(too_large, max_mag, safe_magnitude)
    safe_admittance = safe_magnitude * np.exp(1j * admittance_phase)

    with np.errstate(divide="ignore", invalid="ignore"):
        impedance_value = 1.0 / safe_admittance

    # マスクした要素を戻り値前にクランプ
    impedance_value = np.where(
        too_small, max_mag, impedance_value
    )  # 極小アドミタンス → 極大インピーダンス
    impedance_value = np.where(
        too_large, eps, impedance_value
    )  # 極大アドミタンス → 極小インピーダンス

    return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")


def impedance_from_resistance_and_frequency(
    resistance: FloatResistanceDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """抵抗値からインピーダンスDTOを生成する。

    実数の抵抗値を複素数インピーダンス配列（虚部0）に変換する。
    スカラー値を周波数配列の形状にブロードキャストする。
    結果の配列形状とaxesは周波数配列から取得されます。

    入力値が極大極小の場合は計算をスキップし、戻り値の前にクランプされます。

    Args:
        resistance: 抵抗DTO（スカラー値）
        frequency: 周波数DTO（配列、結果の配列形状とaxesを決定する）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: インピーダンスDTO（単位: Ω）

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    # 抵抗を基本単位（Ω）に変換
    resistance_factor = RESISTANCE_FACTORS[resistance.get_unit()]
    base_resistance_value = resistance.get_value() * resistance_factor

    # 入力値の極大極小を検出
    is_too_small = abs(base_resistance_value) <= eps
    is_too_large = (
        not np.isfinite(base_resistance_value)
        or abs(base_resistance_value) >= max_mag
    )

    if is_too_small:
        record_numerical_stability_event(event_codes.RESISTANCE_TOO_SMALL)
        clamped_value = eps
    elif is_too_large:
        record_numerical_stability_event(event_codes.RESISTANCE_TOO_LARGE)
        clamped_value = (
            max_mag if np.isfinite(base_resistance_value) else max_mag
        )
    else:
        clamped_value = base_resistance_value

    # 配列化（周波数配列の形状に合わせる）
    impedance_value = np.full(
        frequency.value.shape, clamped_value, dtype=np.complex128
    )
    return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")


def impedance_from_inductance_and_frequency(
    inductance: FloatInductanceDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """インダクタンスと周波数からインピーダンスDTOを生成する。

    インダクタンスと周波数からインピーダンスを計算します。
    計算式: Z = jωL = j * 2π * f * L
    結果は常に基本単位（Ω）で返されます。
    インダクタンスはスカラー値として扱い、周波数配列にブロードキャストされます。
    結果の配列形状とaxesは周波数配列から取得されます。

    インダクタンス値が極大極小の場合は計算をスキップし、戻り値の前にクランプされます。

    Args:
        inductance: インダクタンスDTO（スカラー値）
        frequency: 周波数DTO（配列、結果の配列形状とaxesを決定する）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: インピーダンスDTO（単位: Ω）

    Raises:
        ValueError: インダクタンス値が無効な場合

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    # インダクタンスを基本単位（H）に変換
    inductance_factor = INDUCTANCE_FACTORS[inductance.get_unit()]
    inductance_base = inductance.get_value() * inductance_factor

    # 周波数を基本単位（Hz）に変換
    frequency_base = frequency.to_base_unit().value

    # 入力値の極大極小を検出
    is_too_small = abs(inductance_base) <= eps
    is_too_large = (
        not np.isfinite(inductance_base) or abs(inductance_base) >= max_mag
    )

    if is_too_small:
        record_numerical_stability_event(event_codes.INDUCTANCE_TOO_SMALL)
        # 配列全体をクランプ値で埋める
        impedance_value = np.full(
            frequency_base.shape, eps, dtype=np.complex128
        )
        return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")
    if is_too_large:
        record_numerical_stability_event(event_codes.INDUCTANCE_TOO_LARGE)
        # 配列全体をクランプ値で埋める
        impedance_value = np.full(
            frequency_base.shape, max_mag, dtype=np.complex128
        )
        return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")

    # インピーダンス計算: Z = jωL = j * 2π * f * L
    # インダクタンスはスカラーなので、周波数配列にブロードキャストされる
    # 結果の配列形状は周波数配列の形状に従う
    impedance_value = 1j * 2 * np.pi * frequency_base * inductance_base
    return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")


def impedance_from_capacitance_and_frequency(
    capacitance: FloatCapacitanceDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """キャパシタンスと周波数からインピーダンスDTOを生成する。

    キャパシタンスと周波数からキャパシタのインピーダンスを計算します。
    計算式: Z = 1 / (j 2π f C) = -j / (2π f C)
    結果は常に基本単位（Ω）で返されます。
    キャパシタンスはスカラー値として扱い、周波数配列にブロードキャストされます。
    結果の配列形状とaxesは周波数配列から取得されます。

    キャパシタンス値が極大極小の場合は計算をスキップし、戻り値の前にクランプされます。

    Args:
        capacitance: キャパシタンスDTO（スカラー値）
        frequency: 周波数DTO（配列、結果の配列形状とaxesを決定する）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexImpedanceDto: インピーダンスDTO（単位: Ω）

    Raises:
        ValueError: キャパシタンス値が無効な場合

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    # キャパシタンスを基本単位（F）に変換
    capacitance_factor = CAPACITANCE_FACTORS[capacitance.get_unit()]
    capacitance_base = capacitance.get_value() * capacitance_factor

    # 周波数を基本単位（Hz）に変換
    frequency_base = frequency.to_base_unit().value

    # 入力値の極大極小を検出
    is_too_small = abs(capacitance_base) <= eps
    is_too_large = (
        not np.isfinite(capacitance_base) or abs(capacitance_base) >= max_mag
    )

    if is_too_small:
        record_numerical_stability_event(event_codes.CAPACITANCE_TOO_SMALL)
        # 配列全体をクランプ値で埋める
        impedance_value = np.full(
            frequency_base.shape, max_mag, dtype=np.complex128
        )
        return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")
    if is_too_large:
        record_numerical_stability_event(event_codes.CAPACITANCE_TOO_LARGE)
        # 配列全体をクランプ値で埋める
        impedance_value = np.full(
            frequency_base.shape, eps, dtype=np.complex128
        )
        return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")

    # インピーダンス計算: Z = 1 / (j 2π f C) = -j / (2π f C)
    # キャパシタンスはスカラーなので、周波数配列にブロードキャストされる
    with np.errstate(divide="ignore", invalid="ignore"):
        impedance_value = np.asarray(
            (-1j) / (2 * np.pi * frequency_base * capacitance_base),
            dtype=np.complex128,
        )

    return ArrayComplexImpedanceDto(value=impedance_value, unit="Ω")
