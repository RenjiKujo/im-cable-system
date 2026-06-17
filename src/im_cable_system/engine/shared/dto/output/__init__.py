"""Output DTO の公開窓口。

層外・層横断からは本窓口（``output``）経由で OutputDto / OutputDtos /
結果生量 DTO を import する。図表専用属性を持たず、属性として持つ DTO は
``generic`` 由来（``result`` のみ本パッケージ内の結果生量 DTO）。
"""

from im_cable_system.engine.shared.dto.output.output_dto import (
    OutputDto,
    OutputDtos,
)
from im_cable_system.engine.shared.dto.output.output_simulation_result_dto import (  # noqa: E501
    OutputSimulationResultDto,
)

__all__ = [
    "OutputDto",
    "OutputDtos",
    "OutputSimulationResultDto",
]
