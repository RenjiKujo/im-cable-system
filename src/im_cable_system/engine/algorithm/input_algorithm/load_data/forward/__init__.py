"""Forward 系（CartesianGrid / OperatingPoints 共通）ローダー公開窓口。

``ForwardJobSpec`` を受ける単一の ``ForwardLoader`` のみを公開する。
モードによる分岐は本層には存在しない。
"""

from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.loader import (  # noqa: E501
    ForwardLoader,
)

__all__ = [
    "ForwardLoader",
]
