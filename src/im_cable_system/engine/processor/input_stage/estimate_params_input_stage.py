"""estimate_params 用 Input ステージ（job spec を Input DTO に変換）。

1 つの :class:`EstimateParamsJobSpec`（統合 TSV 1 つ）を受け取り、
内部のオーケストレーターに委譲して候補直積分の :class:`InputDtos` を
返す薄いステージ。複数 TSV をまとめて流すユースケースは、本ステージ
を複数回呼び出す側で扱う。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.estimate_params import (  # noqa: E501
    EstimateParamsInputOrchestrator,
    IEstimateParamsInputOrchestrator,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.processor.input_stage.dump_input_dto import (
    dump_input_dtos_if_enabled,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.input import (
    InputDtos,
)
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


class EstimateParamsInputStage(IStage[EstimateParamsJobSpec, InputDtos]):
    """``EstimateParamsJobSpec`` から :class:`InputDtos` を構築する。

    ``process`` に :class:`EstimateParamsJobSpec`（統合 TSV 1 つ）を渡す
    と、内部の :class:`IEstimateParamsInputOrchestrator` に委譲して
    候補軸の直積分の :class:`InputDtos` を返す。複数 TSV をまとめて
    流すユースケースは、本ステージを複数回呼び出す側で扱う。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        input_orchestrator: IEstimateParamsInputOrchestrator,
    ) -> None:
        """初期化する。

        Args:
            config: アプリ設定。
            logger: ロガー。
            input_orchestrator: Input オーケストレーター。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._input_orchestrator: IEstimateParamsInputOrchestrator = (
            input_orchestrator
        )

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IStage[EstimateParamsJobSpec, InputDtos]:
        """ステージインスタンスを生成する。

        Input オーケストレーターを生成し、注入する。
        """
        input_orchestrator = EstimateParamsInputOrchestrator.create(
            config=config,
            logger=logger,
        )
        return cls(
            config=config,
            logger=logger,
            input_orchestrator=input_orchestrator,
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def process(self, job_spec: EstimateParamsJobSpec) -> InputDtos:
        """ジョブ spec を 1 件オーケストレーターに流して InputDtos を返す。

        Args:
            job_spec: 統合 TSV 1 つを指すジョブ spec。

        Returns:
            InputDtos: 候補軸の直積分の InputDto 集合。
        """
        result = self._input_orchestrator.build_input_dto(job_spec)
        dump_input_dtos_if_enabled(
            config=self._config,
            logger=self._logger,
            dtos=result,
        )
        return result
