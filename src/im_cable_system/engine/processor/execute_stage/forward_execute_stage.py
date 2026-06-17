"""IM ケーブルシステム ExecuteStage（forward 実行）。

InputDtos を受け取り、各 InputDto に対して
:class:`ForwardExecutionOrchestratorFactory` で Direct/Iteration を選択し、
その ``execute`` を適用して ItmDtos を返す。

逐次／並列は :class:`DataProcessingStrategyFactory` が config から決定する。
結果 ItmDtos のダンプは共通関数 :func:`dump_itm_dtos_if_enabled` に委譲する。
CartesianGrid / OperatingPoints の差は InputStage 側で吸収されるため、
forward の ExecuteStage は本モジュール 1 つで両モードを扱う。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardExecutionOrchestratorFactory,
)
from im_cable_system.engine.processor.execute_stage.dump_itm_dto import (
    dump_itm_dtos_if_enabled,
)
from im_cable_system.engine.processor.execute_stage.strategy import (
    DataProcessingStrategyFactory,
    IDataProcessingStrategy,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
    ItmDtos,
)


class ForwardExecuteStage(IStage[InputDtos, ItmDtos]):
    """forward 実行用 ExecuteStage。

    各 InputDto ごとに :class:`ForwardExecutionOrchestratorFactory` で
    Direct/Iteration を選び、その ``execute`` を適用する。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        strategy: IDataProcessingStrategy,
    ) -> None:
        """初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            strategy: 逐次／並列のデータ処理戦略。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._strategy: IDataProcessingStrategy = strategy

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IStage[InputDtos, ItmDtos]:
        """インスタンスを生成する。"""
        strategy = DataProcessingStrategyFactory.create(
            config=config,
            logger=logger,
        )
        return cls(
            config=config,
            logger=logger,
            strategy=strategy,
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def process(self, dtos: InputDtos) -> ItmDtos:
        """InputDtos 全件を forward 実行して ItmDtos を返す。"""
        items: list[ItmDto] = self._strategy.process(
            items=dtos.get_all(),
            process_func=self._execute_one,
        )
        result = ItmDtos(objects=items)
        dump_itm_dtos_if_enabled(
            config=self._config,
            logger=self._logger,
            dtos=result,
        )
        return result

    def _execute_one(self, input_dto: InputDto) -> ItmDto:
        """1 件の InputDto に対し Direct/Iteration を選び execute する。"""
        forward = ForwardExecutionOrchestratorFactory.create(
            config=self._config,
            logger=self._logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )
        return forward.execute(input_dto)
