"""中間DTO検証パッケージ（im_cable_system）。

このパッケージは、IMケーブルシステム電気シミュレーションにおける中間DTOの
検証処理を提供します。

公開窓口:
    本パッケージ直下に置くオーケストレーター IF
    （:class:`IItmValidationOrchestrator`）の公開窓口。実装
    （``ItmValidationOrchestrator``）は ``validate_itm_dto.orchestrate``
    窓口を参照すること。
"""

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.i_itm_validation_orchestrator import (  # noqa: E501
    IItmValidationOrchestrator,
)

__all__ = [
    "IItmValidationOrchestrator",
]
