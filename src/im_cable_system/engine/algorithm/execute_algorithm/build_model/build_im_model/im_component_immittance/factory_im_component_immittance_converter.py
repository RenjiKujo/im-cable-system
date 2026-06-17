"""誘導電動機のイミタンス計算のファクトリークラス

ModTypeに応じて適切なコンバーターを生成する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.excitation import (
    BasicExcitationImmittanceConverter,
    CurrentDependentExcitationSaturationImmittanceConverterV1,
    SlipDependentExcitationSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.i_im_component_immittance_converter import (
    IExcitationImmittanceConverter,
    IPrimaryImmittanceConverter,
    ISecondaryImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.primary import (
    BasicPrimaryImmittanceConverter,
    CurrentDependentPrimaryLeakageSaturationImmittanceConverterV1,
    SlipDependentPrimaryLeakageSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary import (
    BasicSecondaryImmittanceConverter,
    CurrentDependentSecondaryLeakageSaturationImmittanceConverterV1,
    CurrentDependentSecondarySkinEffectAndLeakageSaturationImmittanceConverterV1,
    CurrentDependentSecondarySkinEffectImmittanceConverterV1,
    SlipDependentSecondarySkinEffectImmittanceConverterV1,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImExcitationModelDto,
    ImExcitationModelType,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)


class ImComponentImmittanceConverterFactory:
    """誘導電動機の各成分イミタンス計算コンバーターのファクトリークラス

    OCPの原則に従い、ModTypeに応じて適切なイミタンス計算コンバーターを選択する。

    生成したコンバーターは ``config.numerical_guard_config.eps`` を
    ``convert`` 内で参照し、ドメイン層の数値安定化計算へ伝播する。
    """

    @classmethod
    def create_primary_converter(
        cls,
        circuit_model: ImPrimaryModelDto,
        config: IConfig,
        logger: ILogger,
    ) -> IPrimaryImmittanceConverter:
        """一次回路イミタンス計算コンバーターを作成する

        Args:
            circuit_model: 一次回路モデルDTO
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IPrimaryImmittanceConverter: 一次回路イミタンス計算コンバーター

        Raises:
            ValueError: 未対応の一次回路モデルタイプが指定された場合
        """
        model_type_name = circuit_model.get_name()
        if model_type_name == ImPrimaryModelType.BASIC.value:
            return BasicPrimaryImmittanceConverter.create(
                config=config, logger=logger
            )
        if (
            model_type_name
            == ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1.value
        ):
            return SlipDependentPrimaryLeakageSaturationImmittanceConverterV1.create(
                config=config,
                logger=logger,
            )
        if (
            model_type_name
            == ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1.value
        ):
            return CurrentDependentPrimaryLeakageSaturationImmittanceConverterV1.create(
                config=config,
                logger=logger,
            )
        raise ValueError(f"未対応の一次回路モデルタイプです: {model_type_name}")

    @classmethod
    def create_excitation_converter(
        cls,
        circuit_model: ImExcitationModelDto,
        config: IConfig,
        logger: ILogger,
    ) -> IExcitationImmittanceConverter:
        """励磁回路イミタンス計算コンバーターを作成する

        Args:
            circuit_model: 励磁回路モデルDTO
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IExcitationImmittanceConverter: 励磁回路イミタンス計算コンバーター

        Raises:
            ValueError: 未対応の励磁回路モデルタイプが指定された場合
        """
        model_type_name = circuit_model.get_name()
        if model_type_name == ImExcitationModelType.BASIC.value:
            return BasicExcitationImmittanceConverter.create(
                config=config, logger=logger
            )
        if (
            model_type_name
            == ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1.value
        ):
            return (
                SlipDependentExcitationSaturationImmittanceConverterV1.create(
                    config=config,
                    logger=logger,
                )
            )
        if (
            model_type_name
            == ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1.value
        ):
            return CurrentDependentExcitationSaturationImmittanceConverterV1.create(
                config=config,
                logger=logger,
            )
        raise ValueError(f"未対応の励磁回路モデルタイプです: {model_type_name}")

    @classmethod
    def create_secondary_converter(
        cls,
        circuit_model: ImSecondaryModelDto,
        config: IConfig,
        logger: ILogger,
    ) -> ISecondaryImmittanceConverter:
        """二次回路イミタンス計算コンバーターを作成する

        Args:
            circuit_model: 二次回路モデルDTO
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ISecondaryImmittanceConverter: 二次回路イミタンス計算コンバーター

        Raises:
            ValueError: 未対応の二次回路モデルタイプが指定された場合
        """
        model_type_name = circuit_model.get_name()
        if model_type_name == ImSecondaryModelType.BASIC.value:
            return BasicSecondaryImmittanceConverter.create(
                config=config, logger=logger
            )
        if (
            model_type_name
            == ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1.value
        ):
            return SlipDependentSecondarySkinEffectImmittanceConverterV1.create(
                config=config,
                logger=logger,
            )
        if (
            model_type_name
            == ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1.value
        ):
            return (
                CurrentDependentSecondarySkinEffectImmittanceConverterV1.create(
                    config=config,
                    logger=logger,
                )
            )
        if (
            model_type_name
            == ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1.value
        ):
            return CurrentDependentSecondaryLeakageSaturationImmittanceConverterV1.create(
                config=config,
                logger=logger,
            )
        if (
            model_type_name
            == ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1.value
        ):
            return CurrentDependentSecondarySkinEffectAndLeakageSaturationImmittanceConverterV1.create(
                config=config,
                logger=logger,
            )
        raise ValueError(f"未対応の二次回路モデルタイプです: {model_type_name}")
