"""摩擦・風損計算器の実装クラス（CONSTANT_V1: 一定損失）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.i_friction_windage_loss_calculator import (  # noqa: E501
    IFrictionWindageLossCalculator,
)
from im_cable_system.engine.domain.physics import (
    calculate_constant_friction_windage_loss,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


class ConstantFrictionWindageLossCalculator(IFrictionWindageLossCalculator):
    """一定の摩擦・風損（``CONSTANT_V1``）を計算する計算器。

    数式は ``docs/model_equations/im_friction_windage.md`` を正とする。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IFrictionWindageLossCalculator:
        return cls(config=config, logger=logger)

    def calculate(
        self,
        im_model: ItmImModelDto,
        reference_shape: tuple[int, ...],
    ) -> ArrayComplexPowerDto:
        if im_model.friction_windage_model.params is None:
            raise ValueError(
                "friction_windage_model.paramsが必要ですが、Noneです。"
            )
        k_friction_windage = im_model.friction_windage_model.params.get_by_name(
            "k_friction_windage"
        ).get_value()

        loss = calculate_constant_friction_windage_loss(
            nameplate_power=im_model.nameplate_power,
            k_friction_windage=k_friction_windage,
            reference_shape=reference_shape,
        )
        return ArrayComplexPowerDto(
            value=loss.get_value().astype(np.complex128), unit="VA"
        )
