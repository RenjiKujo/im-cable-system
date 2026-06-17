"""中間DTO検証オーケストレーター実装（im_cable_system）。

このモジュールは、IMケーブルシステムの中間DTO検証を統括する
オーケストレーターの実装を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.i_itm_validation_orchestrator import (  # noqa: E501
    IItmValidationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.validate_current_voltage_range import (  # noqa: E501
    CurrentVoltageRangeValidator,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.validate_energy_conservation import (  # noqa: E501
    EnergyConservationValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class ItmValidationOrchestrator(IItmValidationOrchestrator):
    """中間DTO検証オーケストレーター実装。

    config を解釈して、有効な検証だけを既定の順序で順次実行する。
    下位検証器の生成と実行は、対応する private メソッド内に閉じる。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IItmValidationOrchestrator:
        """オーケストレーターのインスタンスを生成する。

        自身のインスタンスのみ生成して返す。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IItmValidationOrchestrator: 生成されたインスタンス。
        """
        return cls(config=config, logger=logger)

    def validate(self, itm_dto: ItmDto) -> None:
        """中間DTOの妥当性を検証する。

        private メソッド内で検証器を生成し、既定の順序で順次実行する。実行順序:
        1. エネルギー保存則の検証（``_validate_energy_conservation``）
        2. 電流・電圧レンジの検証（``_validate_current_voltage_range``）

        各検証が Config で無効な場合、その検証はスキップされる。

        ``simulation_result`` が None の扱い（fail-closed）:
            以前は warning で全検証を一律スキップ（fail-open）していたが、
            検証漏れを隠すため廃止した。有効な検証が 1 つでもあれば、
            下位検証器が ``simulation_result is None`` を ``ValueError`` として
            送出する。いずれの検証も無効な場合は、各 private メソッドが
            早期 return するため None でも何もしない。

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）、
                または有効な検証がある状態で ``simulation_result`` が None の場合。
        """
        self._validate_energy_conservation(itm_dto=itm_dto)
        self._validate_current_voltage_range(itm_dto=itm_dto)

    def _validate_energy_conservation(self, itm_dto: ItmDto) -> None:
        """エネルギー保存則を検証する。

        validate が内部で呼ぶ。Config で無効な場合は何もしない。

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）。
        """
        if not self._config.validation_config.energy_conservation.enabled:
            return
        validator = EnergyConservationValidator.create(
            config=self._config,
            logger=self._logger,
        )
        validator.validate(itm_dto=itm_dto)

    def _validate_current_voltage_range(self, itm_dto: ItmDto) -> None:
        """電流・電圧レンジを検証する。

        validate が内部で呼ぶ。Config で無効な場合は何もしない。

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）。
        """
        if not self._config.validation_config.current_voltage_range.enabled:
            return
        validator = CurrentVoltageRangeValidator.create(
            config=self._config,
            logger=self._logger,
        )
        validator.validate(itm_dto=itm_dto)
