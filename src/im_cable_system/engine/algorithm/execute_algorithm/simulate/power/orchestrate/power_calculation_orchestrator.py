"""電力計算オーケストレーター実装（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_cable_power import (  # noqa: E501
    PieCablePowerCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power import (  # noqa: E501
    ImPowerCalculatorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.i_power_calculation_orchestrator import (  # noqa: E501
    IPowerCalculationOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCablePowerDto,
    ItmImPowerDto,
    ItmModelDto,
    ItmPowerDto,
    ItmVoltageCurrentDto,
)


class PowerCalculationOrchestrator(IPowerCalculationOrchestrator):
    """電力計算オーケストレーター実装。

    ケーブル電力計算とIM電力計算を順次実行し、結果を統合する。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IPowerCalculationOrchestrator:
        return cls(config=config, logger=logger)

    # NOTE: 小さい入力だとミリ秒未満になりログがノイズ化しやすいため、
    # 一定時間以上の処理のみタイマーを出力する。
    @timer(logger=None, line="#", min_duration=0.01)
    def calculate(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmPowerDto:
        cable_power = self._calculate_cable_power(
            model_dto=model_dto,
            voltage_current_dto=voltage_current_dto,
        )
        im_power = self._calculate_im_power(
            model_dto=model_dto,
            voltage_current_dto=voltage_current_dto,
        )
        return ItmPowerDto(im_power=im_power, cable_power=cable_power)

    def _calculate_cable_power(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmCablePowerDto:
        """ケーブル電力を計算する。"""
        cable_calculator = PieCablePowerCalculator.create(
            config=self._config, logger=self._logger
        )
        return cable_calculator.calculate(
            cable_model=model_dto.cable,
            cable_voltage_current=voltage_current_dto.cable_voltage_current,
        )

    def _calculate_im_power(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmImPowerDto:
        """IM電力を計算する。"""
        cage_multiplicity: ImCageMultiplicityType = (
            model_dto.im.secondary_model.cage_multiplicity
        )
        im_calculator = ImPowerCalculatorFactory.create(
            cage_multiplicity=cage_multiplicity,
            config=self._config,
            logger=self._logger,
        )
        return im_calculator.calculate(
            im_model=model_dto.im,
            im_voltage_current=voltage_current_dto.im_voltage_current,
        )
