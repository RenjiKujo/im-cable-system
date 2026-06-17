"""ケーブル電力計算器インターフェース（im_cable_system）。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCableModelDto,
    ItmCablePowerDto,
    ItmCableVoltageCurrentDto,
)


class ICablePowerCalculator(ABC):
    """ケーブル電力計算器のインターフェース。"""

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> ICablePowerCalculator:
        """計算器インスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ICablePowerCalculator: 生成された計算器インスタンス。
        """

    @abstractmethod
    def calculate(
        self,
        cable_model: ItmCableModelDto,
        cable_voltage_current: ItmCableVoltageCurrentDto,
    ) -> ItmCablePowerDto:
        """ケーブル電力DTOを構築する。

        Args:
            cable_model: ケーブルモデルDTO。
            cable_voltage_current: ケーブル電圧・電流DTO。

        Returns:
            ItmCablePowerDto: ケーブル電力DTO。
        """
