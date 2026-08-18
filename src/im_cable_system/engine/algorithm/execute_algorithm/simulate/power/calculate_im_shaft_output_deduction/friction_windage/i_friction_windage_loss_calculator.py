"""摩擦・風損計算器インターフェース（im_cable_system）。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


class IFrictionWindageLossCalculator(ABC):
    """摩擦・風損計算器のインターフェース。"""

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IFrictionWindageLossCalculator:
        """計算器インスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IFrictionWindageLossCalculator: 生成された計算器インスタンス。
        """

    @abstractmethod
    def calculate(
        self,
        im_model: ItmImModelDto,
        reference_shape: tuple[int, ...],
    ) -> ArrayComplexPowerDto:
        """摩擦・風損電力DTOを計算する。

        Args:
            im_model: IMモデルDTO（``friction_windage_model`` と
                ``nameplate_power`` を参照する）。
            reference_shape: 出力配列の形状（軸出力配列の形状に合わせる）。

        Returns:
            ArrayComplexPowerDto: 摩擦・風損電力DTO（虚部は常に0）。
        """
