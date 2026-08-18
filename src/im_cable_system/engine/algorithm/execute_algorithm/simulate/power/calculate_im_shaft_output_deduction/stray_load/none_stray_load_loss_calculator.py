"""漂遊負荷損計算器の実装クラス（NONE: 損失なし）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.i_stray_load_loss_calculator import (  # noqa: E501
    IStrayLoadLossCalculator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


class NoneStrayLoadLossCalculator(IStrayLoadLossCalculator):
    """漂遊負荷損を考慮しない計算器（ゼロ配列を返す）。

    既定（``NONE``）はこの計算器が使われ、既存の数値挙動を一切変えない。
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
        im_model: ItmImModelDto,  # noqa: ARG002
        secondary_current: ArrayComplexCurrentDto,
    ) -> ArrayComplexPowerDto:
        return ArrayComplexPowerDto(
            value=np.zeros_like(secondary_current.get_value()), unit="VA"
        )
