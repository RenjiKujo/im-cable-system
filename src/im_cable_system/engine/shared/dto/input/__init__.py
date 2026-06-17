"""IM ケーブル系シミュレーションの入力（Input）DTO 公開窓口。

processor の Input ステージと algorithm の Input オーケストレーターが受け渡す
トップレベル DTO をここから import する。
"""

from im_cable_system.engine.shared.dto.input.input_dto import (
    REFERENCE_AXIS_ALLOWED,
    InputDto,
    InputDtos,
)

__all__ = [
    "InputDto",
    "InputDtos",
    "REFERENCE_AXIS_ALLOWED",
]
