"""IM電圧電流計算器のファクトリークラス。

このモジュールは、IM二次回路モデルタイプに応じて適切な
IM電圧電流計算器のインスタンスを生成します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current.double_cage_im_voltage_current_calculator import (  # noqa: E501
    DoubleCageImVoltageCurrentCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current.i_im_voltage_current_calculator import (  # noqa: E501
    IImVoltageCurrentCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current.single_cage_im_voltage_current_calculator import (  # noqa: E501
    SingleCageImVoltageCurrentCalculator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
)


class ImVoltageCurrentCalculatorFactory:
    """IM電圧電流計算器のファクトリークラス。

    かごの重数（単一／二重）に応じて適切なIM電圧電流計算器のインスタンスを生成します。

    build_model により各ノードのイミタンス（配列）は確定しているため、
    VI計算器の分岐軸は model type ではなく cage_multiplicity とします。
    """

    @classmethod
    def create(
        cls,
        cage_multiplicity: ImCageMultiplicityType,
        config: IConfig,
        logger: ILogger,
    ) -> IImVoltageCurrentCalculator:
        """IM電圧電流計算器のインスタンスを生成する。

        Args:
            cage_multiplicity: かごの重数（単一／二重）。
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IImVoltageCurrentCalculator: 生成された計算器インスタンス。

        Raises:
            ValueError: 未対応のかご重数が指定された場合。
        """
        if cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
            return SingleCageImVoltageCurrentCalculator.create(
                config=config, logger=logger
            )
        if cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE:
            return DoubleCageImVoltageCurrentCalculator.create(
                config=config, logger=logger
            )
        raise ValueError(f"未対応のかご重数です: {cage_multiplicity}")
