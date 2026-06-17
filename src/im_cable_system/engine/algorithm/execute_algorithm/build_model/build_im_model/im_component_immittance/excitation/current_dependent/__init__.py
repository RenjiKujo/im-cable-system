"""励磁回路イミタンス（電流依存モデル）。

Note:
    Algorithm 層内（build_model）のコンポーネント窓口。層外からは import しない。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.excitation.current_dependent.v1_excitation_saturation_immittance_converter import (  # noqa: E501
    CurrentDependentExcitationSaturationImmittanceConverterV1,
)

__all__ = ["CurrentDependentExcitationSaturationImmittanceConverterV1"]
