"""誘導電動機（IM）モデル構築器のインターフェース定義。

このモジュールは、ImDtoからItmImModelDtoを構築する処理のインターフェースを定義します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    ImDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
)


class IImModelBuilder(ABC):
    """誘導電動機（IM）モデル構築器のインターフェース。

    ImDtoからItmImModelDtoを構築する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> IImModelBuilder:
        """誘導電動機（IM）モデル構築器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 誘導電動機（IM）モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImModelBuilder: 生成された誘導電動機（IM）モデル構築器インスタンス。
        """
        pass

    @abstractmethod
    def build(
        self,
        im_dto: ImDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImModelDto:
        """ImDtoからItmImModelDtoを構築する。

        Args:
            im_dto: 誘導電動機（IM）DTO（必須）。
            model_array_layout: 配列レイアウトDTO（必須）。

        Returns:
            ItmImModelDto: 中間DTO。

        Raises:
            ValueError: 必須引数がNoneの場合。
        """
        pass
