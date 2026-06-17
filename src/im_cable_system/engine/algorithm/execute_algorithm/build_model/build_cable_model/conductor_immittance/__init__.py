"""導線イミタンス計算モジュール。

導線インピーダンス計算のインターフェースとファクトリーを提供する。

Note:
    Algorithm 層内（build_model）のコンポーネント窓口。層外からは import しない。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.factory_conductor_immittance_converter import (  # noqa: E501
    ConductorImmittanceConverterFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.i_conductor_immittance_converter import (  # noqa: E501
    IConductorImmittanceConverter,
)

__all__ = [
    "IConductorImmittanceConverter",
    "ConductorImmittanceConverterFactory",
]
