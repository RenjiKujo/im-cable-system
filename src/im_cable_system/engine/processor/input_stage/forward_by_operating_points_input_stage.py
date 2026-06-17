"""forward_by_operating_points 用 Input ステージ（job spec を Input DTO に変換）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardInputOrchestrator,
    IForwardInputOrchestrator,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.processor.input_stage.dump_input_dto import (
    dump_input_dtos_if_enabled,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpecs,
)


class ForwardByOperatingPointsInputStage(
    IStage[ForwardJobSpecs, InputDtos],
):
    """``ForwardJobSpecs`` から OperatingPoints 用 :class:`InputDtos` を構築する。

    ``process`` に :class:`ForwardJobSpecs`（``ForwardJobSpec`` の束）を
    渡す。各 spec はシリーズ選択 TSV / 軸 TSV / optional 性能曲線 TSV
    の各パスを保持する。カタログ YAML は Config 経由で解決する。
    OperatingPoints モードでは ``reference_axes = [SLIP]`` を
    ``ForwardInputOrchestrator`` に渡し、co-indexed な
    ``ArrayLayoutDto`` を構築する。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        input_orchestrator: IForwardInputOrchestrator,
    ) -> None:
        """初期化する。

        Args:
            config: アプリ設定。
            logger: ロガー。
            input_orchestrator: Input オーケストレーター。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._input_orchestrator: IForwardInputOrchestrator = input_orchestrator

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IStage[ForwardJobSpecs, InputDtos]:
        """ステージインスタンスを生成する。

        OperatingPoints モードの ``reference_axes = [SLIP]`` を渡して Input
        オーケストレーターを生成し、注入する。
        """
        input_orchestrator = ForwardInputOrchestrator.create(
            config=config,
            logger=logger,
            reference_axes=[ArrayKey.SLIP],
        )
        return cls(
            config=config,
            logger=logger,
            input_orchestrator=input_orchestrator,
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def process(
        self,
        job_specs: ForwardJobSpecs,
    ) -> InputDtos:
        """各 spec に対して 1 つずつ :class:`InputDto` を構築する。

        Args:
            job_specs: ジョブ spec の束。各 spec がシリーズ選択 TSV /
                軸 TSV / optional 性能曲線 TSV のパスを保持する。

        Returns:
            InputDtos: 組み立てた InputDto の集合。
        """
        if not job_specs.specs:
            return InputDtos(objects=[])

        built: list[InputDto] = [
            self._input_orchestrator.build_input_dto(spec)
            for spec in job_specs.specs
        ]
        result = InputDtos(objects=built)
        dump_input_dtos_if_enabled(
            config=self._config,
            logger=self._logger,
            dtos=result,
        )
        return result
