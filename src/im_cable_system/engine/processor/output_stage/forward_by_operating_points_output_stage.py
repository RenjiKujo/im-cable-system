"""forward_by_operating_points（運転点指定の順計算）の OutputStage。

各 Itm を Algorithm 層の
:class:`ForwardByOperatingPointsOutputOrchestrator` で出力 DTO へ変換する
（図・表は config 次第でファイル side effect）。estimate_params 固有の
レポートは出力しない。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.output_algorithm import (
    IOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.orchestrate import (
    ForwardByOperatingPointsOutputOrchestrator,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.processor.output_stage.dump_output_dto import (
    dump_output_dtos_if_enabled,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.itm import (
    ItmDtos,
)
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
    OutputDtos,
)


class ForwardByOperatingPointsOutputStage(IStage[ItmDtos, OutputDtos]):
    """運転点指定の順計算の Itm を出力 DTO へ変換する OutputStage。"""

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        output_orchestrator: IOutputOrchestrator,
    ) -> None:
        """初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            output_orchestrator: 出力オーケストレーター。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._output_orchestrator: IOutputOrchestrator = output_orchestrator

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IStage[ItmDtos, OutputDtos]:
        """インスタンスを生成する。

        出力オーケストレーターを生成し、注入する。
        """
        output_orchestrator = ForwardByOperatingPointsOutputOrchestrator.create(
            config=config,
            logger=logger,
        )
        return cls(
            config=config,
            logger=logger,
            output_orchestrator=output_orchestrator,
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def process(self, dtos: ItmDtos) -> OutputDtos:
        """Itm DTO 群を逐次で出力処理する。"""
        all_itm = dtos.get_all()
        if not all_itm:
            return OutputDtos(objects=[])

        items: list[OutputDto] = [
            self._output_orchestrator.run(itm_dto) for itm_dto in all_itm
        ]
        result = OutputDtos(objects=items)
        dump_output_dtos_if_enabled(
            config=self._config,
            logger=self._logger,
            dtos=result,
        )
        return result
