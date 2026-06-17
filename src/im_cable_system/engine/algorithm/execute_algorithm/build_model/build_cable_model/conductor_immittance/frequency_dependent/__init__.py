"""周波数依存導線イミタンス計算モジュール。

周波数依存表皮効果（V1）モデルに対する π 型ケーブル用の
導線イミタンス計算コンバーターを提供する。

Note:
    Algorithm 層内（build_model）のコンポーネント窓口。層外からは import しない。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.frequency_dependent.v1_frequency_dependent_skin_effect_immittance_converter import (  # noqa: E501
    FrequencyDependentSkinEffectConductorImmittanceConverterV1,
)

__all__ = [
    "FrequencyDependentSkinEffectConductorImmittanceConverterV1",
]
