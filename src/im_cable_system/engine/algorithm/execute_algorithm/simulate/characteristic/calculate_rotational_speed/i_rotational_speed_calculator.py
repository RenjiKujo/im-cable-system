from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayRotationalSpeedDto,
)


class IRotationalSpeedCalculator(ABC):
    """回転速度計算器のインターフェース。

    周波数・極数・すべりから回転速度（rad/s）を計算する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IRotationalSpeedCalculator:
        """回転速度計算器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IRotationalSpeedCalculator: 生成された計算器インスタンス。
        """

    @abstractmethod
    def calculate(
        self, *, array_layout: ArrayLayoutDto, poles: int
    ) -> ArrayRotationalSpeedDto:
        """回転速度を計算する。

        Args:
            array_layout: 配列レイアウトDTO（少なくとも `slip`, `frequency` を含む）。
            poles: 極数。

        Returns:
            ArrayRotationalSpeedDto: 回転速度配列DTO（基本単位: rad/s）。

        Raises:
            ValueError: 必要な軸が存在しない場合、または計算に失敗した場合。
        """
