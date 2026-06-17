"""トルク計算器。

回転速度 DTO と IM 有効電力から、ドメイン層のトルク計算を用いて
トルク DTO を算出する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_torque.i_torque_calculator import (  # noqa: E501
    ITorqueCalculator,
)
from im_cable_system.engine.domain.physics import (
    calculate_torque,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayRotationalSpeedDto,
    ArrayTorqueDto,
)
from im_cable_system.engine.shared.dto.itm import ItmPowerDto


class TorqueCalculator(ITorqueCalculator):
    """トルク計算器実装（im_cable_system）。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> ITorqueCalculator:
        return cls(config=config, logger=logger)

    def calculate(
        self,
        *,
        power_dto: ItmPowerDto,
        rotational_speed: ArrayRotationalSpeedDto,
    ) -> ArrayTorqueDto:
        """トルクを計算する。"""
        # IM出力電力（3相合計複素電力）から、有効電力配列へ変換して使用する
        output_active_power = (
            power_dto.im_power.output_power.to_active_power_array(unit="W")
        )

        return calculate_torque(
            output_power=output_active_power,
            rotational_speed=rotational_speed,
            eps=self._config.numerical_guard_config.eps,
        )
