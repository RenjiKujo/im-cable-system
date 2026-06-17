"""電流・電圧レンジ検証のインターフェース（im_cable_system）。

このモジュールは、電流・電圧が定格値や設計上の許容範囲に収まっているかを
検証するバリデータのインターフェースを定義します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class ICurrentVoltageRangeValidator(ABC):
    """電流・電圧レンジ検証のインターフェース。

    各エンティティ（IM/ケーブル）の電流・電圧が、定格値や設計上の許容範囲に
    収まっているかを検証する。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ICurrentVoltageRangeValidator:
        """バリデータのインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ICurrentVoltageRangeValidator: 生成されたインスタンス。
        """

    @abstractmethod
    def validate(self, itm_dto: ItmDto) -> None:
        """電流・電圧レンジを検証する。

        各エンティティ（IM/ケーブル）の電流・電圧が、定格値や設計上の許容範囲に
        収まっているかを検証する。

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）。
        """
