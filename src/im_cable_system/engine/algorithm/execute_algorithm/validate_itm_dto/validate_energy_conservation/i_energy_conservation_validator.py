"""エネルギー保存則検証のインターフェース（im_cable_system）。

このモジュールは、エネルギー保存則の検証を行うバリデータの
インターフェースを定義します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class IEnergyConservationValidator(ABC):
    """エネルギー保存則検証のインターフェース。

    電力における入出力と損失のバランスが、許容誤差内でエネルギー保存則を
    満たしているかを検証する。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IEnergyConservationValidator:
        """バリデータのインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IEnergyConservationValidator: 生成されたインスタンス。
        """

    @abstractmethod
    def validate(self, itm_dto: ItmDto) -> None:
        """エネルギー保存則を検証する。

        入力電力 = 出力電力 + 損失電力 が許容誤差内で成り立つことを検証する。

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）。
        """
