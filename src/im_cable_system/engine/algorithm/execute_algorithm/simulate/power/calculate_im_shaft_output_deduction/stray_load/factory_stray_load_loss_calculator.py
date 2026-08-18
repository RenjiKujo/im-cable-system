"""漂遊負荷損計算器ファクトリー（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.current_dependent_quadratic_stray_load_loss_calculator import (  # noqa: E501
    CurrentDependentQuadraticStrayLoadLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.i_stray_load_loss_calculator import (  # noqa: E501
    IStrayLoadLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.none_stray_load_loss_calculator import (  # noqa: E501
    NoneStrayLoadLossCalculator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImStrayLoadModelType,
)


class StrayLoadLossCalculatorFactory:
    """漂遊負荷損計算器のファクトリークラス。"""

    @classmethod
    def create(
        cls,
        model_type: ImStrayLoadModelType,
        config: IConfig,
        logger: ILogger,
    ) -> IStrayLoadLossCalculator:
        """漂遊負荷損計算器を生成する。

        Args:
            model_type: 漂遊負荷損モデル種別。
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IStrayLoadLossCalculator: 計算器インスタンス。

        Raises:
            ValueError: 未対応のモデル種別が指定された場合。
        """
        if model_type == ImStrayLoadModelType.NONE:
            return NoneStrayLoadLossCalculator.create(
                config=config, logger=logger
            )
        if model_type == ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1:
            return CurrentDependentQuadraticStrayLoadLossCalculator.create(
                config=config, logger=logger
            )
        raise ValueError(f"未対応の漂遊負荷損モデル型です: {model_type}")
