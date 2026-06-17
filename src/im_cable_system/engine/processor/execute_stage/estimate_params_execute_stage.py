"""IM ケーブルシステム ExecuteStage（パラメータ推定 estimate_params）。

InputDtos を受け取り、各 InputDto に
:class:`EstimateParamsOrchestrator` の ``execute`` を適用して ItmDtos を返す。
各 Input に ``im_pc_catalogs`` が少なくとも 1 件必須（空は execute 時にエラー）。

逐次／並列は :class:`DataProcessingStrategyFactory` が config から決定する。
結果 ItmDtos のダンプは共通関数 :func:`dump_itm_dtos_if_enabled` に委譲する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm import (
    IExecuteAlgorithmsOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params import (  # noqa: E501
    EstimateParamsOrchestrator,
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


class EstimateParamsExecuteStage(IStage[InputDtos, ItmDtos]):
    """パラメータ推定用 ExecuteStage。"""

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        orchestrator: IExecuteAlgorithmsOrchestrator[InputDto, ItmDto],
        strategy: IDataProcessingStrategy,
    ) -> None:
        """初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            orchestrator: 各 InputDto に適用する推定オーケストレーター。
            strategy: 逐次／並列のデータ処理戦略。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._orchestrator: IExecuteAlgorithmsOrchestrator[InputDto, ItmDto] = (
            orchestrator
        )
        self._strategy: IDataProcessingStrategy = strategy

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IStage[InputDtos, ItmDtos]:
        """インスタンスを生成する。"""
        orchestrator = EstimateParamsOrchestrator.create(
            config=config,
            logger=logger,
        )
        strategy = DataProcessingStrategyFactory.create(
            config=config,
            logger=logger,
        )
        return cls(
            config=config,
            logger=logger,
            orchestrator=orchestrator,
            strategy=strategy,
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def process(self, dtos: InputDtos) -> ItmDtos:
        """InputDtos 全件をパラメータ推定実行して ItmDtos を返す。"""
        items: list[ItmDto] = self._strategy.process(
            items=dtos.get_all(),
            process_func=self._orchestrator.execute,
        )
        result = ItmDtos(objects=items)
        dump_itm_dtos_if_enabled(
            config=self._config,
            logger=self._logger,
            dtos=result,
        )
        return result
