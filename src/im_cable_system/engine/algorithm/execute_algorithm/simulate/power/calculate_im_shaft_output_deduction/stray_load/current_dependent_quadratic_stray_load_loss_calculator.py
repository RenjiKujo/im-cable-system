"""漂遊負荷損計算器の実装クラス（CURRENT_DEPENDENT_QUADRATIC_V1）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.i_stray_load_loss_calculator import (  # noqa: E501
    IStrayLoadLossCalculator,
)
from im_cable_system.engine.domain.physics import (
    calculate_quadratic_stray_load_loss,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


class CurrentDependentQuadraticStrayLoadLossCalculator(
    IStrayLoadLossCalculator
):
    """二次電流比の2乗に比例する漂遊負荷損
    （``CURRENT_DEPENDENT_QUADRATIC_V1``）を計算する計算器。

    数式は ``docs/model_equations/im_stray_load.md`` を正とする。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IStrayLoadLossCalculator:
        return cls(config=config, logger=logger)

    def calculate(
        self,
        im_model: ItmImModelDto,
        secondary_current: ArrayComplexCurrentDto,
    ) -> ArrayComplexPowerDto:
        if im_model.stray_load_model.params is None:
            raise ValueError("stray_load_model.paramsが必要ですが、Noneです。")
        k_stray_load = im_model.stray_load_model.params.get_by_name(
            "k_stray_load"
        ).get_value()
        eps = self._config.numerical_guard_config.eps

        loss = calculate_quadratic_stray_load_loss(
            nameplate_power=im_model.nameplate_power,
            nameplate_current=im_model.nameplate_current,
            secondary_current=secondary_current,
            k_stray_load=k_stray_load,
            eps=eps,
        )
        return ArrayComplexPowerDto(
            value=loss.get_value().astype(np.complex128), unit="VA"
        )
