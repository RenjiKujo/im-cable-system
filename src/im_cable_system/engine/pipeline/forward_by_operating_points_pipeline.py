"""IM ケーブルシステム forward_by_operating_points パイプライン実装。"""

from __future__ import annotations

from im_cable_system.engine.pipeline.i_pipeline import IPipeline
from im_cable_system.engine.processor.execute_stage import (
    ForwardExecuteStage,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.processor.input_stage import (
    ForwardByOperatingPointsInputStage,
)
from im_cable_system.engine.processor.output_stage import (
    ForwardByOperatingPointsOutputStage,
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
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpecs,
)


class ForwardByOperatingPointsPipeline(
    IPipeline[
        ForwardJobSpecs,
        OutputDtos,
    ],
):
    """``ForwardJobSpecs`` → Input → Execute → Output を連鎖する。

    実行時入力は :class:`ForwardJobSpecs` であり、Workflow 等の呼び出し側
    から ``run(input=...)`` で渡される。運転点指定モードでは
    Input/Output のみ ``ForwardByCartesianGridPipeline`` と異なり、Execute は
    共通の :class:`ForwardExecuteStage` を用いる。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        input_stage: IStage[
            ForwardJobSpecs,
            InputDtos,
        ],
        execute_stage: IStage[
            InputDtos,
            ItmDtos,
        ],
        output_stage: IStage[
            ItmDtos,
            OutputDtos,
        ],
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
        self._input_stage: IStage[
            ForwardJobSpecs,
            InputDtos,
        ] = input_stage
        self._execute_stage: IStage[
            InputDtos,
            ItmDtos,
        ] = execute_stage
        self._output_stage: IStage[
            ItmDtos,
            OutputDtos,
        ] = output_stage

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IPipeline[
        ForwardJobSpecs,
        OutputDtos,
    ]:
        """パイプラインインスタンスを生成する。

        各ステージを ``IStage.create`` で生成し、コンストラクタへ注入する。
        """
        return cls(
            config=config,
            logger=logger,
            input_stage=ForwardByOperatingPointsInputStage.create(
                config=config,
                logger=logger,
            ),
            execute_stage=ForwardExecuteStage.create(
                config=config,
                logger=logger,
            ),
            output_stage=ForwardByOperatingPointsOutputStage.create(
                config=config,
                logger=logger,
            ),
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def run(
        self,
        input: ForwardJobSpecs,
    ) -> OutputDtos:
        """パイプラインを実行する。

        Args:
            input: ジョブ spec の束（``ForwardJobSpecs``）。
        """
        input_dtos = self._input_stage.process(input)
        itm_dtos = self._execute_stage.process(input_dtos)
        return self._output_stage.process(itm_dtos)
