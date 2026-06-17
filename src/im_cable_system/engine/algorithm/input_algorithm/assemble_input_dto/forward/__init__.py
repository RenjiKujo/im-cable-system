"""Forward 系（CartesianGrid / OperatingPoints 共通）InputDto 組み立て公開窓口。

層外・オーケストレーターからは本パッケージの ``ForwardInputDtoAssembler`` を
import する。モードに応じた参照軸の差は ``reference_axes`` の指定で表現する。
"""

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.forward.assembler import (  # noqa: E501
    ForwardInputDtoAssembler,
)

__all__ = [
    "ForwardInputDtoAssembler",
]
