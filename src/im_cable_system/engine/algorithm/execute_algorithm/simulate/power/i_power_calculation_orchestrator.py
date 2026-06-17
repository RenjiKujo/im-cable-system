"""電力計算オーケストレーターのインターフェース（im_cable_system）。

設計方針（execute_algorithm の最上位 IF / ISimulationOrchestrator と形態を揃える）:
    - ``create(config, logger)`` と公開実行メソッド ``calculate`` で完結させる。
      下位計算器の組み立ては ``calculate`` 内部の private 処理に閉じ、計算器
      インスタンスを跨いで保持・再利用しない。
    - ``_calculate_cable_power`` / ``_calculate_im_power`` を ``@abstractmethod``
      として明示し、「calculate が何を順に呼ぶか」を IF の契約として固定する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCablePowerDto,
    ItmImPowerDto,
    ItmModelDto,
    ItmPowerDto,
    ItmVoltageCurrentDto,
)


class IPowerCalculationOrchestrator(ABC):
    """電力計算オーケストレーターのインターフェース。

    電圧・電流の計算結果とモデル情報から、電力DTO（IM電力・ケーブル電力）を構築する。

    メソッドの並び（呼び出し順）: ``create(config, logger)`` → ``calculate``。
    ``calculate`` は内部で ``_calculate_cable_power`` → ``_calculate_im_power``
    を呼ぶ。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IPowerCalculationOrchestrator:
        """オーケストレーターのインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IPowerCalculationOrchestrator: 生成されたインスタンス。
        """

    @abstractmethod
    def calculate(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmPowerDto:
        """電力を計算してDTOを構築する。

        ``_calculate_cable_power → _calculate_im_power`` をこの順に実行し、
        結果を統合する。各 private メソッド内で必要な計算器を生成する。

        Args:
            model_dto: モデルDTO。
            voltage_current_dto: 電圧・電流シミュレーション結果DTO。

        Returns:
            ItmPowerDto: 電力シミュレーション結果DTO。
        """

    @abstractmethod
    def _calculate_cable_power(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmCablePowerDto:
        """ケーブル電力を計算する。

        ケーブル電力計算器を生成して計算する。calculate が内部で呼ぶ。
        外部からは直接呼ばない想定。

        Args:
            model_dto: モデルDTO。
            voltage_current_dto: 電圧・電流シミュレーション結果DTO。

        Returns:
            ItmCablePowerDto: ケーブル電力DTO。
        """

    @abstractmethod
    def _calculate_im_power(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmImPowerDto:
        """IM電力を計算する。

        ``cage_multiplicity`` に応じた IM 電力計算器を生成して計算する。
        calculate が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            model_dto: モデルDTO。
            voltage_current_dto: 電圧・電流シミュレーション結果DTO。

        Returns:
            ItmImPowerDto: IM電力DTO。
        """
