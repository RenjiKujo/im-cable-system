"""一次回路イミタンス（基本モデル）。

Note:
    Algorithm 層内（build_model）のコンポーネント窓口。層外からは import しない。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.primary.basic.primary_immittance_converter import (  # noqa: E501
    BasicPrimaryImmittanceConverter,
)

__all__ = ["BasicPrimaryImmittanceConverter"]
