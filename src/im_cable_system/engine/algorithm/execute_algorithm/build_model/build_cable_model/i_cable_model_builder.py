"""ケーブルモデル構築器のインターフェース。

CableDtosからItmCableModelDtoを構築する処理の契約を定義します。

Note:
    本インターフェースは、ケーブル等価回路のトポロジー（例: π型、T型、多重π型など）を
    実装クラスの差し替えで拡張できるようにするための契約です。
    現状はπ型（`PieCableModelBuilder`）のみをサポートしますが、
    将来的なトポロジー追加時には本インターフェースを実装するクラスを追加します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    CableDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableModelDto,
)


class ICableModelBuilder(ABC):
    """ケーブルモデル構築器のインターフェース。

    CableDtosからItmCableModelDtoを構築する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> ICableModelBuilder:
        """ケーブルモデル構築器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: ケーブルモデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ICableModelBuilder: 生成されたケーブルモデル構築器インスタンス。
        """
        pass

    @abstractmethod
    def build(
        self,
        cable_dto: CableDto | None,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmCableModelDto:
        """CableDtoからItmCableModelDtoを構築する。

        Args:
            cable_dto: ケーブルDTO。Noneの場合は、完全導体かつ完全絶縁の擬似ケーブルモデルを作成する。
            model_array_layout: 配列レイアウトDTO（必須）。

        Returns:
            ItmCableModelDto: 中間DTO。
                cable_dtoがNoneの場合、cable_infoはNoneとなる。

        Raises:
            ValueError: model_array_layoutがNoneの場合。
        """
        pass
