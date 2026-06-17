"""IM電圧電流計算器のインターフェース定義。

このモジュールは、IMの各地点の電圧・電流を計算する処理のインターフェースを定義します。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
    ItmImVoltageCurrentDto,
)


class IImVoltageCurrentCalculator(ABC):
    """IM電圧電流計算器のインターフェース。

    IMの各地点の電圧・電流を計算する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IImVoltageCurrentCalculator:
        """IM電圧電流計算器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImVoltageCurrentCalculator: 生成された計算器インスタンス。
        """
        pass

    @abstractmethod
    def calculate(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        im_model: ItmImModelDto,
    ) -> ItmImVoltageCurrentDto:
        """IM各地点の電圧・電流を計算し、`ItmImVoltageCurrentDto`を構築する。

        ケーブル終点の相電圧・相電流とIMモデル情報から、IM各地点の電圧・電流を計算し、
        `ItmImVoltageCurrentDto`を構築します。

        Args:
            input_phase_voltage: 入力相電圧DTO（ケーブル終点の相電圧、
                `ItmCableVoltageCurrentDto.end_point_phase_voltage`、
                配列形状は`ItmModelDto.array_layout`で定義）。
            input_phase_current: 入力相電流DTO（ケーブル終点の相電流、
                `ItmCableVoltageCurrentDto.end_point_phase_current`、
                配列形状は`ItmModelDto.array_layout`で定義）。
            im_model: IMモデルDTO（`ItmModelDto.im`、
                `primary_model`, `excitation_model`, `secondary_model`を含む）。

        Returns:
            ItmImVoltageCurrentDto: IM各地点の電圧・電流DTO
                （`im_input_*`, `im_primary_*`, `im_excitation_*`, `im_secondary_*`を含む）。

        Raises:
            ValueError: 計算に失敗した場合。
        """
        pass
