"""システム回路モデル構築器のインターフェース定義。

このモジュールは、ItmImModelDtoとItmCableModelDtoからItmSystemModelDtoを構築する
システム回路モデル構築器のインターフェースを定義します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCableModelDto,
    ItmImModelDto,
    ItmSystemModelDto,
)


class ISystemModelBuilder(ABC):
    """システム回路モデル構築器のインターフェース。

    ItmImModelDtoとItmCableModelDtoからItmSystemModelDtoを構築する処理の契約を定義します。

    Note:
        本インターフェースは、システム等価回路のトポロジー（例: π型、T型、多重π型など）を
        実装クラスの差し替えで拡張できるようにするための契約です。
        現状は π 型（`ImPieCableSystemModelBuilder`）のみをサポートしますが、
        将来的なトポロジー追加時には本インターフェースを実装するクラスを追加します。
    """

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> ISystemModelBuilder:
        """システム回路モデル構築器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: システム回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ISystemModelBuilder: 生成されたシステム回路モデル構築器インスタンス。
        """
        pass

    @abstractmethod
    def build(
        self,
        itm_im_model_dto: ItmImModelDto,
        itm_cable_model_dto: ItmCableModelDto,
    ) -> ItmSystemModelDto:
        """システム回路モデルを構築する。

        Args:
            itm_im_model_dto: 誘導電動機モデルDTO（必須）。
            itm_cable_model_dto: ケーブルモデルDTO（必須）。

        Returns:
            ItmSystemModelDto: システムモデルDTO。

        Raises:
            ValueError: 必須引数がNoneの場合。

        Note:
            ドメイン層計算・クランプ処理には
            ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を用い、
            ドメイン関数の既定値に依存しないこと。
        """
        pass
