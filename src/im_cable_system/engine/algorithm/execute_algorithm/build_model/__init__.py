"""IMケーブルモデル構築モジュール。

このモジュールは、IM（誘導電動機）とケーブルのモデル構築処理を提供します。

公開窓口:
    本パッケージ直下に置くオーケストレーター IF
    （:class:`IImCableModelBuildOrchestrator`）の公開窓口。実装
    （``ImCableModelBuildOrchestrator``）は ``build_model.orchestrate``
    窓口を参照すること。
"""

from im_cable_system.engine.algorithm.execute_algorithm.build_model.i_im_cable_model_build_orchestrator import (  # noqa: E501
    IImCableModelBuildOrchestrator,
)

__all__ = [
    "IImCableModelBuildOrchestrator",
]
