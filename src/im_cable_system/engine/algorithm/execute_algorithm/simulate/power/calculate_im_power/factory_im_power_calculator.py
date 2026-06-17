"""IM電力計算器ファクトリー（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power.double_cage_im_power_calculator import (  # noqa: E501
    DoubleCageImPowerCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power.i_im_power_calculator import (  # noqa: E501
    IImPowerCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power.single_cage_im_power_calculator import (  # noqa: E501
    SingleCageImPowerCalculator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
)


class ImPowerCalculatorFactory:
    """IM電力計算器のファクトリークラス。"""

    @classmethod
    def create(
        cls,
        cage_multiplicity: ImCageMultiplicityType,
        config: IConfig,
        logger: ILogger,
    ) -> IImPowerCalculator:
        """IM電力計算器を生成する。

        Args:
            cage_multiplicity: かごの重数（単一／二重）。
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IImPowerCalculator: 計算器インスタンス。

        Raises:
            ValueError: 未対応のかご重数が指定された場合。
        """
        if cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
            return SingleCageImPowerCalculator.create(
                config=config, logger=logger
            )
        if cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE:
            return DoubleCageImPowerCalculator.create(
                config=config, logger=logger
            )
        raise ValueError(f"未対応のかご重数です: {cage_multiplicity}")
