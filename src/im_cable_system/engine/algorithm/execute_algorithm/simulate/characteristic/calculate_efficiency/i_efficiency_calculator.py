from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmEfficiencyDto,
    ItmPowerDto,
)


class IEfficiencyCalculator(ABC):
    """効率計算器のインターフェース。

    入力電力と出力電力から効率を計算する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> IEfficiencyCalculator:
        """効率計算器のインスタンスを生成するファクトリーメソッド。"""

    @abstractmethod
    def calculate(self, *, power_dto: ItmPowerDto) -> ItmEfficiencyDto:
        """効率を計算する。

        Args:
            power_dto: 電力DTO（入力電力・出力電力が必要）。

        Returns:
            ItmEfficiencyDto: 効率特性値DTO。

        Raises:
            ValueError: 計算に失敗した場合。
        """
