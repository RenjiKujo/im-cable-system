"""IM 電気シミュレーション（im_cable_system）アルゴリズムパッケージ。

build_model / simulate / validate_itm_dto など、IM ケーブルシステム固有の
実行アルゴリズム実装を、ステップ別のサブパッケージに分割して束ねる。

公開窓口:
    本パッケージ直下に置く全モード共通のオーケストレーター IF
    （:class:`IExecuteAlgorithmsOrchestrator`）の公開窓口。モード別 IF
    （``IForwardExecutionOrchestrator`` 等）はこの共通 IF を継承して
    具体化し、それぞれの実行モードのサブパッケージ窓口で公開する。

Note:
    層外（processor / pipeline 等）が「モードを問わず任意の実行
    オーケストレーターを受け取る」型として用いるのは、本窓口の共通 IF
    （:class:`IExecuteAlgorithmsOrchestrator`）である。実行モード別の
    オーケストレーター実装・ファクトリは ``orchestrate.forward`` /
    ``orchestrate.estimate_params`` 等の窓口から import すること。
"""

from im_cable_system.engine.algorithm.execute_algorithm.i_execute_algorithms_orchestrator import (  # noqa: E501
    IExecuteAlgorithmsOrchestrator,
)

__all__ = [
    "IExecuteAlgorithmsOrchestrator",
]
