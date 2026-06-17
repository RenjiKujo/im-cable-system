"""シミュレーション計算モジュール（im_cable_system）。

電流電圧→電力→特性値のシミュレーション計算を提供します。

公開窓口:
    本パッケージ直下に置くオーケストレーター IF
    （:class:`ISimulationOrchestrator`）の公開窓口。実装
    （``SimulationOrchestrator``）や数値安定化レポートの受け渡しは
    ``simulate.orchestrate`` 窓口を参照すること。
"""

from im_cable_system.engine.algorithm.execute_algorithm.simulate.i_simulation_orchestrator import (  # noqa: E501
    ISimulationOrchestrator,
)

__all__ = [
    "ISimulationOrchestrator",
]
