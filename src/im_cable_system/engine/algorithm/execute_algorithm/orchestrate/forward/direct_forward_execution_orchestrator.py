"""IM ケーブルシステム全体実行オーケストレーターの Direct 実装（forward）。

電流依存なし。1回 build_model + 1回 simulate + validate_itm_dto で完了する。
validate は電流・電圧レンジ以外（エネルギー保存・特性一貫性）を実行する。

設計メモ（``execute`` と ``execute_without_validation`` の関係）:
    本クラスでは ``execute`` を ``execute_without_validation`` のラッパーにせず、
    ``execute`` 側で ``_build_model → _simulate → _validate_itm_dto`` を明示的に
    展開する。``execute`` は本実装の正規ルートであり、ラッパー経由にすると
    「主要パス」と「最適化用パス」の主従が逆転して読みづらくなるため。

    一方 ``execute_without_validation`` は IF（:class:`IForwardExecutionOrchestrator`）
    の契約として保持する。これは ``EstimateParams`` のパラメータ推定ループ
    （``scipy.optimize.least_squares`` の残差評価）で **高頻度に呼ばれるため
    検証コストを払いたくない** ケースに使う正規ルートである。
    IF にこのメソッドを置かないと、呼び出し側が ``_build_model`` / ``_simulate``
    のような private を直接叩く規約違反に陥るため、契約として明示する。
    結果として Direct では実装が短くなるが、IF の対称性
    （Direct/Iteration とも ``execute_without_validation`` を提供）と
    呼び出し側の安全性を優先する。
"""

from __future__ import annotations

from dataclasses import replace

from im_cable_system.engine.algorithm.execute_algorithm.build_model import (  # noqa: E501
    IImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.i_forward_execution_orchestrator import (  # noqa: E501
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate import (  # noqa: E501
    ISimulationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.orchestrate import (  # noqa: E501
    SimulationOrchestrator,
    take_simulation_numerical_stability_report,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto import (  # noqa: E501
    IItmValidationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.orchestrate import (  # noqa: E501
    ItmValidationOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    numerical_stability_scope,
)


class DirectForwardExecutionOrchestrator(IForwardExecutionOrchestrator):
    """IM ケーブルシステム forward 実行オーケストレーター（Direct 実装）。

    create(config, logger) で生成する。シリーズ詳細は InputDto に埋め込まれる。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """オーケストレーターを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IForwardExecutionOrchestrator:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    # NOTE: 小さい入力だとミリ秒未満になりログがノイズ化しやすいため、
    # 一定時間以上の処理のみタイマーを出力する。
    @timer(logger=None, line="#", min_duration=0.01)
    def execute(self, input_dto: InputDto) -> ItmDto:
        """1本の InputDto に対して build_model → simulate → validate_itm_dto をこの順で実行する。

        本実装の正規ルート。``execute_without_validation`` を経由せず、
        ``_build_model → _simulate → _validate_itm_dto`` を直接展開する
        （理由はモジュール docstring「設計メモ」を参照）。
        """
        with numerical_stability_scope():
            itm_with_model = self._build_model(input_dto)
            itm_with_simulation = self._simulate(itm_with_model)
        self._validate_itm_dto(itm_with_simulation)
        return itm_with_simulation

    def execute_without_validation(self, input_dto: InputDto) -> ItmDto:
        """1本の InputDto に対して build_model とフル simulate まで実行する（検証なし）。

        ``EstimateParams`` の残差評価ループのように、同一入力に対して高頻度に
        forward を呼び出す用途で、``_validate_itm_dto`` のコストを避けるための
        正規ルート。IF 契約として提供する（モジュール docstring「設計メモ」参照）。
        """
        with numerical_stability_scope():
            itm_with_model = self._build_model(input_dto)
            return self._simulate(itm_with_model)

    def _build_model(self, input_dto: InputDto) -> ItmDto:
        """単一の入力 DTO から物理モデルを構築し、中間 DTO（simulation_result は未設定）を返す。"""
        build_orchestrator: IImCableModelBuildOrchestrator = (
            ImCableModelBuildOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        model_dto = build_orchestrator.build(input_dto)
        return ItmDto(
            name=input_dto.name,
            model=model_dto,
            simulation_result=None,
        )

    def _simulate(self, itm_dto: ItmDto) -> ItmDto:
        """単一の中間 DTO に対してシミュレーションを実行し、結果を付与した中間 DTO を返す。"""
        sim_orchestrator: ISimulationOrchestrator = (
            SimulationOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        simulation_dto = sim_orchestrator.calculate(model_dto=itm_dto.model)
        report = take_simulation_numerical_stability_report()
        return replace(
            itm_dto,
            simulation_result=simulation_dto,
            numerical_stability_report=report,
        )

    def _validate_itm_dto(self, itm_dto: ItmDto) -> None:
        """単一の中間 DTO の妥当性を検証する。"""
        validator: IItmValidationOrchestrator = (
            ItmValidationOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        validator.validate(itm_dto=itm_dto)
