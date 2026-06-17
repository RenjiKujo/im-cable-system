"""機器特性計算ロジック（ドメイン層）。

このモジュールは、機器特性値（効率・力率・トルク・回転速度）の純粋計算
ロジックを提供する。

含まれる計算:
    - 効率 (calculate_efficiency): IM・ケーブル・回転負荷機械等
    - 力率 (calculate_power_factor): 複素電力を持つ系全般
    - トルク (calculate_torque): 回転機械全般
    - 回転速度 (calculate_rotational_speed): 誘導電動機（IM）特有

特徴:
    - 入力・出力はすべて DTO（``physical_quantity`` DTO）。
    - アルゴリズム層から利用される純粋計算ロジックの集約点。
    - 分母ガード（``eps``）は Config 由来の値をアルゴリズム層が注入する。
      Domain 側で既定値・共通定数を持たない。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayComplexPowerDto,
    ArrayEfficiencyDto,
    ArrayFrequencyDto,
    ArrayPowerFactorDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def calculate_efficiency(
    input_active_power: ArrayActivePowerDto,
    output_active_power: ArrayActivePowerDto,
    *,
    eps: float,
) -> ArrayEfficiencyDto:
    """有効電力DTOから効率DTOを計算する。

    計算式:
        eta = P_out / P_in

    入力電力の大きさが ``eps`` 以下（近接ゼロ）の要素は、効率を計算できない
    ため 0 を返す。これは電圧電流系の「極値入力 → 出力を eps 基準に丸める」
    方針と整合させるための分母ガードである。

    Args:
        input_active_power: 入力有効電力配列DTO[W, kW, MW]。
        output_active_power: 出力有効電力配列DTO[W, kW, MW]。
        eps: 近接ゼロ判定のしきい値（Config 由来）。
            ``abs(P_in) <= eps`` の要素は効率 0 とする。

    Returns:
        ArrayEfficiencyDto: 効率配列DTO（単位: 無次元"-"）。
            入力電力が近接ゼロの要素は 0 になる。

    Raises:
        ValueError: 入力電力と出力電力の配列形状が一致しない場合、
            効率が1.0超または負になる場合（物理的にあり得ない）。
    """
    input_base = input_active_power.to_base_unit().get_value()
    output_base = output_active_power.to_base_unit().get_value()

    input_shape = input_base.shape
    output_shape = output_base.shape
    if input_shape != output_shape:
        raise ValueError(
            "入力電力と出力電力の配列形状が一致しません: "
            f"input_active_power shape={input_shape}, "
            f"output_active_power shape={output_shape}"
        )

    efficiency = np.zeros_like(input_base, dtype=np.float64)
    np.divide(
        output_base,
        input_base,
        out=efficiency,
        where=(np.abs(input_base) > eps),
    )

    efficiency_over_one = efficiency > 1.0
    if np.any(efficiency_over_one):
        raise ValueError(
            "効率が1.0を超える値が計算されました。"
            "入力電力より出力電力が大きい場合、物理的にあり得ない状況です。"
            "入力電力と出力電力の値を確認してください。"
        )

    efficiency_negative = efficiency < 0.0
    if np.any(efficiency_negative):
        raise ValueError(
            "効率が負の値が計算されました。"
            "入力電力と出力電力の値を確認してください。"
        )

    return ArrayEfficiencyDto(value=efficiency, unit="-")


def calculate_power_factor(
    complex_power: ArrayComplexPowerDto,
    *,
    eps: float,
) -> ArrayPowerFactorDto:
    """複素電力配列から力率配列を計算する。

    計算式:
        pf = Re(S) / |S|

    皮相電力 ``|S|`` が ``eps`` 以下（近接ゼロ）の要素は力率を計算できない
    ため、分母を ``eps`` にクランプする（極小ガード ``abs(x) <= eps``）。
    力率は比であり単位に依存しないため、入力単位のまま計算する。

    Args:
        complex_power: 複素電力配列DTO。
        eps: 近接ゼロ判定のしきい値（Config 由来）。Domain 側で既定値を
            持たない。``abs(S) <= eps`` の要素は分母を ``eps`` にクランプする。

    Returns:
        ArrayPowerFactorDto: 力率配列DTO（単位: 無次元"-"）。

    Note:
        皮相電力が近接ゼロの要素がある場合、数値安定化イベント
        ``APPARENT_POWER_NEAR_ZERO_POWER_FACTOR`` を記録する。
    """
    complex_value = complex_power.get_value()
    active_power = np.real(complex_value)
    apparent_power = np.abs(complex_value)

    small_mask = apparent_power <= eps
    if np.any(small_mask):
        record_numerical_stability_event(
            event_codes.APPARENT_POWER_NEAR_ZERO_POWER_FACTOR,
        )
    apparent_safe = np.where(small_mask, eps, apparent_power)
    power_factor = active_power / apparent_safe
    return ArrayPowerFactorDto(value=power_factor, unit="-")


def calculate_torque(
    output_power: ArrayActivePowerDto,
    rotational_speed: ArrayRotationalSpeedDto,
    *,
    eps: float,
) -> ArrayTorqueDto:
    """トルク配列を計算する。

    計算式:
        トルク[Nm] = 出力電力[W] / 角速度[rad/s]

    角速度は回転速度DTOを基本単位（rad/s）に正規化した値を用いる。

    角速度がゼロ（または極小）の場合、トルクは計算できないためNaNを返す。
    回転していない場合でもトルクが存在する可能性があるが、この計算式では
    角速度がゼロの場合にトルクを計算できないことに注意。

    Args:
        output_power: 出力有効電力配列DTO。
        rotational_speed: 回転速度配列DTO。
        eps: 近接ゼロ判定のしきい値（Config 由来）。

    Returns:
        ArrayTorqueDto: トルク配列DTO（基本単位: Nm）。
            角速度がゼロの要素はNaNになる。

    Raises:
        ValueError: 出力電力と回転速度の配列形状が一致しない場合。

    Note:
        角速度がゼロまたは極小の要素がある場合、
        数値安定化イベント ``OMEGA_NEAR_ZERO_TORQUE`` を記録する。
    """
    output_power_w = output_power.to_base_unit().get_value()
    omega = rotational_speed.to_base_unit().get_value()

    power_shape = output_power_w.shape
    omega_shape = omega.shape
    if power_shape != omega_shape:
        raise ValueError(
            "出力電力と回転速度の配列形状が一致しません: "
            f"output_power shape={power_shape}, "
            f"rotational_speed shape={omega_shape}"
        )

    omega_zero_or_small = np.abs(omega) <= eps

    if np.any(omega_zero_or_small):
        record_numerical_stability_event(event_codes.OMEGA_NEAR_ZERO_TORQUE)

    torque_nm = np.full_like(omega, np.nan, dtype=np.float64)
    np.divide(
        output_power_w,
        omega,
        out=torque_nm,
        where=~omega_zero_or_small,
    )

    return ArrayTorqueDto(value=torque_nm, unit="Nm")


def calculate_rotational_speed(
    slip_array: ArraySlipDto,
    frequency_array: ArrayFrequencyDto,
    poles: int,
) -> ArrayRotationalSpeedDto:
    """誘導電動機の回転速度配列を計算する。

    計算ステップ:
        1. スリップと周波数を基本単位に正規化
        2. 同期速度を計算: n_s [rpm] = 120 * f[Hz] / poles
        3. 実回転速度を計算: n[rpm] = (1 - s) * n_s
        4. DTOの``to_base_unit``で rad/s に変換

    Args:
        slip_array: スリップ配列DTO。
        frequency_array: 周波数配列DTO。
        poles: 極数。正の偶数である必要がある（誘導電動機の物理契約）。

    Returns:
        ArrayRotationalSpeedDto: 回転速度配列DTO（基本単位: rad/s）。

    Raises:
        ValueError: スリップと周波数の配列形状が一致しない場合、または
            ``poles`` が正の偶数でない場合。
    """
    if poles <= 0 or poles % 2 != 0:
        raise ValueError(
            f"polesは正の偶数である必要がありますが、{poles}を受け取りました。"
        )

    slip_base = slip_array.to_base_unit().get_value()
    freq_base = frequency_array.to_base_unit().get_value()

    slip_shape = slip_base.shape
    freq_shape = freq_base.shape
    if slip_shape != freq_shape:
        raise ValueError(
            "スリップと周波数の配列形状が一致しません: "
            f"slip shape={slip_shape}, "
            f"frequency shape={freq_shape}"
        )

    rotational_speed_rpm = (1.0 - slip_base) * (120.0 * freq_base) / poles

    rotational_speed_dto = ArrayRotationalSpeedDto(
        value=rotational_speed_rpm,
        unit="rpm",
    )
    return rotational_speed_dto.to_base_unit()
