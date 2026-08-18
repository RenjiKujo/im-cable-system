"""摩擦・風損計算器ファクトリー（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.constant_friction_windage_loss_calculator import (  # noqa: E501
    ConstantFrictionWindageLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.i_friction_windage_loss_calculator import (  # noqa: E501
    IFrictionWindageLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.none_friction_windage_loss_calculator import (  # noqa: E501
    NoneFrictionWindageLossCalculator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImFrictionWindageModelType,
)


class FrictionWindageLossCalculatorFactory:
    """摩擦・風損計算器のファクトリークラス。"""

    @classmethod
    def create(
        cls,
        model_type: ImFrictionWindageModelType,
        config: IConfig,
        logger: ILogger,
    ) -> IFrictionWindageLossCalculator:
        """摩擦・風損計算器を生成する。

        Args:
            model_type: 摩擦・風損モデル種別。
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IFrictionWindageLossCalculator: 計算器インスタンス。

        Raises:
            ValueError: 未対応のモデル種別が指定された場合。
        """
        if model_type == ImFrictionWindageModelType.NONE:
            return NoneFrictionWindageLossCalculator.create(
                config=config, logger=logger
            )
        if model_type == ImFrictionWindageModelType.CONSTANT_V1:
            return ConstantFrictionWindageLossCalculator.create(
                config=config, logger=logger
            )
        raise ValueError(f"未対応の摩擦・風損モデル型です: {model_type}")
