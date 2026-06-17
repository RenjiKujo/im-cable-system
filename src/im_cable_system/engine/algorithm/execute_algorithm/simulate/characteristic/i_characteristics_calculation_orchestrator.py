"""特性値計算オーケストレーターのインターフェース（im_cable_system）。

設計方針（execute_algorithm の最上位 IF / ISimulationOrchestrator と形態を揃える）:
    - ``create(config, logger)`` と公開実行メソッド ``calculate`` で完結させる。
      下位計算器の組み立ては ``calculate`` 内部の private 処理に閉じ、計算器
      インスタンスを跨いで保持・再利用しない。
    - ``_calculate_rotational_speed`` / ``_calculate_torque`` /
      ``_calculate_efficiency`` を ``@abstractmethod`` として明示し、
      「calculate が何を順に呼ぶか」を IF の契約として固定する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCharacteristicDto,
    ItmEfficiencyDto,
    ItmModelDto,
    ItmPowerDto,
    ItmRotationalSpeedDto,
    ItmTorqueDto,
)


class ICharacteristicsCalculationOrchestrator(ABC):
    """特性値計算オーケストレーターのインターフェース。

    回転速度・トルク・効率の計算を統括し、`ItmCharacteristicDto` を構築する。

    メソッドの並び（呼び出し順）: ``create(config, logger)`` → ``calculate``。
    ``calculate`` は内部で ``_calculate_rotational_speed`` →
    ``_calculate_torque`` → ``_calculate_efficiency`` をこの順に呼ぶ。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ICharacteristicsCalculationOrchestrator:
        """オーケストレーターのインスタンスを生成する。"""

    @abstractmethod
    def calculate(
        self,
        *,
        model_dto: ItmModelDto,
        power_dto: ItmPowerDto,
    ) -> ItmCharacteristicDto:
        """特性値を計算し、統合DTOを返す。

        ``_calculate_rotational_speed → _calculate_torque →
        _calculate_efficiency`` をこの順に実行し、結果を統合する。各 private
        メソッド内で必要な計算器を生成する。

        Args:
            model_dto: モデルDTO。
            power_dto: 電力DTO。

        Returns:
            ItmCharacteristicDto: 特性値計算結果DTO。
        """

    @abstractmethod
    def _calculate_rotational_speed(
        self,
        model_dto: ItmModelDto,
    ) -> ItmRotationalSpeedDto:
        """回転速度を計算する。

        回転速度計算器を生成して計算する。calculate が内部で呼ぶ。
        外部からは直接呼ばない想定。

        Args:
            model_dto: モデルDTO。

        Returns:
            ItmRotationalSpeedDto: 回転速度特性値DTO（基本単位: rad/s）。
        """

    @abstractmethod
    def _calculate_torque(
        self,
        power_dto: ItmPowerDto,
        rotational_speed: ItmRotationalSpeedDto,
    ) -> ItmTorqueDto:
        """トルクを計算する。

        トルク計算器を生成して計算する。calculate が内部で呼ぶ。
        外部からは直接呼ばない想定。

        Args:
            power_dto: 電力DTO。
            rotational_speed: 回転速度特性値DTO。

        Returns:
            ItmTorqueDto: トルク特性値DTO（基本単位: N·m）。
        """

    @abstractmethod
    def _calculate_efficiency(
        self,
        power_dto: ItmPowerDto,
    ) -> ItmEfficiencyDto:
        """効率を計算する。

        効率計算器を生成して計算する。calculate が内部で呼ぶ。
        外部からは直接呼ばない想定。

        Args:
            power_dto: 電力DTO。

        Returns:
            ItmEfficiencyDto: 効率特性値DTO。
        """
