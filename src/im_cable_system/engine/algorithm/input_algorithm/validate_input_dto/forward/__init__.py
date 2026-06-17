"""Forward 系（CartesianGrid / OperatingPoints 共通）InputDto バリデーション公開窓口。

層外・オーケストレーターからは本パッケージの ``ForwardInputDtoValidator`` を
import する。モード分岐は持たず、``reference_axes`` に従って一様に検査する。

責務分担:
    TSV/YAML 構造・スキーマ違反は ``load_data`` 層、
    DTO 化・単位正規化・enum 変換は ``assemble_input_dto`` 層、
    DTO ``__post_init__`` による局所契約は各 DTO に分離している。
    本パッケージでは InputDto 全体になって初めて判定できる契約
    （SI 基本単位、cross-field 数値、参照軸直積グリッド上限等）のみを扱う。
"""

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.forward.validator import (  # noqa: E501
    ForwardInputDtoValidator,
)

__all__ = [
    "ForwardInputDtoValidator",
]
