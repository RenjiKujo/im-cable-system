from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayRotationalSpeedDto,
    ArrayTorqueDto,
)
from im_cable_system.engine.shared.dto.itm import ItmPowerDto


class ITorqueCalculator(ABC):
    """トルク計算器のインターフェース。

    IM出力電力と回転速度からトルクを計算する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig, logger: ILogger) -> ITorqueCalculator:
        """トルク計算器のインスタンスを生成するファクトリーメソッド。"""

    @abstractmethod
    def calculate(
        self,
        *,
        power_dto: ItmPowerDto,
        rotational_speed: ArrayRotationalSpeedDto,
    ) -> ArrayTorqueDto:
        """トルクを計算する。

        Args:
            power_dto: 電力DTO（IM出力電力が必要）。
            rotational_speed: 回転速度配列DTO（基本単位: rad/s）。

        Returns:
            ArrayTorqueDto: トルク配列DTO（基本単位: N·m）。

        Raises:
            ValueError: 計算に失敗した場合。
        """
