"""導線イミタンス計算のファクトリークラス

現状は π 型ケーブル用のコンバーターのみ生成する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.basic import (
    BasicConductorImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.current_dependent import (
    CurrentDependentSkinEffectConductorImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.frequency_dependent import (
    FrequencyDependentSkinEffectConductorImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.i_conductor_immittance_converter import (
    IConductorImmittanceConverter,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    ConductorModelType,
)


class ConductorImmittanceConverterFactory:
    """導線イミタンス計算コンバーターのファクトリークラス

    OCPの原則に従い、ConductorModelType に応じて
    適切なイミタンス計算コンバーターを選択する（π 型ケーブル用）。

    生成したコンバーターは ``config.numerical_guard_config.eps`` を
    ``convert`` 内で参照し、ドメイン層の数値安定化計算へ伝播する。
    """

    @classmethod
    def create_pie_converter(
        cls,
        conductor_model: CableConductorModelDto,
        config: IConfig,
        logger: ILogger,
    ) -> IConductorImmittanceConverter:
        """PIE型用の導線イミタンス計算コンバーターを作成する

        Args:
            conductor_model: 導線回路モデルDTO
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IConductorImmittanceConverter: PIE用導線イミタンス計算コンバーター

        Raises:
            ValueError: 未対応の導線回路モデルタイプが指定された場合
        """
        model_type_name = conductor_model.get_name()
        if model_type_name == ConductorModelType.BASIC.value:
            return BasicConductorImmittanceConverter.create(
                config=config, logger=logger
            )
        if (
            model_type_name
            == ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1.value
        ):
            return FrequencyDependentSkinEffectConductorImmittanceConverterV1.create(
                config=config, logger=logger
            )
        if (
            model_type_name
            == ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1.value
        ):
            return (
                CurrentDependentSkinEffectConductorImmittanceConverterV1.create(
                    config=config, logger=logger
                )
            )
        raise ValueError(f"未対応の導線回路モデルタイプです: {model_type_name}")
