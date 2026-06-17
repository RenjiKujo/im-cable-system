"""Forward Input オーケストレーター（CartesianGrid / OperatingPoints 共通）。

両モードの違いは ``reference_axes`` の選び方だけなので、本オーケストレーターは
モード分岐を持たず、:meth:`create` の引数で受け取った ``reference_axes`` を
``ForwardInputDtoAssembler`` に渡すのみ。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto import (
    IInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.forward import (  # noqa: E501
    ForwardInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardInputLoadedData,
    ForwardLoader,
    IInputDataLoader,
)
from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward.i_forward_input_orchestrator import (  # noqa: E501
    IForwardInputOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto import (
    ForwardInputDtoValidator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec import (
    ForwardJobSpecValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)


class ForwardInputOrchestrator(IForwardInputOrchestrator):
    """Forward Input 4 段フローの共通オーケストレーター。

    ``_validate_job_spec`` → ``_load_data`` → ``_assemble_input_dto`` →
    ``_validate_input_dto`` の順で呼び出す。モード分岐は持たない。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        loader: IInputDataLoader[
            ForwardJobSpec,
            ForwardInputLoadedData,
        ],
        assembler: IInputDtoAssembler[ForwardInputLoadedData,],
        job_spec_validator: ForwardJobSpecValidator,
        input_dto_validator: ForwardInputDtoValidator,
    ) -> None:
        """初期化する。

        Args:
            config: 設定。開発ガイドライン（``docs/rules/``）の
                「``IConfig`` / ``ILogger`` は属性として保持する」ルールに従い保持する。
            logger: ロガー。``@timer`` デコレータ（``logger=None``）が
                ``self._logger`` を参照するためにも用いる。
            loader: 入力データローダー。
            assembler: InputDto アセンブラー。``reference_axes`` は
                生成時に注入済み。
            job_spec_validator: ジョブ spec バリデータ。
            input_dto_validator: InputDto バリデータ。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._loader: IInputDataLoader[
            ForwardJobSpec,
            ForwardInputLoadedData,
        ] = loader
        self._assembler: IInputDtoAssembler[ForwardInputLoadedData,] = assembler
        self._job_spec_validator: ForwardJobSpecValidator = job_spec_validator
        self._input_dto_validator: ForwardInputDtoValidator = (
            input_dto_validator
        )

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
        reference_axes: list[ArrayKey],
    ) -> ForwardInputOrchestrator:
        """オーケストレーターを生成する。

        Args:
            config: 設定。子コンポーネントに伝播する。
            logger: ロガー。``@timer`` 経由のログ出力と子への伝播に用いる。
            reference_axes: ``ArrayLayoutDto.reference_axes`` に渡す軸の
                順序付きリスト。CartesianGrid 用 ``[SLIP, INPUT_LINE_VOLTAGE,
                FREQUENCY]`` / OperatingPoints 用 ``[SLIP]`` を呼び出し側
                （InputStage）が選んで渡す。
        """
        return cls(
            config=config,
            logger=logger,
            loader=ForwardLoader.create(config=config, logger=logger),
            assembler=ForwardInputDtoAssembler.create(
                config=config,
                logger=logger,
                reference_axes=reference_axes,
            ),
            job_spec_validator=ForwardJobSpecValidator.create(
                config=config,
                logger=logger,
            ),
            input_dto_validator=ForwardInputDtoValidator.create(
                config=config,
                logger=logger,
            ),
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def build_input_dto(
        self,
        input_data: ForwardJobSpec,
    ) -> InputDto:
        """spec の各パスから InputDto を構築する。

        Args:
            input_data: 1 ジョブ分のパス束（``ForwardJobSpec``）。

        Returns:
            InputDto: 検証済み入力。

        Raises:
            ValueError: 検証失敗時。
        """
        self._validate_job_spec(input_data)
        loaded_data = self._load_data(input_data)
        assembled = self._assemble_input_dto(loaded_data)
        self._validate_input_dto(assembled)
        return assembled

    def _validate_job_spec(self, input_data: ForwardJobSpec) -> None:
        self._job_spec_validator.validate(input_data)

    def _load_data(
        self,
        input_data: ForwardJobSpec,
    ) -> ForwardInputLoadedData:
        return self._loader.load(input_data)

    def _assemble_input_dto(
        self,
        loaded_data: ForwardInputLoadedData,
    ) -> InputDto:
        return self._assembler.assemble(loaded_data=loaded_data)

    def _validate_input_dto(self, input_dto: InputDto) -> None:
        self._input_dto_validator.validate(input_dto)
