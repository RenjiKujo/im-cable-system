"""電流電圧計算オーケストレーターのインターフェース定義。

このモジュールは、電流電圧計算を統括するオーケストレーターの
インターフェースを定義します。

設計方針（execute_algorithm の最上位 IF / ISimulationOrchestrator と形態を揃える）:
    - ``create(config, logger)`` と公開実行メソッド ``calculate(model_dto)`` で
      完結させる。下位計算器の組み立ては ``calculate`` 内部の private 処理に
      閉じ、計算器インスタンスを跨いで保持・再利用しない。
    - ``_calculate_cable_voltage_current`` / ``_calculate_im_voltage_current``
      を ``@abstractmethod`` として明示し、「calculate が何を順に呼ぶか」を
      IF の契約として固定する（:class:`IExecuteAlgorithmsOrchestrator` と同じ
      「実行手順そのものを IF で握る」ポリシー）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCableVoltageCurrentDto,
    ItmImVoltageCurrentDto,
    ItmModelDto,
    ItmVoltageCurrentDto,
)


class IVoltageCurrentCalculationOrchestrator(ABC):
    """電流電圧計算オーケストレーターのインターフェース。

    電流電圧計算を統括するオーケストレーターの契約を定義します。

    メソッドの並び（呼び出し順）: ``create(config, logger)`` → ``calculate``。
    ``calculate`` は内部で ``_calculate_cable_voltage_current`` →
    ``_calculate_im_voltage_current`` をこの順に呼ぶ。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IVoltageCurrentCalculationOrchestrator:
        """電流電圧計算オーケストレーターのインスタンスを生成する。

        Args:
            config: オーケストレーター生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IVoltageCurrentCalculationOrchestrator:
                生成されたオーケストレーターインスタンス。
        """
        pass

    @abstractmethod
    def calculate(
        self,
        model_dto: ItmModelDto,
    ) -> ItmVoltageCurrentDto:
        """各地点の電流電圧を計算する。

        ``_calculate_cable_voltage_current → _calculate_im_voltage_current`` を
        この順に実行し、結果を統合します。各 private メソッド内で必要な計算器を
        生成する。

        Args:
            model_dto: モデルDTO（`array_layout`, `im`, `cable`, `system`を含む）。

        Returns:
            ItmVoltageCurrentDto: 電圧・電流シミュレーション結果DTO。

        Raises:
            ValueError: 計算に失敗した場合。
        """
        pass

    @abstractmethod
    def _calculate_cable_voltage_current(
        self,
        model_dto: ItmModelDto,
    ) -> ItmCableVoltageCurrentDto:
        """ケーブル各地点の電流電圧を計算する。

        入力線間電圧の取得・ブロードキャストを行い、ケーブル計算器を生成して
        計算する。calculate が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            model_dto: モデルDTO。

        Returns:
            ItmCableVoltageCurrentDto: ケーブル各地点の電流電圧DTO。
        """
        pass

    @abstractmethod
    def _calculate_im_voltage_current(
        self,
        model_dto: ItmModelDto,
        cable_voltage_current: ItmCableVoltageCurrentDto,
    ) -> ItmImVoltageCurrentDto:
        """誘導電動機各地点の電流電圧を計算する。

        ``cage_multiplicity`` に応じた IM 計算器を生成して計算する。
        calculate が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            model_dto: モデルDTO。
            cable_voltage_current: ケーブル各地点の電流電圧DTO
                （終点の相電圧・相電流を IM 計算の入力に用いる）。

        Returns:
            ItmImVoltageCurrentDto: IM各地点の電流電圧DTO。
        """
        pass
