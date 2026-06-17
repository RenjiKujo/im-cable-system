"""オームの法則計算ロジック（ドメイン層）。

このモジュールは、オームの法則に基づく計算を提供します。
（V = I * Z, I = V / Z, V = I / Y, I = V * Y）

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def calculate_voltage_from_current_and_impedance(
    current: ArrayComplexCurrentDto,
    impedance: ArrayComplexImpedanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """電流とインピーダンスから電圧を計算する（オームの法則）。

    計算式: V = I * Z

    Args:
        current: 電流配列DTO
        impedance: インピーダンス配列DTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 電圧DTO（単位: V）

    Raises:
        ValueError: 電流とインピーダンスの配列形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（電流またはインピーダンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    current_base = current.to_base_unit()
    impedance_base = impedance.to_base_unit()

    current_shape = current_base.value.shape
    impedance_shape = impedance_base.value.shape

    # 電流とインピーダンスの形状が完全に一致することを確認
    if current_shape != impedance_shape:
        raise ValueError(
            "電流とインピーダンスの配列形状が一致しません: "
            f"current shape={current_shape}, "
            f"impedance shape={impedance_shape}"
        )

    # 入力値の検証（極小・極大の位置を記録）
    current_value = current_base.value
    current_magnitude = np.abs(current_value)
    current_too_small = current_magnitude <= eps
    current_too_large = ~np.isfinite(current_value) | (
        current_magnitude >= max_mag
    )
    input_extreme_mask = current_too_small | current_too_large

    impedance_value = impedance_base.value
    impedance_magnitude = np.abs(impedance_value)
    impedance_too_small = impedance_magnitude <= eps
    impedance_too_large = ~np.isfinite(impedance_value) | (
        impedance_magnitude >= max_mag
    )
    input_extreme_mask = (
        input_extreme_mask | impedance_too_small | impedance_too_large
    )

    if np.any(input_extreme_mask):
        record_numerical_stability_event(
            event_codes.OHMS_LAW_VOLTAGE_IMPEDANCE_INPUT_EXTREME,
        )

    # ゼロ除算を避けるため、インピーダンスが極小の場合はクランプ
    impedance_phase = np.angle(impedance_value)
    impedance_magnitude_safe = np.where(
        impedance_too_small, eps, impedance_magnitude
    )
    impedance_safe = impedance_magnitude_safe * np.exp(1j * impedance_phase)

    # オームの法則: V = I * Z  # noqa: ERA001
    voltage_complex = current_value * impedance_safe

    # 計算結果のクランプ（入力値で極小・極大だった要素に対応）
    if np.any(input_extreme_mask):
        voltage_magnitude = np.abs(voltage_complex)
        voltage_phase = np.angle(voltage_complex)
        # 極小インピーダンスの場合、電圧をepsにクランプ
        voltage_magnitude_clamped = np.where(
            impedance_too_small, eps, voltage_magnitude
        )
        # 極大インピーダンスの場合、電流の大きさに応じて電圧をクランプ
        # 極大電流 × 極大インピーダンス = 極大電圧
        # 極小電流 × 極大インピーダンス = 極小電圧
        current_magnitude = np.abs(current_value)
        voltage_magnitude_clamped = np.where(
            impedance_too_large & (current_magnitude >= max_mag),
            max_mag,
            voltage_magnitude_clamped,
        )
        voltage_magnitude_clamped = np.where(
            impedance_too_large & (current_magnitude <= eps),
            eps,
            voltage_magnitude_clamped,
        )
        # その他の極小・極大値の処理
        voltage_magnitude_clamped = np.where(
            input_extreme_mask & (voltage_magnitude_clamped <= eps),
            eps,
            voltage_magnitude_clamped,
        )
        voltage_magnitude_clamped = np.where(
            input_extreme_mask & (voltage_magnitude_clamped >= max_mag),
            max_mag,
            voltage_magnitude_clamped,
        )
        voltage_complex = voltage_magnitude_clamped * np.exp(1j * voltage_phase)
    # 計算結果のDTOを作成して基本単位を取得
    voltage_result = ArrayComplexVoltageDto(value=voltage_complex, unit="V")
    base_unit = voltage_result.to_base_unit().unit

    return ArrayComplexVoltageDto(value=voltage_complex, unit=base_unit)


def calculate_voltage_from_current_and_admittance(
    current: ArrayComplexCurrentDto,
    admittance: ArrayComplexAdmittanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """電流とアドミタンスから電圧を計算する（オームの法則）。

    計算式: V = I / Y

    Args:
        current: 電流配列DTO
        admittance: アドミタンス配列DTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 電圧DTO（単位: V）

    Raises:
        ValueError: 電流とアドミタンスの配列形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（電流またはアドミタンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    current_base = current.to_base_unit()
    admittance_base = admittance.to_base_unit()

    current_shape = current_base.value.shape
    admittance_shape = admittance_base.value.shape

    # 電流とアドミタンスの形状が完全に一致することを確認
    if current_shape != admittance_shape:
        raise ValueError(
            "電流とアドミタンスの配列形状が一致しません: "
            f"current shape={current_shape}, "
            f"admittance shape={admittance_shape}"
        )

    # 入力値の検証（極小・極大の位置を記録）
    current_value = current_base.value
    current_magnitude = np.abs(current_value)
    current_too_small = current_magnitude <= eps
    current_too_large = ~np.isfinite(current_value) | (
        current_magnitude >= max_mag
    )
    input_extreme_mask = current_too_small | current_too_large

    admittance_value = admittance_base.value
    admittance_magnitude = np.abs(admittance_value)
    admittance_too_small = admittance_magnitude <= eps
    admittance_too_large = ~np.isfinite(admittance_value) | (
        admittance_magnitude >= max_mag
    )
    input_extreme_mask = (
        input_extreme_mask | admittance_too_small | admittance_too_large
    )

    if np.any(input_extreme_mask):
        record_numerical_stability_event(
            event_codes.OHMS_LAW_VOLTAGE_ADMITTANCE_INPUT_EXTREME,
        )

    # ゼロ除算を避けるため、アドミタンスが極小の場合はクランプ
    admittance_phase = np.angle(admittance_value)
    admittance_magnitude_safe = np.where(
        admittance_too_small, eps, admittance_magnitude
    )
    admittance_safe = admittance_magnitude_safe * np.exp(1j * admittance_phase)

    # オームの法則: V = I / Y  # noqa: ERA001
    voltage_complex = current_value / admittance_safe

    # 計算結果のクランプ（入力値で極小・極大だった要素に対応）
    if np.any(input_extreme_mask):
        voltage_magnitude = np.abs(voltage_complex)
        voltage_phase = np.angle(voltage_complex)
        # 極小アドミタンスの場合、電流の大きさに応じて電圧をクランプ
        # 極大電流 / 極小アドミタンス = 極大電圧（開放回路に近い）
        # 極小電流 / 極小アドミタンス = 極小電圧
        current_magnitude = np.abs(current_value)
        voltage_magnitude_clamped = np.where(
            admittance_too_small & (current_magnitude >= max_mag),
            max_mag,
            voltage_magnitude,
        )
        voltage_magnitude_clamped = np.where(
            admittance_too_small & (current_magnitude <= eps),
            eps,
            voltage_magnitude_clamped,
        )
        # その他の極小・極大値の処理
        voltage_magnitude_clamped = np.where(
            input_extreme_mask & (voltage_magnitude_clamped <= eps),
            eps,
            voltage_magnitude_clamped,
        )
        voltage_magnitude_clamped = np.where(
            input_extreme_mask & (voltage_magnitude_clamped >= max_mag),
            max_mag,
            voltage_magnitude_clamped,
        )
        voltage_complex = voltage_magnitude_clamped * np.exp(1j * voltage_phase)
    # 計算結果のDTOを作成して基本単位を取得
    voltage_result = ArrayComplexVoltageDto(value=voltage_complex, unit="V")
    base_unit = voltage_result.to_base_unit().unit

    return ArrayComplexVoltageDto(value=voltage_complex, unit=base_unit)


def calculate_current_from_voltage_and_impedance(
    voltage: ArrayComplexVoltageDto,
    impedance: ArrayComplexImpedanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """電圧とインピーダンスから電流を計算する（オームの法則）。

    計算式: I = V / Z

    Args:
        voltage: 電圧配列DTO
        impedance: インピーダンス配列DTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: 電流DTO（単位: A）

    Raises:
        ValueError: 電圧とインピーダンスの配列形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（電圧またはインピーダンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    # 単位を基本単位に変換
    voltage_base = voltage.to_base_unit()
    impedance_base = impedance.to_base_unit()

    voltage_shape = voltage_base.value.shape
    impedance_shape = impedance_base.value.shape

    # 電圧とインピーダンスの形状が完全に一致することを確認
    if voltage_shape != impedance_shape:
        raise ValueError(
            "電圧とインピーダンスの配列形状が一致しません: "
            f"voltage shape={voltage_shape}, "
            f"impedance shape={impedance_shape}"
        )

    # 入力値の検証（極小・極大の位置を記録）
    voltage_value = voltage_base.value
    voltage_magnitude = np.abs(voltage_value)
    voltage_too_small = voltage_magnitude <= eps
    voltage_too_large = ~np.isfinite(voltage_value) | (
        voltage_magnitude >= max_mag
    )
    input_extreme_mask = voltage_too_small | voltage_too_large

    impedance_value = impedance_base.value
    impedance_magnitude = np.abs(impedance_value)
    impedance_too_small = impedance_magnitude <= eps
    impedance_too_large = ~np.isfinite(impedance_value) | (
        impedance_magnitude >= max_mag
    )
    input_extreme_mask = (
        input_extreme_mask | impedance_too_small | impedance_too_large
    )

    if np.any(input_extreme_mask):
        record_numerical_stability_event(
            event_codes.OHMS_LAW_CURRENT_IMPEDANCE_INPUT_EXTREME,
        )

    # ゼロ除算を避けるため、インピーダンスが極小の場合はクランプ
    impedance_phase = np.angle(impedance_value)
    impedance_magnitude_safe = np.where(
        impedance_too_small, eps, impedance_magnitude
    )
    impedance_safe = impedance_magnitude_safe * np.exp(1j * impedance_phase)

    # オームの法則: I = V / Z  # noqa: ERA001
    # 電流計算（複素数）
    current_complex = voltage_value / impedance_safe

    # 計算結果のクランプ（入力値で極小・極大だった要素に対応）
    if np.any(input_extreme_mask):
        current_magnitude = np.abs(current_complex)
        current_phase = np.angle(current_complex)
        voltage_magnitude = np.abs(voltage_value)
        # 極小電圧×極小インピーダンスの場合、中間値（約1.0）になる
        both_small_mask = voltage_too_small & impedance_too_small
        # 極大電圧×極大インピーダンスの場合、中間値（約1.0）になる
        both_large_mask = voltage_too_large & impedance_too_large
        # 極小インピーダンスの場合、電圧が極小でない場合は電流をmax_magにクランプ（短絡に近い）
        current_magnitude_clamped = np.where(
            impedance_too_small & ~voltage_too_small, max_mag, current_magnitude
        )
        # 極大インピーダンスの場合、電圧の大きさに応じて電流をクランプ
        # 極大電圧 / 極大インピーダンス = 中間値（約1.0）
        # 極小電圧 / 極大インピーダンス = 極小電流
        current_magnitude_clamped = np.where(
            impedance_too_large & ~voltage_too_large,
            eps,
            current_magnitude_clamped,
        )
        # 極小電圧×極小インピーダンス、極大電圧×極大インピーダンスの場合、中間値（約1.0）を保持
        # その他の極小・極大値の処理（極小×極小、極大×極大は除外）
        other_extreme_mask = (
            input_extreme_mask & ~both_small_mask & ~both_large_mask
        )
        current_magnitude_clamped = np.where(
            other_extreme_mask & (current_magnitude_clamped <= eps),
            eps,
            current_magnitude_clamped,
        )
        current_magnitude_clamped = np.where(
            other_extreme_mask & (current_magnitude_clamped >= max_mag),
            max_mag,
            current_magnitude_clamped,
        )
        current_complex = current_magnitude_clamped * np.exp(1j * current_phase)
    # 計算結果のDTOを作成して基本単位を取得
    current_result = ArrayComplexCurrentDto(value=current_complex, unit="A")
    base_unit = current_result.to_base_unit().unit

    return ArrayComplexCurrentDto(value=current_complex, unit=base_unit)


def calculate_current_from_voltage_and_admittance(
    voltage: ArrayComplexVoltageDto,
    admittance: ArrayComplexAdmittanceDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """電圧とアドミタンスから電流を計算する（オームの法則）。

    計算式: I = V * Y

    Args:
        voltage: 電圧配列DTO
        admittance: アドミタンス配列DTO
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: 電流DTO（単位: A）

    Raises:
        ValueError: 電圧とアドミタンスの配列形状が一致しない場合

    Warns:
        RuntimeWarning: 入力値（電圧またはアドミタンス）に極小または極大の要素がある場合。
            計算結果の対応する要素をクランプします。
    """
    # 単位を基本単位に変換
    voltage_base = voltage.to_base_unit()
    admittance_base = admittance.to_base_unit()

    voltage_shape = voltage_base.value.shape
    admittance_shape = admittance_base.value.shape

    # 電圧とアドミタンスの形状が完全に一致することを確認
    if voltage_shape != admittance_shape:
        raise ValueError(
            "電圧とアドミタンスの配列形状が一致しません: "
            f"voltage shape={voltage_shape}, "
            f"admittance shape={admittance_shape}"
        )

    # 入力値の検証（極小・極大の位置を記録）
    voltage_value = voltage_base.value
    voltage_magnitude = np.abs(voltage_value)
    voltage_too_small = voltage_magnitude <= eps
    voltage_too_large = ~np.isfinite(voltage_value) | (
        voltage_magnitude >= max_mag
    )
    input_extreme_mask = voltage_too_small | voltage_too_large

    admittance_value = admittance_base.value
    admittance_magnitude = np.abs(admittance_value)
    admittance_too_small = admittance_magnitude <= eps
    admittance_too_large = ~np.isfinite(admittance_value) | (
        admittance_magnitude >= max_mag
    )
    input_extreme_mask = (
        input_extreme_mask | admittance_too_small | admittance_too_large
    )

    if np.any(input_extreme_mask):
        record_numerical_stability_event(
            event_codes.OHMS_LAW_CURRENT_ADMITTANCE_INPUT_EXTREME,
        )

    # ゼロ除算を避けるため、アドミタンスが極小の場合はクランプ
    admittance_phase = np.angle(admittance_value)
    admittance_magnitude_safe = np.where(
        admittance_too_small, eps, admittance_magnitude
    )
    admittance_safe = admittance_magnitude_safe * np.exp(1j * admittance_phase)

    # オームの法則: I = V * Y  # noqa: ERA001
    # 電流計算（複素数）
    current_complex = voltage_value * admittance_safe

    # 計算結果のクランプ（入力値で極小・極大だった要素に対応）
    if np.any(input_extreme_mask):
        current_magnitude = np.abs(current_complex)
        current_phase = np.angle(current_complex)
        # 極小アドミタンスの場合、電流をepsにクランプ（開放回路に近い）
        current_magnitude_clamped = np.where(
            admittance_too_small, eps, current_magnitude
        )
        # 極大アドミタンスの場合、電流をmax_magにクランプ（短絡に近い）
        current_magnitude_clamped = np.where(
            admittance_too_large, max_mag, current_magnitude_clamped
        )
        # その他の極小・極大値の処理
        current_magnitude_clamped = np.where(
            input_extreme_mask & (current_magnitude_clamped <= eps),
            eps,
            current_magnitude_clamped,
        )
        current_magnitude_clamped = np.where(
            input_extreme_mask & (current_magnitude_clamped >= max_mag),
            max_mag,
            current_magnitude_clamped,
        )
        current_complex = current_magnitude_clamped * np.exp(1j * current_phase)
    # 計算結果のDTOを作成して基本単位を取得
    current_result = ArrayComplexCurrentDto(value=current_complex, unit="A")
    base_unit = current_result.to_base_unit().unit

    return ArrayComplexCurrentDto(value=current_complex, unit=base_unit)
