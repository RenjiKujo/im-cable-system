"""誘導電動機の総合イミタンス合成のインターフェース定義

OCPの原則に従い、回路トポロジー（L型、T型など）に応じた
異なる合成方法を拡張可能にするためのインターフェース。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
)


class IImTotalImmittanceSynthesizer(ABC):
    """誘導電動機の総合イミタンス合成のインターフェース

    一次、励磁、二次の各イミタンスから総合イミタンスを合成する。
    各実装は回路トポロジー（L型、T型など）に応じた合成方法を実装する。

    生成時の契約:
        実装は ``create(config, logger)`` を通じて生成し、``IConfig`` と
        ``ILogger`` を保持すること。

    Note:
        ``synthesize`` 内のドメイン層合成・変換には
        ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を用い、
        ドメイン関数の既定値に依存しないこと。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IImTotalImmittanceSynthesizer:
        """総合イミタンス合成ストラテジーを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImTotalImmittanceSynthesizer: 総合イミタンス合成ストラテジー。
        """
        pass

    @abstractmethod
    def synthesize(
        self,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """総合イミタンスを合成する

        Args:
            primary_model: 一次側モデル情報DTO（インピーダンス、アドミタンスを含む）
            excitation_model: 励磁モデル情報DTO（インピーダンス、アドミタンスを含む）
            secondary_model: 二次側モデル情報DTO（枝辞書のイミタンスを含む）

        Returns:
            ItmImTotalDto: 総合モデル情報DTO（総合インピーダンス、総合アドミタンスを含む）
        """
        pass
