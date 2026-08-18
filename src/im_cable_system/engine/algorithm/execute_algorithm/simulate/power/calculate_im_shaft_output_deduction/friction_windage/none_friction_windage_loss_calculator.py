"""摩擦・風損計算器の実装クラス（NONE: 損失なし）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.i_friction_windage_loss_calculator import (  # noqa: E501
    IFrictionWindageLossCalculator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


class NoneFrictionWindageLossCalculator(IFrictionWindageLossCalculator):
    """摩擦・風損を考慮しない計算器（ゼロ配列を返す）。

    既定（``NONE``）はこの計算器が使われ、既存の数値挙動を一切変えない。
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
        im_model: ItmImModelDto,  # noqa: ARG002
        reference_shape: tuple[int, ...],
    ) -> ArrayComplexPowerDto:
        return ArrayComplexPowerDto(
            value=np.zeros(reference_shape, dtype=np.complex128), unit="VA"
        )
