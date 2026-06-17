"""Forward 系ジョブ spec 公開窓口.

CartesianGrid モードと OperatingPoints モードは同じ ``ForwardJobSpec`` /
``ForwardJobSpecs`` を共有する。軸ファイルの解釈の違い（直積 / co-indexed）は
``assemble_input_dto`` 段の ``reference_axes`` 指定で表現される。
"""

from im_cable_system.engine.shared.job_spec.forward.forward_job_spec import (
    ForwardJobSpec,
    ForwardJobSpecs,
)

__all__ = [
    "ForwardJobSpec",
    "ForwardJobSpecs",
]
