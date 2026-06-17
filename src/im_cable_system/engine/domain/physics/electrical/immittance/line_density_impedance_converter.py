"""線密度からインピーダンス変換計算ロジック（ドメイン層）。

このモジュールは、線密度パラメータ（単位長さあたりの値）と長さから
実際のインピーダンスを計算する処理を提供します。

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
    - ケーブルや伝送線路などの分布定数回路の計算に適用可能
"""

from __future__ import annotations

from im_cable_system.engine.domain.physics.electrical.immittance.impedance_combiner import (  # noqa: E501
    combine_impedance_parallel,
    combine_impedance_series,
)
from im_cable_system.engine.domain.physics.electrical.immittance.impedance_converter import (  # noqa: E501
    impedance_from_capacitance_and_frequency,
    impedance_from_inductance_and_frequency,
    impedance_from_resistance_and_frequency,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatCapacitanceDto,
    FloatCapacitancePerLengthDto,
    FloatInductanceDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


def impedance_from_conductor_line_density(
    resistance_per_length: FloatResistancePerLengthDto,
    inductance_per_length: FloatInductancePerLengthDto,
    length: FloatLengthDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """導線インピーダンスを線密度から計算する。

    抵抗とインダクタンスの線密度と長さから、実際の導線インピーダンスを計算します。
    抵抗とインダクタンスは直列接続として扱われます。

    計算式:
        R_total = R_per_length × length
        L_total = L_per_length × length
        Z = R_total + jωL_total

    Args:
        resistance_per_length: 抵抗線密度DTO（例: Ω/m）。
        inductance_per_length: インダクタンス線密度DTO（例: H/m）。
        length: 長さDTO。
        frequency: 周波数配列DTO。
        eps: 近接ゼロ判定のしきい値（Config 由来）。
            内部のインピーダンス変換・直列合成のクランプに伝播する。
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）。同上。

    Returns:
        ArrayComplexImpedanceDto: 導線インピーダンスDTO。
            配列形状はfrequencyと同じ形状になります。

    Raises:
        ValueError: 抵抗線密度、インダクタンス線密度、または長さが負の場合。
    """
    # 線密度を基本単位に変換
    resistance_per_length_base = resistance_per_length.to_base_unit()
    inductance_per_length_base = inductance_per_length.to_base_unit()
    length_base = length.to_base_unit()

    # 物理的にあり得ない負の値のチェック
    if resistance_per_length_base.value < 0:
        raise ValueError(
            f"抵抗線密度が負の値です: {resistance_per_length_base.value} Ω/m. "
            "抵抗は常に正の値である必要があります。"
        )
    if inductance_per_length_base.value < 0:
        raise ValueError(
            f"インダクタンス線密度が負の値です: {inductance_per_length_base.value} H/m. "
            "自己インダクタンス線密度は常に正の値である必要があります。"
        )
    if length_base.value <= 0:
        raise ValueError(
            f"長さが0以下です: {length_base.value} m. "
            "長さは正の値である必要があります。"
        )

    # 長さを掛けて実際の値に変換
    resistance_total = resistance_per_length_base.value * length_base.value
    inductance_total = inductance_per_length_base.value * length_base.value

    # 抵抗成分のインピーダンス
    resistance_dto = FloatResistanceDto(value=resistance_total, unit="Ω")
    resistance_impedance = impedance_from_resistance_and_frequency(
        resistance=resistance_dto,
        frequency=frequency,
        eps=eps,
        max_mag=max_mag,
    )

    # インダクタンス成分のインピーダンス
    inductance_dto = FloatInductanceDto(value=inductance_total, unit="H")
    inductance_impedance = impedance_from_inductance_and_frequency(
        inductance=inductance_dto,
        frequency=frequency,
        eps=eps,
        max_mag=max_mag,
    )

    # 直列合成（R + jωL）
    return combine_impedance_series(
        impedance1=resistance_impedance,
        impedance2=inductance_impedance,
        eps=eps,
        max_mag=max_mag,
    )


def impedance_from_ground_line_density(
    resistance_length: FloatResistanceLengthDto,
    capacitance_per_length: FloatCapacitancePerLengthDto,
    length: FloatLengthDto,
    frequency: ArrayFrequencyDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexImpedanceDto:
    """アースインピーダンスを線密度から計算する。

    抵抗長積とキャパシタンス線密度と長さから、実際のアースインピーダンスを計算します。
    抵抗とキャパシタンスは並列接続として扱われます。

    計算式:
        R_total = (R×length) / length = R（抵抗長積から抵抗値を取得）
        C_total = C_per_length × length
        Z = R_total || (1 / jωC_total)

    Args:
        resistance_length: 抵抗長積DTO（例: Ω·m）。
            これは抵抗と長さの積であり、長さで割ることで実際の抵抗値を得ます。
        capacitance_per_length: キャパシタンス線密度DTO（例: F/m）。
        length: 長さDTO。
        frequency: 周波数配列DTO。
        eps: 近接ゼロ判定のしきい値（Config 由来）。
            内部のインピーダンス変換・並列合成のクランプに伝播する。
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）。同上。

    Returns:
        ArrayComplexImpedanceDto: アースインピーダンスDTO。
            配列形状はfrequencyと同じ形状になります。

    Raises:
        ValueError: 抵抗長積、キャパシタンス線密度、または長さが負の場合。

    Note:
        キャパシタンス線密度=0（完全絶縁）や抵抗長積=0（地絡）などの極端値でも、
        内部の ``impedance_from_capacitance_and_frequency`` /
        ``combine_impedance_parallel`` が eps/max_mag でクランプするため発散しない。
    """
    # 線密度を基本単位に変換
    resistance_length_base = resistance_length.to_base_unit()
    capacitance_per_length_base = capacitance_per_length.to_base_unit()
    length_base = length.to_base_unit()

    # 物理的にあり得ない負の値のチェック
    if resistance_length_base.value < 0:
        raise ValueError(
            f"抵抗長積が負の値です: {resistance_length_base.value} Ω·m. "
            "抵抗長積は常に正の値である必要があります。"
        )
    if capacitance_per_length_base.value < 0:
        raise ValueError(
            f"キャパシタンス線密度が負の値です: {capacitance_per_length_base.value} F/m. "
            "キャパシタンス線密度は常に正の値である必要があります。"
        )
    if length_base.value <= 0:
        raise ValueError(
            f"長さが0以下です: {length_base.value} m. "
            "長さは正の値である必要があります。"
        )

    # 抵抗はΩ·mを長さで割ることで実際の抵抗値を得る
    # キャパシタンスはF/mに長さを掛けることで実際の容量を得る
    resistance_total = resistance_length_base.value / length_base.value
    capacitance_total = capacitance_per_length_base.value * length_base.value

    # 抵抗成分のインピーダンス
    resistance_dto = FloatResistanceDto(value=resistance_total, unit="Ω")
    resistance_impedance = impedance_from_resistance_and_frequency(
        resistance=resistance_dto,
        frequency=frequency,
        eps=eps,
        max_mag=max_mag,
    )

    # キャパシタンス成分のインピーダンス
    capacitance_dto = FloatCapacitanceDto(value=capacitance_total, unit="F")
    capacitance_impedance = impedance_from_capacitance_and_frequency(
        capacitance=capacitance_dto,
        frequency=frequency,
        eps=eps,
        max_mag=max_mag,
    )

    # 並列合成（R || C）
    return combine_impedance_parallel(
        impedance1=resistance_impedance,
        impedance2=capacitance_impedance,
        eps=eps,
        max_mag=max_mag,
    )
