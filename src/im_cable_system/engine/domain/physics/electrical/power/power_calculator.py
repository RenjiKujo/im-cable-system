"""電力計算ロジック（ドメイン層）。

このモジュールは、電力計算を提供します。
（電圧・電流から電力、電圧・アドミタンスから電力、電流・インピーダンスから電力）

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
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)


def power_from_voltage_and_current(
    voltage: ArrayComplexVoltageDto,
    current: ArrayComplexCurrentDto,
) -> ArrayComplexPowerDto:
    """電圧と電流から電力DTOを生成する。

    電圧 V と電流 I から複素電力 S を計算します。
    計算式: S = V * I_conj

    Args:
        voltage: 電圧配列DTO
        current: 電流配列DTO

    Returns:
        ArrayComplexPowerDto: 電力DTO（単位: VA）

    Raises:
        ValueError: 電圧と電流の配列形状が一致しない場合
    """
    voltage_base = voltage.to_base_unit()
    current_base = current.to_base_unit()

    voltage_shape = voltage_base.value.shape
    current_shape = current_base.value.shape

    # 電圧と電流の形状が完全に一致することを確認
    if voltage_shape != current_shape:
        raise ValueError(
            "電圧と電流の配列形状が一致しません: "
            f"voltage shape={voltage_shape}, "
            f"current shape={current_shape}"
        )

    power_value = voltage_base.value * np.conjugate(current_base.value)
    return ArrayComplexPowerDto(value=power_value, unit="VA")


def power_from_voltage_and_admittance(
    voltage: ArrayComplexVoltageDto,
    admittance: ArrayComplexAdmittanceDto,
) -> ArrayComplexPowerDto:
    """電圧とアドミタンスから電力DTOを生成する。

    電圧 V とアドミタンス Y から複素電力 S を計算します。
    計算式: S = V * conj(V * Y) = V * V_conj * conj(Y)

    Args:
        voltage: 電圧配列DTO
        admittance: アドミタンス配列DTO

    Returns:
        ArrayComplexPowerDto: 電力DTO（単位: VA）

    Raises:
        ValueError: 電圧とアドミタンスの配列形状が一致しない場合
    """
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

    current_value = voltage_base.value * admittance_base.value
    power_value = voltage_base.value * np.conjugate(current_value)
    return ArrayComplexPowerDto(value=power_value, unit="VA")


def power_from_current_and_impedance(
    current: ArrayComplexCurrentDto,
    impedance: ArrayComplexImpedanceDto,
) -> ArrayComplexPowerDto:
    """電流とインピーダンスから電力DTOを生成する。

    電流 I とインピーダンス Z から複素電力 S を計算します。
    計算式: S = Z * I * I_conj

    Args:
        current: 電流配列DTO
        impedance: インピーダンス配列DTO

    Returns:
        ArrayComplexPowerDto: 電力DTO（単位: VA）

    Raises:
        ValueError: 電流とインピーダンスの配列形状が一致しない場合
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

    s_value = impedance_base.value * current_base.value
    power_value = s_value * np.conjugate(current_base.value)
    return ArrayComplexPowerDto(value=power_value, unit="VA")


def add_power(
    power1: ArrayComplexPowerDto,
    power2: ArrayComplexPowerDto,
) -> ArrayComplexPowerDto:
    """2つの電力DTOを加算する。

    2つの電力を加算します。
    計算式: S_total = S1 + S2
    単位が異なる場合は、両方を基本単位（VA）に変換してから加算します。

    Args:
        power1: 第1の電力DTO
        power2: 第2の電力DTO

    Returns:
        ArrayComplexPowerDto: 加算された電力DTO（単位: VA）

    Raises:
        ValueError: 配列の形状が一致しない場合

    Notes:
        - 戻りのunitは常に "VA"。
        - 入力配列は同一形状である必要がある（ブロードキャストは行わない）。
    """
    if power1.value.shape != power2.value.shape:
        raise ValueError(
            f"電力配列の形状が一致しません: "
            f"{power1.value.shape} vs {power2.value.shape}"
        )

    # 単位を統一してから加算
    power1_base = power1.to_base_unit()
    power2_base = power2.to_base_unit()

    combined_value = power1_base.value + power2_base.value
    return ArrayComplexPowerDto(value=combined_value, unit="VA")


def subtract_power(
    power1: ArrayComplexPowerDto,
    power2: ArrayComplexPowerDto,
) -> ArrayComplexPowerDto:
    """2つの電力DTOを減算する（power1 - power2）。

    計算式: S_result = S1 - S2
    単位が異なる場合は、両方を基本単位（VA）に変換してから減算します。

    Args:
        power1: 被減数の電力DTO
        power2: 減数の電力DTO

    Returns:
        ArrayComplexPowerDto: 減算された電力DTO（単位: VA）

    Raises:
        ValueError: 配列の形状が一致しない場合

    Notes:
        - 戻りのunitは常に "VA"。
        - 入力配列は同一形状である必要がある（ブロードキャストは行わない）。
        - ``add_power`` と対になる関数（IM 軸出力 = 二次負荷電力 - 軸出力控除 の
          計算で使う）。
    """
    if power1.value.shape != power2.value.shape:
        raise ValueError(
            f"電力配列の形状が一致しません: "
            f"{power1.value.shape} vs {power2.value.shape}"
        )

    # 単位を統一してから減算
    power1_base = power1.to_base_unit()
    power2_base = power2.to_base_unit()

    combined_value = power1_base.value - power2_base.value
    return ArrayComplexPowerDto(value=combined_value, unit="VA")
