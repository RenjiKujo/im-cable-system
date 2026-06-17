"""IM電力計算器インターフェース（im_cable_system）。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
    ItmImPowerDto,
    ItmImVoltageCurrentDto,
)


class IImPowerCalculator(ABC):
    """IM電力計算器のインターフェース。"""

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> IImPowerCalculator:
        """計算器インスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IImPowerCalculator: 生成された計算器インスタンス。
        """

    @abstractmethod
    def calculate(
        self,
        im_model: ItmImModelDto,
        im_voltage_current: ItmImVoltageCurrentDto,
    ) -> ItmImPowerDto:
        """IM電力DTOを構築する。

        Args:
            im_model: IMモデルDTO。
            im_voltage_current: IM電圧・電流DTO。

        Returns:
            ItmImPowerDto: IM電力DTO。
        """
