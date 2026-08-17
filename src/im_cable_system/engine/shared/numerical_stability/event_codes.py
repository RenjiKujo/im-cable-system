"""数値安定化イベントコード（シミュレーション結果メタ用のキー）。

ルーチン・クランプや近傍検知をイベント種別ごとにカウントし、
:func:`record_numerical_stability_event` に渡す。

Notes:
    コード値はログ・DTOに載るため、機密にならない英語 snake_case とする。
"""

from __future__ import annotations

# 力率計算時の皮相電力近傍
APPARENT_POWER_NEAR_ZERO_POWER_FACTOR = "apparent_power_near_zero_power_factor"

# トルク計算で角速度が極小（NaN になる要素あり）
OMEGA_NEAR_ZERO_TORQUE = "omega_near_zero_torque"

# domain: admittance_from_impedance / impedance_from_admittance 等
IMPEDANCE_TOO_SMALL_FOR_ADMITTANCE = "impedance_too_small_for_admittance"
IMPEDANCE_TOO_LARGE_FOR_ADMITTANCE = "impedance_too_large_for_admittance"
ADMITTANCE_TOO_SMALL_FOR_IMPEDANCE = "admittance_too_small_for_impedance"
ADMITTANCE_TOO_LARGE_FOR_IMPEDANCE = "admittance_too_large_for_impedance"
CONDUCTANCE_TOO_SMALL = "conductance_too_small"
CONDUCTANCE_TOO_LARGE = "conductance_too_large"

# impedance_converter（R/L/C 由来）
RESISTANCE_TOO_SMALL = "resistance_too_small"
RESISTANCE_TOO_LARGE = "resistance_too_large"
INDUCTANCE_TOO_SMALL = "inductance_too_small"
INDUCTANCE_TOO_LARGE = "inductance_too_large"
CAPACITANCE_TOO_SMALL = "capacitance_too_small"
CAPACITANCE_TOO_LARGE = "capacitance_too_large"

# admittance combiner / impedance combiner
ADMITTANCE_COMBINER_CLAMP = "admittance_combiner_clamp"
IMPEDANCE_COMBINER_CLAMP = "impedance_combiner_clamp"

# 相・線変換・結線（電圧・電流の極小・極大検知）
VOLTAGE_EXTREME_SMALL = "voltage_extreme_small"
VOLTAGE_EXTREME_LARGE = "voltage_extreme_large"
CURRENT_EXTREME_SMALL = "current_extreme_small"
CURRENT_EXTREME_LARGE = "current_extreme_large"

# キルヒホッフ・オーム
KIRCHHOFF_VOLTAGE_EXTREME_INPUT = "kirchhoff_voltage_extreme_input"
KIRCHHOFF_CURRENT_EXTREME_INPUT = "kirchhoff_current_extreme_input"
OHMS_LAW_CURRENT_IMPEDANCE_INPUT_EXTREME = (
    "ohms_law_current_impedance_input_extreme"
)
OHMS_LAW_CURRENT_ADMITTANCE_INPUT_EXTREME = (
    "ohms_law_current_admittance_input_extreme"
)
OHMS_LAW_VOLTAGE_IMPEDANCE_INPUT_EXTREME = (
    "ohms_law_voltage_impedance_input_extreme"
)
OHMS_LAW_VOLTAGE_ADMITTANCE_INPUT_EXTREME = (
    "ohms_law_voltage_admittance_input_extreme"
)

# algorithm: 二次イミタンス（スリップ極小マスク／負荷枝・全範囲）
SLIP_NEAR_ZERO_SECONDARY_LOAD_IMM = "slip_near_zero_secondary_load_immittance"
SLIP_NEAR_ZERO_SECONDARY_TOTAL_IMM = "slip_near_zero_secondary_total_immittance"
SLIP_NEAR_ZERO_SECONDARY_SKIN_EFFECT_LOAD = (
    "slip_near_zero_secondary_skin_effect_load"
)
SLIP_NEAR_ZERO_SECONDARY_SKIN_EFFECT_TOTAL = (
    "slip_near_zero_secondary_skin_effect_total"
)
SLIP_NEAR_ZERO_SECONDARY_LEAKAGE_SAT_LOAD = (
    "slip_near_zero_secondary_leakage_sat_load"
)
SLIP_NEAR_ZERO_SECONDARY_LEAKAGE_SAT_TOTAL = (
    "slip_near_zero_secondary_leakage_sat_total"
)
SLIP_NEAR_ZERO_SECONDARY_SKIN_LEAKAGE_SAT_LOAD = (
    "slip_near_zero_secondary_skin_leakage_sat_load"
)
SLIP_NEAR_ZERO_SECONDARY_SKIN_LEAKAGE_SAT_TOTAL = (
    "slip_near_zero_secondary_skin_leakage_sat_total"
)

# domain: shaft_output_deduction（漂遊負荷損の銘牌電流正規化）
NAMEPLATE_CURRENT_NEAR_ZERO_STRAY_LOAD_NORMALIZATION = (
    "nameplate_current_near_zero_stray_load_normalization"
)
