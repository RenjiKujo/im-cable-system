"""三相電力変換計算ロジック（ドメイン層）。

このモジュールは、一相の電力から三相回路の電力に変換する処理を提供します。

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する

本実装では、入力として与えられる一相電力 `S_1phase` を
「任意の定義（相電圧/相電流、線間電圧/線電流など）に基づく
一相分の複素電力」とみなし、その3倍を三相総電力とします。

平衡三相回路の典型的な関係式:
    S_3phase = 3 × S_1phase

ここで、S_1phase がどのような電圧・電流から導かれているか
（相/線、Y/Δ結線、位相シフトなど）は本関数では扱わず、
呼び出し元で `ArrayComplexPowerDto` を構成する際に統一しておくことを前提とします。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)

# 三相回路の相数
_PHASE_COUNT: float = 3.0
# √3の値（線間電圧・線電流から三相電力を計算する際の係数）
_SQRT_3: float = np.sqrt(3.0)


def to_three_phase_power_from_phase(
    single_phase_power_dto: ArrayComplexPowerDto,
) -> ArrayComplexPowerDto:
    """一相電力を三相電力に変換する（相電圧・電流から計算した場合）。

    一相の電力から三相回路の総電力を計算します。
    計算式: S_3phase = S_1phase × 3

    Args:
        single_phase_power_dto: 一相電力DTO（複素数配列）。
            配列の次元数は任意（例: 3次配列: slip × frequency × power）。

    Returns:
        ArrayComplexPowerDto: 三相電力DTO（単位: VA、複素数配列）。
            入力と同じ次元数の配列を返す。
    """
    # 基本単位に変換してから計算
    single_phase_base = single_phase_power_dto.to_base_unit()
    three_phase_value = single_phase_base.value * _PHASE_COUNT

    return ArrayComplexPowerDto(value=three_phase_value, unit="VA")


def to_three_phase_power_from_line(
    line_voltage: ArrayComplexVoltageDto,
    line_current: ArrayComplexCurrentDto,
) -> ArrayComplexPowerDto:
    """線間電圧と線電流から三相電力を計算する。

    線間電圧 V_line と線電流 I_line から三相回路の総電力を計算します。
    計算式: S_3phase = √3 × V_line × I_line_conj

    この式は平衡三相回路（スター結線・デルタ結線の両方）において成立します。

    Args:
        line_voltage: 線間電圧DTO（複素数配列）。
            配列の次元数は任意（例: 3次配列: slip × frequency × line_voltage）。
        line_current: 線電流DTO（複素数配列）。
            配列の次元数は任意（例: 3次配列: slip × frequency × line_current）。

    Returns:
        ArrayComplexPowerDto: 三相電力DTO（単位: VA、複素数配列）。
            入力と同じ次元数の配列を返す。

    Raises:
        ValueError: 線間電圧と線電流の配列形状が一致しない場合

    Notes:
        - 平衡三相回路では、スター結線・デルタ結線のどちらでも
          この式が成立します。
        - 複素電力の計算では、電流の共役複素数を使用します。
    """
    line_voltage_base = line_voltage.to_base_unit()
    line_current_base = line_current.to_base_unit()

    line_voltage_shape = line_voltage_base.value.shape
    line_current_shape = line_current_base.value.shape

    # 線間電圧と線電流の形状が完全に一致することを確認
    if line_voltage_shape != line_current_shape:
        raise ValueError(
            "線間電圧と線電流の配列形状が一致しません: "
            f"line_voltage shape={line_voltage_shape}, "
            f"line_current shape={line_current_shape}"
        )

    # 三相電力計算: S_3phase = √3 × V_line × I_line_conj
    three_phase_value = (
        _SQRT_3
        * line_voltage_base.value
        * np.conjugate(line_current_base.value)
    )

    return ArrayComplexPowerDto(value=three_phase_value, unit="VA")
