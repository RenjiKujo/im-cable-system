"""電流依存導線イミタンス計算モジュール。

電流依存表皮効果（V1）モデルに対する π 型ケーブル用の
導線イミタンス計算コンバーターを提供する。

Note:
    Algorithm 層内（build_model）のコンポーネント窓口。層外からは import しない。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.current_dependent.v1_current_dependent_skin_effect_immittance_converter import (  # noqa: E501
    CurrentDependentSkinEffectConductorImmittanceConverterV1,
)

__all__ = [
    "CurrentDependentSkinEffectConductorImmittanceConverterV1",
]
