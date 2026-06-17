"""二次イミタンス（スリップ依存）。

Note:
    Algorithm 層内（build_model）のコンポーネント窓口。層外からは import しない。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.slip_dependent.v1_secondary_skin_effect_immittance_converter import (  # noqa: E501
    SlipDependentSecondarySkinEffectImmittanceConverterV1,
)

__all__ = [
    "SlipDependentSecondarySkinEffectImmittanceConverterV1",
]
