"""特性値計算オーケストレーター実装（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_efficiency import (  # noqa: E501
    EfficiencyCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_rotational_speed import (  # noqa: E501
    RotationalSpeedCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_torque import (  # noqa: E501
    TorqueCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.i_characteristics_calculation_orchestrator import (  # noqa: E501
    ICharacteristicsCalculationOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.itm import (
    ItmCharacteristicDto,
    ItmEfficiencyDto,
    ItmModelDto,
    ItmPowerDto,
    ItmRotationalSpeedDto,
    ItmTorqueDto,
)


class CharacteristicsCalculationOrchestrator(
    ICharacteristicsCalculationOrchestrator
):
    """特性値計算オーケストレーター実装。

    回転速度 → トルク → 効率の順で計算し、`ItmCharacteristicDto` として返す。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ICharacteristicsCalculationOrchestrator:
        return cls(config=config, logger=logger)

    # NOTE: 小さい入力だとミリ秒未満になりログがノイズ化しやすいため、
    # 一定時間以上の処理のみタイマーを出力する。
    @timer(logger=None, line="#", min_duration=0.01)
    def calculate(
        self,
        *,
        model_dto: ItmModelDto,
        power_dto: ItmPowerDto,
    ) -> ItmCharacteristicDto:
        rotational_speed = self._calculate_rotational_speed(model_dto=model_dto)
        torque = self._calculate_torque(
            power_dto=power_dto,
            rotational_speed=rotational_speed,
        )
        efficiency = self._calculate_efficiency(power_dto=power_dto)

        return ItmCharacteristicDto(
            rotational_speed=rotational_speed,
            torque=torque,
            efficiency=efficiency,
        )

    def _calculate_rotational_speed(
        self,
        model_dto: ItmModelDto,
    ) -> ItmRotationalSpeedDto:
        """回転速度を計算する。"""
        calculator = RotationalSpeedCalculator.create(
            config=self._config,
            logger=self._logger,
        )
        poles = model_dto.im.poles.value
        rotational_speed = calculator.calculate(
            array_layout=model_dto.array_layout,
            poles=poles,
        )
        return ItmRotationalSpeedDto(rotational_speed=rotational_speed)

    def _calculate_torque(
        self,
        power_dto: ItmPowerDto,
        rotational_speed: ItmRotationalSpeedDto,
    ) -> ItmTorqueDto:
        """トルクを計算する。"""
        calculator = TorqueCalculator.create(
            config=self._config,
            logger=self._logger,
        )
        torque = calculator.calculate(
            power_dto=power_dto,
            rotational_speed=rotational_speed.rotational_speed,
        )
        return ItmTorqueDto(torque=torque)

    def _calculate_efficiency(
        self,
        power_dto: ItmPowerDto,
    ) -> ItmEfficiencyDto:
        """効率を計算する。"""
        calculator = EfficiencyCalculator.create(
            config=self._config,
            logger=self._logger,
        )
        return calculator.calculate(power_dto=power_dto)
