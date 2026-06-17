"""EstimateParams 用 Input オーケストレーター。

1 つの :class:`EstimateParamsJobSpec`（統合 TSV 1 つ）に対して
:class:`InputDtos`（候補直積分の :class:`InputDto`）を返す。
4 段フロー（``_validate_job_spec`` → ``_load_data`` →
``_assemble_input_dto`` → ``_validate_input_dto``）の順で呼び出される。

候補直積に対する for ループの設計方針:
    EstimateParams は「1 TSV → 複数 LoadedData → 複数 InputDto」のように
    複数件を扱うが、for を **どこで回すか** はステージ間の責務分担で決める。

    - ``_load_data``: **Loader 内部で for を回す**。
      候補軸（``im_primary`` / ``im_excitation`` / ``im_secondary`` /
      ``cable_conductor``）や cable_length・double_cage 判定は TSV を
      パースしないと分からないため、直積展開は Loader の責務に閉じる。
      Orchestrator 側で for を回そうとすると、Loader の内部手順
      （``parse`` → ``iter_combos`` → ``build_one``）を Orchestrator に
      漏らす必要があり、責務が濁る。
    - ``_assemble_input_dto`` / ``_validate_input_dto``:
      **Orchestrator 側で for を回す**。
      ここまで来れば対象は ``LoadedData`` / ``InputDto`` の集合になって
      いるので、個別処理（1 件 → 1 件変換 / 1 件検証）は
      :class:`IInputDtoAssembler` / Validator に委ね、複数件の順序制御
      だけを Orchestrator に置く。これにより Forward と粒度を揃え、
      Assembler / Validator は「単一件処理」の単純な契約に保てる。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto import (
    IInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.estimate_params import (  # noqa: E501
    EstimateParamsAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.estimate_params_input_loaded_data import (  # noqa: E501
    EstimateParamsInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.loader import (  # noqa: E501
    EstimateParamsLoader,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.i_data_loader import (  # noqa: E501
    IInputDataLoader,
)
from im_cable_system.engine.algorithm.input_algorithm.orchestrate.estimate_params.i_estimate_params_input_orchestrator import (  # noqa: E501
    IEstimateParamsInputOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto import (  # noqa: E501
    EstimateParamsInputDtoValidator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec import (
    EstimateParamsJobSpecValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


class EstimateParamsInputOrchestrator(IEstimateParamsInputOrchestrator):
    """1 ジョブの統合 TSV を 1 回読み、候補直積の InputDtos を返す。"""

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        loader: IInputDataLoader[
            EstimateParamsJobSpec,
            tuple[EstimateParamsInputLoadedData, ...],
        ],
        assembler: IInputDtoAssembler[EstimateParamsInputLoadedData,],
        job_spec_validator: EstimateParamsJobSpecValidator,
        input_dto_validator: EstimateParamsInputDtoValidator,
    ) -> None:
        """初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._loader: IInputDataLoader[
            EstimateParamsJobSpec,
            tuple[EstimateParamsInputLoadedData, ...],
        ] = loader
        self._assembler: IInputDtoAssembler[EstimateParamsInputLoadedData,] = (
            assembler
        )
        self._job_spec_validator: EstimateParamsJobSpecValidator = (
            job_spec_validator
        )
        self._input_dto_validator: EstimateParamsInputDtoValidator = (
            input_dto_validator
        )

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> EstimateParamsInputOrchestrator:
        """オーケストレーターを生成する。"""
        return cls(
            config=config,
            logger=logger,
            loader=EstimateParamsLoader.create(config=config, logger=logger),
            assembler=EstimateParamsAssembler.create(
                config=config,
                logger=logger,
            ),
            job_spec_validator=EstimateParamsJobSpecValidator.create(
                config=config,
                logger=logger,
            ),
            input_dto_validator=EstimateParamsInputDtoValidator.create(
                config=config,
                logger=logger,
            ),
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def build_input_dto(
        self,
        input_data: EstimateParamsJobSpec,
    ) -> InputDtos:
        """ジョブ spec から InputDtos を構築する。"""
        self._validate_job_spec(input_data)
        loaded_tuple = self._load_data(input_data)
        built = self._assemble_input_dto(loaded_tuple)
        self._validate_input_dto(built)
        return built

    def _validate_job_spec(self, input_data: EstimateParamsJobSpec) -> None:
        """ジョブ spec を検証する。"""
        self._job_spec_validator.validate(input_data)

    def _load_data(
        self,
        input_data: EstimateParamsJobSpec,
    ) -> tuple[EstimateParamsInputLoadedData, ...]:
        """統合 TSV を 1 回パースし、直積展開済みの LoadedData タプルを返す。

        直積展開の for ループは Loader 側に閉じる。候補軸・cable_length・
        double_cage 判定が TSV パース結果に依存するため、Orchestrator が
        for を持つと Loader 内部手順を漏らすことになる（モジュール
        docstring の設計方針を参照）。
        """
        return self._loader.load(input_data)

    def _assemble_input_dto(
        self,
        loaded_data: tuple[EstimateParamsInputLoadedData, ...],
    ) -> InputDtos:
        """直積分の LoadedData から各 InputDto を組み立てる。

        ここでの for ループは Orchestrator の責務。
        :class:`EstimateParamsAssembler` は ``LoadedData 1 件 →
        InputDto 1 件`` の純な変換に閉じ、複数件の束ね方は本メソッドが
        担う（モジュール docstring の設計方針を参照）。
        """
        built: list[InputDto] = [
            self._assembler.assemble(loaded_data=item) for item in loaded_data
        ]
        return InputDtos(objects=built)

    def _validate_input_dto(self, input_dto: InputDtos) -> None:
        """組み立て後の各 InputDto を検証する。

        ここでの for ループも Orchestrator の責務。
        :class:`EstimateParamsInputDtoValidator` は ``InputDto 1 件``
        の検証に閉じ、複数件のループは本メソッドが担う
        （モジュール docstring の設計方針を参照）。
        """
        for one in input_dto.get_all():
            self._input_dto_validator.validate(one)
