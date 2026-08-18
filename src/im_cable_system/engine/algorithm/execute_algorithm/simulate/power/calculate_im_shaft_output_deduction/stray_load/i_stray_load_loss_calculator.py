"""漂遊負荷損計算器インターフェース（im_cable_system）。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


class IStrayLoadLossCalculator(ABC):
    """漂遊負荷損計算器のインターフェース。"""

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IStrayLoadLossCalculator:
        """計算器インスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IStrayLoadLossCalculator: 生成された計算器インスタンス。
        """

    @abstractmethod
    def calculate(
        self,
        im_model: ItmImModelDto,
        secondary_current: ArrayComplexCurrentDto,
    ) -> ArrayComplexPowerDto:
        """漂遊負荷損電力DTOを計算する。

        Args:
            im_model: IMモデルDTO（``stray_load_model``・``nameplate_power``・
                ``nameplate_current`` を参照する）。
            secondary_current: 二次側合計電流配列（基準電流）。

        Returns:
            ArrayComplexPowerDto: 漂遊負荷損電力DTO（虚部は常に0）。
        """
