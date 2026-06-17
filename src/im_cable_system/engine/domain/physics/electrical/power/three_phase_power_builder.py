"""三相電力構築ユーティリティ（ドメイン層）。

このモジュールは、アルゴリズム層で頻出する「相量（1相分）→3相合計」変換や、
dict構造の電圧・電流から電力dictを構築する処理を提供します。

NOTE:
    - 本モジュールは純粋計算ロジック（DTO入力/DTO出力）とし、ログ出力等は行いません。
    - 外部からの利用は `im_cable_system.engine.domain.physics.electrical` から import してください。
"""

from __future__ import annotations

from im_cable_system.engine.domain.physics.electrical.power.power_calculator import (  # noqa: E501
    add_power,
    power_from_voltage_and_current,
)
from im_cable_system.engine.domain.physics.electrical.power.three_phase_power_converter import (  # noqa: E501
    to_three_phase_power_from_phase,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)


def three_phase_power_from_voltage_and_current_phase(
    *,
    voltage: ArrayComplexVoltageDto,
    current: ArrayComplexCurrentDto,
) -> ArrayComplexPowerDto:
    """相量（1相分）の電圧・電流から3相合計複素電力を計算する。

    計算手順:
      1. 1相分の複素電力: S_1phase = V * I_conj
      2. 3相合計へ変換: S_total = 3 * S_1phase

    Args:
        voltage: 相電圧DTO（複素数配列）。
        current: 相電流DTO（複素数配列）。

    Returns:
        ArrayComplexPowerDto: 3相合計複素電力DTO。
    """
    single_phase_power = power_from_voltage_and_current(
        voltage=voltage, current=current
    )
    return to_three_phase_power_from_phase(
        single_phase_power_dto=single_phase_power
    )


def three_phase_power_dict_from_voltage_and_current_phase_dict(
    *,
    voltage_dict: dict[str, ArrayComplexVoltageDto],
    current_dict: dict[str, ArrayComplexCurrentDto],
) -> dict[str, ArrayComplexPowerDto]:
    """dict形式の相電圧・相電流から、3相合計複素電力dictを構築する。

    Args:
        voltage_dict: 相電圧の辞書（key -> ArrayComplexVoltageDto）。
        current_dict: 相電流の辞書（key -> ArrayComplexCurrentDto）。

    Returns:
        dict[str, ArrayComplexPowerDto]: 3相合計複素電力の辞書。

    Raises:
        ValueError: voltage_dict と current_dict のキー集合が一致しない場合。
    """
    if set(voltage_dict.keys()) != set(current_dict.keys()):
        raise ValueError(
            "電圧dictと電流dictのキーが一致しません: "
            f"voltage_keys={sorted(voltage_dict.keys())}, "
            f"current_keys={sorted(current_dict.keys())}"
        )

    power_dict: dict[str, ArrayComplexPowerDto] = {}
    for key, voltage in voltage_dict.items():
        power_dict[key] = three_phase_power_from_voltage_and_current_phase(
            voltage=voltage,
            current=current_dict[key],
        )
    return power_dict


def sum_power_dict_values(
    *,
    power_dicts: list[dict[str, ArrayComplexPowerDto]],
) -> ArrayComplexPowerDto:
    """複数の電力dictに含まれるvalueを全て合算する。

    Args:
        power_dicts: 電力dictのリスト。

    Returns:
        ArrayComplexPowerDto: 合算結果。

    Raises:
        ValueError: 合算対象が空の場合。
    """
    total_power: ArrayComplexPowerDto | None = None
    for power_dict in power_dicts:
        for power in power_dict.values():
            total_power = (
                power
                if total_power is None
                else add_power(power1=total_power, power2=power)
            )
    if total_power is None:
        raise ValueError("損失電力の合計対象が空です。")
    return total_power
