"""IM電圧電流計算器ファクトリーのテスト。

`ImVoltageCurrentCalculatorFactory` が、かごの重数に応じて適切な
計算器インスタンスを返すこと（分岐ロジック）を検証します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current import (  # noqa: E501
    DoubleCageImVoltageCurrentCalculator,
    IImVoltageCurrentCalculator,
    ImVoltageCurrentCalculatorFactory,
    SingleCageImVoltageCurrentCalculator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
)


class TestImVoltageCurrentCalculatorFactory:
    """`ImVoltageCurrentCalculatorFactory` の分岐ロジックのテスト。"""

    def test_single_cage_returns_single_cage_calculator(
        self, config, logger
    ) -> None:
        """単一かごでは単一かご計算器を返すこと。"""
        calculator = ImVoltageCurrentCalculatorFactory.create(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            config=config,
            logger=logger,
        )
        assert isinstance(calculator, IImVoltageCurrentCalculator)
        assert isinstance(calculator, SingleCageImVoltageCurrentCalculator)

    def test_double_cage_returns_double_cage_calculator(
        self, config, logger
    ) -> None:
        """二重かごでは二重かご計算器を返すこと。"""
        calculator = ImVoltageCurrentCalculatorFactory.create(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            config=config,
            logger=logger,
        )
        assert isinstance(calculator, IImVoltageCurrentCalculator)
        assert isinstance(calculator, DoubleCageImVoltageCurrentCalculator)
