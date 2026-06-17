"""Forward Input オーケストレーションの公開窓口（CartesianGrid / OperatingPoints 共通）。

CartesianGrid / OperatingPoints のモード分岐は ``reference_axes`` の選び方
のみで表現する。呼び出し側（InputStage）が自身のモードに応じた
``reference_axes`` を ``ForwardInputOrchestrator.create`` に渡す。
"""

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward.forward_input_orchestrator import (  # noqa: E501
    ForwardInputOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward.i_forward_input_orchestrator import (  # noqa: E501
    IForwardInputOrchestrator,
)

__all__ = [
    "ForwardInputOrchestrator",
    "IForwardInputOrchestrator",
]
