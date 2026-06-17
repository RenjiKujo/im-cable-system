"""イミタンス計算ストラテジーのインターフェース定義

OCPの原則に従い、励磁飽和や表皮効果などの
異なる計算方法を拡張可能にするためのインターフェース。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    ImSecondaryCageBranchType,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
)


class IPrimaryImmittanceConverter(ABC):
    """一次回路イミタンス計算のコンバーターインターフェース

    ImSeriesDtoとArrayLayoutDtoを受け取り、ItmImPrimaryDtoを返す。

    生成時の契約:
        実装は ``create(config, logger)`` を通じて生成し、``IConfig`` と
        ``ILogger`` を保持すること。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IPrimaryImmittanceConverter:
        """一次回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IPrimaryImmittanceConverter: 一次回路イミタンス計算コンバーター。
        """
        pass

    @abstractmethod
    def convert(
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImPrimaryDto:
        """一次側イミタンスを計算する

        Args:
            src: モーターシリーズDTO（必要な情報は全て含まれている）
            model_array_layout: 配列レイアウトDTO

        Returns:
            ItmImPrimaryDto: 一次側モデル情報DTO

        Note:
            ドメイン層計算・クランプ処理には
            ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を用い、
            ドメイン関数の既定値に依存しないこと。
        """
        pass


class IExcitationImmittanceConverter(ABC):
    """励磁回路イミタンス計算のコンバーターインターフェース

    ImSeriesDtoとArrayLayoutDtoを受け取り、ItmImExcitationDtoを返す。

    生成時の契約:
        実装は ``create(config, logger)`` を通じて生成し、``IConfig`` と
        ``ILogger`` を保持すること。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IExcitationImmittanceConverter:
        """励磁回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IExcitationImmittanceConverter: 励磁回路イミタンス計算コンバーター。
        """
        pass

    @abstractmethod
    def convert(
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImExcitationDto:
        """励磁回路イミタンスを計算する

        Args:
            src: モーターシリーズDTO（必要な情報は全て含まれている）
            model_array_layout: 配列レイアウトDTO

        Returns:
            ItmImExcitationDto: 励磁モデル情報DTO

        Note:
            ドメイン層計算・クランプ処理には
            ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を用い、
            ドメイン関数の既定値に依存しないこと。
        """
        pass


class ISecondaryImmittanceConverter(ABC):
    """二次回路イミタンス計算のコンバーターインターフェース

    ImSeriesDtoとArrayLayoutDtoを受け取り、ItmImSecondaryDtoを返す。

    電流依存モデルは ``secondary_current`` に当該枝の二次相電流（基本単位）を
    渡すこと。単一かごでは
    :mod:`~im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.resolve_secondary_current_for_layout`
    の ``resolve_secondary_current_for_layout`` でレイアウトから解決して渡す。
    Basic / スリップ依存実装は
    ``secondary_current`` を無視してよい。

    ``secondary_cage_branch_type`` で内翅・外翅など計算対象枝を指定する。
    戻り値の辞書は当該枝のキーのみを含む。二重かごで全枝の
    :class:`ItmImSecondaryDto` が必要な場合は呼び出し側で枝ごとの結果をマージする。

    生成時の契約:
        実装は ``create(config, logger)`` を通じて生成し、``IConfig`` と
        ``ILogger`` を保持すること。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ISecondaryImmittanceConverter:
        """二次回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ISecondaryImmittanceConverter: 二次回路イミタンス計算コンバーター。
        """
        pass

    @abstractmethod
    def convert(
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
        *,
        secondary_cage_branch_type: ImSecondaryCageBranchType = (
            ImSecondaryCageBranchType.SINGLE
        ),
        secondary_current: ArrayComplexCurrentDto | None = None,
    ) -> ItmImSecondaryDto:
        """二次側イミタンスを計算する

        Args:
            src: モーターシリーズDTO（必要な情報は全て含まれている）
            model_array_layout: 配列レイアウトDTO
            secondary_cage_branch_type: 計算対象の二次枝（単一かごは ``SINGLE``）。
            secondary_current: 二次相電流（基本単位）。電流依存モデルでは必須。
                Basic / スリップ依存では None 可（無視される）。

        Returns:
            ItmImSecondaryDto: 二次側モデル情報DTO（当該枝キーのみの辞書。
                :attr:`cage_multiplicity` は ``src`` に一致）。

        Raises:
            ValueError: 電流依存モデルで ``secondary_current`` が None の場合。
            ValueError: 指定枝が ``src`` の二次辞書に無い場合。

        Note:
            ドメイン層計算・スリップ近接ゼロのクランプ処理には
            ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を用い、
            ドメイン関数の既定値に依存しないこと。
        """
        pass
