"""Simulation実行全体オーケストレーター実装（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.orchestrate import (  # noqa: E501
    CharacteristicsCalculationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.i_simulation_orchestrator import (  # noqa: E501
    ISimulationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.orchestrate.numerical_stability_report_factory import (  # noqa: E501
    build_numerical_stability_report,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.orchestrate.simulation_numerical_stability_report_slot import (  # noqa: E501
    publish_simulation_numerical_stability_report,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power import (  # noqa: E501
    PowerCalculationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current import (  # noqa: E501
    VoltageCurrentCalculationOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.itm import (
    ItmCharacteristicDto,
    ItmModelDto,
    ItmPowerDto,
    ItmSimulationDto,
    ItmVoltageCurrentDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    NumericalStabilityAccumulator,
    numerical_stability_scope,
)


class SimulationOrchestrator(ISimulationOrchestrator):
    """Simulation実行全体オーケストレーター実装。

    `ItmModelDto` を入力として、以下の順で計算を実行し、
    `ItmSimulationDto` を構築して返す。
    数値安定レポートは :func:`publish_simulation_numerical_stability_report`
    により別途公開する。

    - 電流電圧計算 → 電力計算 → 特性値計算
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ISimulationOrchestrator:
        """オーケストレーターのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    # NOTE: 小さい入力だとミリ秒未満になりログがノイズ化しやすいため、
    # 一定時間以上の処理のみタイマーを出力する。
    @timer(logger=None, line="#", min_duration=0.1)
    def calculate(self, model_dto: ItmModelDto) -> ItmSimulationDto:
        """simulate全体を実行し、統合DTOを返す。

        Args:
            model_dto: モデルDTO（`array_layout`, `im`, `cable`, `system`を含む）。

        Returns:
            ItmSimulationDto: シミュレーション結果DTO。
        """
        with numerical_stability_scope() as accumulator:
            voltage_current_dto = self._calculate_voltage_current(
                model_dto=model_dto
            )
            power_dto = self._calculate_power(
                model_dto=model_dto,
                voltage_current_dto=voltage_current_dto,
            )
            characteristic_dto = self._calculate_characteristic(
                model_dto=model_dto,
                power_dto=power_dto,
            )
            return self._build_output(
                voltage_current_dto=voltage_current_dto,
                power_dto=power_dto,
                characteristic_dto=characteristic_dto,
                accumulator=accumulator,
            )

    def calculate_voltage_current_only(
        self, model_dto: ItmModelDto
    ) -> ItmSimulationDto:
        """電流電圧計算のみ実行し、シミュレーション結果DTOを返す。

        power と characteristic は None。電流反復の収束判定など、
        電圧電流結果のみ必要な場合に用いる。

        Args:
            model_dto: モデルDTO（`array_layout`, `im`, `cable`, `system`を含む）。

        Returns:
            ItmSimulationDto:
                voltage_current のみ設定、power/characteristic は None。
        """
        with numerical_stability_scope() as accumulator:
            voltage_current_dto = self._calculate_voltage_current(
                model_dto=model_dto
            )
            return self._build_output(
                voltage_current_dto=voltage_current_dto,
                power_dto=None,
                characteristic_dto=None,
                accumulator=accumulator,
            )

    def _calculate_voltage_current(
        self, model_dto: ItmModelDto
    ) -> ItmVoltageCurrentDto:
        """電流電圧計算を実行する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=self._config,
            logger=self._logger,
        )
        return orchestrator.calculate(model_dto=model_dto)

    def _calculate_power(
        self,
        model_dto: ItmModelDto,
        voltage_current_dto: ItmVoltageCurrentDto,
    ) -> ItmPowerDto:
        """電力計算を実行する。"""
        orchestrator = PowerCalculationOrchestrator.create(
            config=self._config,
            logger=self._logger,
        )
        return orchestrator.calculate(
            model_dto=model_dto,
            voltage_current_dto=voltage_current_dto,
        )

    def _calculate_characteristic(
        self,
        model_dto: ItmModelDto,
        power_dto: ItmPowerDto,
    ) -> ItmCharacteristicDto:
        """特性値計算を実行する。"""
        orchestrator = CharacteristicsCalculationOrchestrator.create(
            config=self._config,
            logger=self._logger,
        )
        return orchestrator.calculate(
            model_dto=model_dto,
            power_dto=power_dto,
        )

    def _build_output(
        self,
        voltage_current_dto: ItmVoltageCurrentDto,
        power_dto: ItmPowerDto | None,
        characteristic_dto: ItmCharacteristicDto | None,
        accumulator: NumericalStabilityAccumulator,
    ) -> ItmSimulationDto:
        """シミュレーション結果DTOを構築する。

        数値安定化イベントの集計は per-itm の CSV レポート
        （``report_numerical_stability_*.csv``）と
        ``OutputDto.numerical_stability_report`` に集約されるため、ここでは
        ログ出力せず、収集結果の公開のみ行う。
        """
        report = build_numerical_stability_report(accumulator=accumulator)
        publish_simulation_numerical_stability_report(report=report)
        return ItmSimulationDto(
            voltage_current=voltage_current_dto,
            power=power_dto,
            characteristic=characteristic_dto,
        )
