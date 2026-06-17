"""Simulation実行全体オーケストレーターのインターフェース（im_cable_system）。

このモジュールは、IMケーブルシステムの simulate（電流電圧→電力→特性値）を
統括するオーケストレーターの契約を定義します。オーケストレーターの IF は、
実装（および公開窓口）が置かれる ``orchestrate`` サブパッケージの
**親 Dir（simulate 直下）** に配置する。

設計方針（execute_algorithm の最上位 IF と形態を揃える）:
    - ``create(config, logger)`` と公開実行メソッド ``calculate(model_dto)`` /
      ``calculate_voltage_current_only(model_dto)`` で完結させる。下位
      オーケストレーターの組み立ては公開実行メソッド内部の private 処理に閉じ、
      構成インスタンスを跨いで保持・再利用しない。
    - ``_calculate_voltage_current`` / ``_calculate_power`` /
      ``_calculate_characteristic`` を ``@abstractmethod`` として明示し、
      「calculate が何を順に呼ぶか」を IF の契約として固定する
      （:class:`IExecuteAlgorithmsOrchestrator` と同じ
      「実行手順そのものを IF で握る」ポリシー）。

Note:
    数値安定化レポートは戻り値には含めない。実装が contextvar に公開するため、
    呼び出し側は ``calculate`` / ``calculate_voltage_current_only`` の直後に
    ``take_simulation_numerical_stability_report`` を 1 回呼び出すこと。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCharacteristicDto,
    ItmModelDto,
    ItmPowerDto,
    ItmSimulationDto,
    ItmVoltageCurrentDto,
)


class ISimulationOrchestrator(ABC):
    """Simulation実行全体オーケストレーターのインターフェース。

    単一の ``ItmModelDto`` を受け取り、電流電圧→電力→特性値の順序で計算して
    ``ItmSimulationDto`` を構築する。

    メソッドの並び（呼び出し順）: ``create(config, logger)`` →
    ``calculate`` または ``calculate_voltage_current_only``。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ISimulationOrchestrator:
        """config と logger を受け取り、自身のインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ISimulationOrchestrator: 生成されたインスタンス。
        """

    @abstractmethod
    def calculate(self, model_dto: ItmModelDto) -> ItmSimulationDto:
        """simulate 全体を実行し、統合 DTO を返す。

        ``_calculate_voltage_current → _calculate_power →
        _calculate_characteristic`` をこの順に実行し、各 private メソッド内で
        必要な計算オーケストレーターを生成する。

        Args:
            model_dto: モデル DTO（`array_layout`, `im`, `cable`, `system`を含む）。

        Returns:
            ItmSimulationDto: シミュレーション結果 DTO。
        """

    @abstractmethod
    def calculate_voltage_current_only(
        self, model_dto: ItmModelDto
    ) -> ItmSimulationDto:
        """電流電圧計算のみ実行し、シミュレーション結果 DTO を返す。

        power と characteristic は None。電力計算・特性値計算は行わない。
        電流反復（Iteration forward）の収束判定など、電圧電流結果のみ
        必要な場合に用いる。

        Args:
            model_dto: モデル DTO（`array_layout`, `im`, `cable`, `system`を含む）。

        Returns:
            ItmSimulationDto:
                voltage_current のみ設定、power/characteristic は None。
        """

    @abstractmethod
    def _calculate_voltage_current(
        self, model_dto: ItmModelDto
    ) -> ItmVoltageCurrentDto:
        """電流電圧計算を実行する。

        calculate が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            model_dto: モデル DTO。

        Returns:
            ItmVoltageCurrentDto: 電流電圧計算結果 DTO。
        """

    @abstractmethod
    def _calculate_power(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmPowerDto:
        """電力計算を実行する。

        calculate が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            model_dto: モデル DTO。
            voltage_current_dto: 電流電圧計算結果 DTO。

        Returns:
            ItmPowerDto: 電力計算結果 DTO。
        """

    @abstractmethod
    def _calculate_characteristic(
        self,
        model_dto: ItmModelDto,
        power_dto: ItmPowerDto,
    ) -> ItmCharacteristicDto:
        """特性値計算を実行する。

        calculate が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            model_dto: モデル DTO。
            power_dto: 電力計算結果 DTO。

        Returns:
            ItmCharacteristicDto: 特性値計算結果 DTO。
        """
