"""アドミタンス変換計算ロジック（ドメイン層）。

このモジュールは、アドミタンスの変換を提供します。
（コンダクタンスからアドミタンス、インピーダンスからアドミタンス、
インダクタンス+周波数からアドミタンス、キャパシタンス+周波数からアドミタンス）

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatCapacitanceDto,
    FloatConductanceDto,
    FloatInductanceDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def admittance_from_impedance(
    impedance: ArrayComplexImpedanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """インピーダンス値からアドミタンスDTOを生成する。

    インピーダンス Z からアドミタンス Y を計算します。
    計算式: Y = 1 / Z
    結果は常に基本単位（S）で返されます。
    入力配列はブロードキャスト互換である必要があります。

    入力値が極大極小の要素は計算から除外され、戻り値の前にクランプされます。

    Args:
        impedance: インピーダンスDTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: アドミタンスDTO（単位: S）

    Note:
        極小・極大検知時は数値安定化イベントとして記録する（スコープ外では無操作）。
    """
    impedance_base = impedance.to_base_unit().value

    # 入力値の極大極小を検出
    # その前の段階（生成・合成）でクランプされているが、
    # 計算過程で極小・極大値が生成される可能性があるため、検出する
    too_small = np.abs(impedance_base) <= eps
    too_large = ~np.isfinite(impedance_base) | (
        np.abs(impedance_base) >= max_mag
    )

    if np.any(too_small):
        record_numerical_stability_event(
            event_codes.IMPEDANCE_TOO_SMALL_FOR_ADMITTANCE,
        )
    if np.any(too_large):
        record_numerical_stability_event(
            event_codes.IMPEDANCE_TOO_LARGE_FOR_ADMITTANCE,
        )

    # 極小値は位相を保持して大きさをepsに正規化
    # これにより、Y=1/Zの関係が物理的に正しく保たれる
    impedance_magnitude = np.abs(impedance_base)
    impedance_phase = np.angle(impedance_base)
    # 極小値の場合、位相を保持して大きさをepsに正規化
    safe_magnitude = np.where(too_small, eps, impedance_magnitude)
    # 極大値の場合、位相を保持して大きさをmax_magに正規化
    safe_magnitude = np.where(too_large, max_mag, safe_magnitude)
    safe_impedance = safe_magnitude * np.exp(1j * impedance_phase)

    with np.errstate(divide="ignore", invalid="ignore"):
        admittance_value = 1.0 / safe_impedance

    # マスクした要素を戻り値前にクランプ
    admittance_value = np.where(
        too_small, max_mag, admittance_value
    )  # 極小インピーダンス → 極大アドミタンス
    admittance_value = np.where(
        too_large, eps, admittance_value
    )  # 極大インピーダンス → 極小アドミタンス

    return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")


def admittance_from_conductance_and_frequency(
    conductance: FloatConductanceDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """実数コンダクタンス値からアドミタンスDTOを生成する。

    実数のコンダクタンス値を複素数アドミタンス配列（虚部0）に変換する。
    スカラー値を周波数配列の形状にブロードキャストする。
    結果の配列形状とaxesは周波数配列から取得されます。
    結果は常に基本単位（S）で返される。

    入力値が極大極小の場合は計算をスキップし、戻り値の前にクランプされます。

    Args:
        conductance: コンダクタンスDTO（スカラー値）
        frequency: 周波数DTO（配列、結果の配列形状とaxesを決定する）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: アドミタンスDTO（単位: S）

    Raises:
        ValueError: 無効なコンダクタンス単位の場合

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    conductance_base = conductance.to_base_unit()
    base_conductance_value = conductance_base.value

    # 入力値の極大極小を検出
    is_too_small = abs(base_conductance_value) <= eps
    is_too_large = (
        not np.isfinite(base_conductance_value)
        or abs(base_conductance_value) >= max_mag
    )

    if is_too_small:
        record_numerical_stability_event(event_codes.CONDUCTANCE_TOO_SMALL)
        clamped_value = eps
    elif is_too_large:
        record_numerical_stability_event(event_codes.CONDUCTANCE_TOO_LARGE)
        clamped_value = (
            max_mag if np.isfinite(base_conductance_value) else max_mag
        )
    else:
        clamped_value = base_conductance_value

    # 配列化（周波数配列の形状に合わせる）
    admittance_value = np.full(
        frequency.value.shape, clamped_value, dtype=np.complex128
    )
    return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")


def admittance_from_inductance_and_frequency(
    inductance: FloatInductanceDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """インダクタンスと周波数からアドミタンスDTOを生成する。

    インダクタンスと周波数からアドミタンスを計算します。
    計算式: Y = 1 / (j 2π f L) = -j / (2π f L)
    結果は常に基本単位（S）で返されます。
    インダクタンスはスカラー値として扱い、周波数配列にブロードキャストされます。
    結果の配列形状とaxesは周波数配列から取得されます。

    インダクタンス値が極大極小の場合は計算をスキップし、戻り値の前にクランプされます。

    Args:
        inductance: インダクタンスDTO（スカラー値）
        frequency: 周波数DTO（配列、結果の配列形状とaxesを決定する）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: アドミタンスDTO（単位: S）

    Raises:
        ValueError: インダクタンス値が無効な場合

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    # インダクタンスを基本単位（H）に変換
    inductance_base = inductance.to_base_unit().value

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
        admittance_value = np.full(
            frequency_base.shape, max_mag, dtype=np.complex128
        )
        return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")
    if is_too_large:
        record_numerical_stability_event(event_codes.INDUCTANCE_TOO_LARGE)
        # 配列全体をクランプ値で埋める
        admittance_value = np.full(
            frequency_base.shape, eps, dtype=np.complex128
        )
        return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")

    # アドミタンス計算: Y = 1 / (j 2π f L) = -j / (2π f L)
    # インダクタンスはスカラーなので、周波数配列にブロードキャストされる
    with np.errstate(divide="ignore", invalid="ignore"):
        admittance_value = np.asarray(
            (-1j) / (2 * np.pi * frequency_base * inductance_base),
            dtype=np.complex128,
        )

    return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")


def admittance_from_capacitance_and_frequency(
    capacitance: FloatCapacitanceDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexAdmittanceDto:
    """キャパシタンスと周波数からアドミタンスDTOを生成する。

    キャパシタンスと周波数からキャパシタのアドミタンスを計算します。
    計算式: Y = j 2π f C
    結果は常に基本単位（S）で返されます。
    キャパシタンスはスカラー値として扱い、周波数配列にブロードキャストされます。
    結果の配列形状とaxesは周波数配列から取得されます。

    キャパシタンス値が極大極小の場合は計算をスキップし、戻り値の前にクランプされます。

    Args:
        capacitance: キャパシタンスDTO（スカラー値）
        frequency: 周波数DTO（配列、結果の配列形状とaxesを決定する）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexAdmittanceDto: アドミタンスDTO（単位: S）

    Raises:
        ValueError: キャパシタンス値が無効な場合

    Note:
        極小・極大検知時は数値安定化イベントとして記録する。
    """
    # キャパシタンスを基本単位（F）に変換
    capacitance_base = capacitance.to_base_unit().value

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
        admittance_value = np.full(
            frequency_base.shape, eps, dtype=np.complex128
        )
        return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")
    if is_too_large:
        record_numerical_stability_event(event_codes.CAPACITANCE_TOO_LARGE)
        # 配列全体をクランプ値で埋める
        admittance_value = np.full(
            frequency_base.shape, max_mag, dtype=np.complex128
        )
        return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")

    # アドミタンス計算: Y = j 2π f C
    # キャパシタンスはスカラーなので、周波数配列にブロードキャストされる
    # 結果の配列形状は周波数配列の形状に従う
    admittance_value = 1j * 2 * np.pi * frequency_base * capacitance_base
    return ArrayComplexAdmittanceDto(value=admittance_value, unit="S")
