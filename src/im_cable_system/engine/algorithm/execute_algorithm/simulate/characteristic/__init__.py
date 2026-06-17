"""特性値計算モジュール（im_cable_system）。

外部に公開する契約は特性値計算オーケストレーターのインターフェース
（:class:`ICharacteristicsCalculationOrchestrator`）のみとする。
実装（``CharacteristicsCalculationOrchestrator``）は ``orchestrate`` 窓口、
個別計算器は各 ``calculate_*`` 窓口から import すること。
"""

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.i_characteristics_calculation_orchestrator import (  # noqa: E501
    ICharacteristicsCalculationOrchestrator,
)

__all__ = [
    "ICharacteristicsCalculationOrchestrator",
]
