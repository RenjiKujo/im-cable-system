"""IM ケーブルシステム・estimate_params パイプライン実装。

1 つの :class:`EstimateParamsJobSpec`（統合 TSV 1 つ）を入力に取り、
``InputStage`` → ``ExecuteStage`` → ``OutputStage`` の 3 段を直列に
連結する。複数 TSV をまとめて処理したい場合は、呼び出し側でループする。
"""

from __future__ import annotations

from im_cable_system.engine.pipeline.i_pipeline import IPipeline
from im_cable_system.engine.processor.execute_stage import (
    EstimateParamsExecuteStage,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.processor.input_stage import (
    EstimateParamsInputStage,
)
from im_cable_system.engine.processor.output_stage import (
    EstimateParamsOutputStage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.input import (
    InputDtos,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDtos,
)
from im_cable_system.engine.shared.dto.output import (
    OutputDtos,
)
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


class EstimateParamsPipeline(IPipeline[EstimateParamsJobSpec, OutputDtos]):
    """job_spec → Input → estimate_params Execute → Output を連結する。

    実行時入力は :class:`EstimateParamsJobSpec` 1 件。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        input_stage: IStage[EstimateParamsJobSpec, InputDtos],
        execute_stage: IStage[InputDtos, ItmDtos],
        output_stage: IStage[ItmDtos, OutputDtos],
    ) -> None:
        """初期化する。

        Args:
            config: 設定。
            logger: ロガー。
            input_stage: Input ステージ。
            execute_stage: Execute ステージ。
            output_stage: Output ステージ。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._input_stage: IStage[EstimateParamsJobSpec, InputDtos] = (
            input_stage
        )
        self._execute_stage: IStage[InputDtos, ItmDtos] = execute_stage
        self._output_stage: IStage[ItmDtos, OutputDtos] = output_stage

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IPipeline[EstimateParamsJobSpec, OutputDtos]:
        """パイプラインを生成する。

        各ステージを ``IStage.create`` で生成し、コンストラクタへ注入する。
        """
        return cls(
            config=config,
            logger=logger,
            input_stage=EstimateParamsInputStage.create(
                config=config,
                logger=logger,
            ),
            execute_stage=EstimateParamsExecuteStage.create(
                config=config,
                logger=logger,
            ),
            output_stage=EstimateParamsOutputStage.create(
                config=config,
                logger=logger,
            ),
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def run(self, input: EstimateParamsJobSpec) -> OutputDtos:
        """パイプラインを実行する。

        Args:
            input: 統合 TSV 1 つを指す :class:`EstimateParamsJobSpec`。
        """
        input_dtos = self._input_stage.process(input)
        itm_dtos = self._execute_stage.process(input_dtos)
        return self._output_stage.process(itm_dtos)
