"""二重かご型誘導電動機（IM）モデル構築器。

ImDto から ItmImModelDto を構築する。二次は INNER/OUTER を別々に変換しマージし、
総合イミタンスは INNER/OUTER 二次アドミタンスの並列等価を経て L/T 合成する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.i_im_model_builder import (  # noqa: E501
    IImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance import (  # noqa: E501
    ImComponentImmittanceConverterFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary import (  # noqa: E501
    resolve_secondary_current_for_branch,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance import (  # noqa: E501
    DoubleCageImTotalImmittanceSynthesizerFactory,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    ImCageMultiplicityType,
    ImDto,
    ImSecondaryCageBranchType,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImBasicDto,
    ItmImCircuitDto,
    ItmImExcitationDto,
    ItmImModelDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
)


def merge_double_cage_itm_im_secondary_dto(
    inner_partial: ItmImSecondaryDto,
    outer_partial: ItmImSecondaryDto,
) -> ItmImSecondaryDto:
    """INNER/OUTER の部分 DTO を二重かご用 DTO にマージする。

    Args:
        inner_partial: INNER 枝のみの計算結果。
        outer_partial: OUTER 枝のみの計算結果。

    Returns:
        ItmImSecondaryDto: INNER/OUTER を両方含む二次側 DTO。

    Raises:
        ValueError: 重数・辞書キーが二重かごの契約に合わない場合。
    """
    if inner_partial.cage_multiplicity != ImCageMultiplicityType.DOUBLE_CAGE:
        raise ValueError(
            "inner_partial.cage_multiplicity は DOUBLE_CAGE である必要があります: "
            f"{inner_partial.cage_multiplicity!s}"
        )
    if outer_partial.cage_multiplicity != ImCageMultiplicityType.DOUBLE_CAGE:
        raise ValueError(
            "outer_partial.cage_multiplicity は DOUBLE_CAGE である必要があります: "
            f"{outer_partial.cage_multiplicity!s}"
        )
    inner_key = ImSecondaryCageBranchType.INNER
    outer_key = ImSecondaryCageBranchType.OUTER
    if frozenset(inner_partial.models.keys()) != frozenset({inner_key}):
        raise ValueError(
            "inner_partial の models キーは INNER のみである必要があります: "
            f"{sorted(b.value for b in inner_partial.models)}"
        )
    if frozenset(outer_partial.models.keys()) != frozenset({outer_key}):
        raise ValueError(
            "outer_partial の models キーは OUTER のみである必要があります: "
            f"{sorted(b.value for b in outer_partial.models)}"
        )

    return ItmImSecondaryDto(
        cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
        resistances={
            **inner_partial.resistances,
            **outer_partial.resistances,
        },
        inductances={
            **inner_partial.inductances,
            **outer_partial.inductances,
        },
        models={**inner_partial.models, **outer_partial.models},
        impedances={**inner_partial.impedances, **outer_partial.impedances},
        admittances={**inner_partial.admittances, **outer_partial.admittances},
        base_impedances={
            **inner_partial.base_impedances,
            **outer_partial.base_impedances,
        },
        base_admittances={
            **inner_partial.base_admittances,
            **outer_partial.base_admittances,
        },
        load_impedances={
            **inner_partial.load_impedances,
            **outer_partial.load_impedances,
        },
        load_admittances={
            **inner_partial.load_admittances,
            **outer_partial.load_admittances,
        },
    )


class DoubleCageImModelBuilder(IImModelBuilder):
    """二重かご型誘導電動機（IM）モデル構築器。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """二重かご型 IM モデル構築器を初期化する。

        Args:
            config: 設定。
            logger: ロガー。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> IImModelBuilder:
        """ファクトリーメソッド。

        Args:
            config: 設定。
            logger: ロガー。

        Returns:
            IImModelBuilder: 構築器インスタンス。
        """
        return cls(config=config, logger=logger)

    @timer(logger=None, line="=", min_duration=0.1)
    def build(
        self,
        im_dto: ImDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImModelDto:
        """ImDto から ItmImModelDto を構築する。

        Args:
            im_dto: 誘導電動機 DTO。
            model_array_layout: 配列レイアウト DTO。

        Returns:
            ItmImModelDto: 中間モデル DTO。

        Raises:
            ValueError: 引数が無効、またはシリーズが二重かごでない場合。
        """
        self._validate_build_arguments(
            im_dto=im_dto,
            model_array_layout=model_array_layout,
        )

        im_series_dto = im_dto.im_series
        if im_series_dto is None:
            raise ValueError(
                "ImSeriesDto is not embedded in im_dto. "
                "Please set ImDto.im_series."
            )
        if (
            im_series_dto.cage_multiplicity
            != ImCageMultiplicityType.DOUBLE_CAGE
        ):
            raise ValueError(
                "DoubleCageImModelBuilder は cage_multiplicity=DOUBLE_CAGE の "
                "ImSeriesDto のみ扱います: "
                f"{im_series_dto.cage_multiplicity!s}"
            )

        basic = self._convert_im_basic(im_series_dto=im_series_dto)
        circuit = self._convert_im_circuit(im_series_dto=im_series_dto)
        primary_model = self._convert_im_primary_immittance(
            im_series_dto=im_series_dto,
            model_array_layout=model_array_layout,
        )
        excitation_model = self._convert_im_excitation_immittance(
            im_series_dto=im_series_dto,
            model_array_layout=model_array_layout,
        )
        secondary_model = self._convert_im_secondary_immittance(
            im_series_dto=im_series_dto,
            model_array_layout=model_array_layout,
        )
        total_model = self._convert_im_total_immittance(
            circuit=circuit,
            primary_model=primary_model,
            excitation_model=excitation_model,
            secondary_model=secondary_model,
        )

        return ItmImModelDto(
            name=im_dto.name,
            basic_info=basic,
            circuit_info=circuit,
            primary_model=primary_model,
            excitation_model=excitation_model,
            secondary_model=secondary_model,
            total_model=total_model,
        )

    def _validate_build_arguments(
        self,
        im_dto: ImDto,
        model_array_layout: ArrayLayoutDto,
    ) -> None:
        """build の引数を検証する。"""
        if im_dto is None:
            raise ValueError("im_dtoは必須です。")
        if model_array_layout is None:
            raise ValueError("model_array_layoutは必須です。")

    def _convert_im_basic(
        self,
        im_series_dto: ImSeriesDto,
    ) -> ItmImBasicDto:
        """基本情報を変換する。"""
        series_name = im_series_dto.name
        poles = im_series_dto.poles
        voltage = im_series_dto.nameplate_voltage.to_base_unit()
        current = im_series_dto.nameplate_current.to_base_unit()
        power = im_series_dto.nameplate_power.to_base_unit()
        frequency = im_series_dto.nameplate_frequency.to_base_unit()

        return ItmImBasicDto(
            series_name=series_name,
            poles=poles,
            nameplate_voltage=voltage,
            nameplate_current=current,
            nameplate_power=power,
            nameplate_frequency=frequency,
        )

    def _convert_im_circuit(
        self,
        im_series_dto: ImSeriesDto,
    ) -> ItmImCircuitDto:
        """回路情報を変換する。

        NOTE: build_model が生成するイミタンスは結線（STAR/DELTA）に依らず
            「per-phase スター等価」値として扱う（InputDto の設計契約に準拠）。
            よって connection_type は DTO に保持するのみで、ここでインピーダンスの
            STAR/DELTA 換算は行わない。実巻線相への換算が必要な場合は Output
            ステージで balanced 変換を用いる。規約の正本は ItmImVoltageCurrentDto
            のクラス docstring を参照。
        """
        return ItmImCircuitDto(
            connection_type=im_series_dto.connection_type,
            circuit_type=im_series_dto.circuit_type,
        )

    def _convert_im_primary_immittance(
        self,
        im_series_dto: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImPrimaryDto:
        """一次側イミタンスを変換する。"""
        circuit_model = im_series_dto.primary_model
        converter = (
            ImComponentImmittanceConverterFactory.create_primary_converter(
                circuit_model=circuit_model,
                config=self._config,
                logger=self._logger,
            )
        )
        return converter.convert(im_series_dto, model_array_layout)

    def _convert_im_excitation_immittance(
        self,
        im_series_dto: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImExcitationDto:
        """励磁回路イミタンスを変換する。"""
        circuit_model = im_series_dto.excitation_model
        converter = (
            ImComponentImmittanceConverterFactory.create_excitation_converter(
                circuit_model=circuit_model,
                config=self._config,
                logger=self._logger,
            )
        )
        return converter.convert(im_series_dto, model_array_layout)

    def _convert_im_secondary_immittance(
        self,
        im_series_dto: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImSecondaryDto:
        """二次回路イミタンスを INNER/OUTER で変換しマージする。"""
        inner_branch = ImSecondaryCageBranchType.INNER
        outer_branch = ImSecondaryCageBranchType.OUTER
        inner_converter = (
            ImComponentImmittanceConverterFactory.create_secondary_converter(
                circuit_model=im_series_dto.secondary_models[inner_branch],
                config=self._config,
                logger=self._logger,
            )
        )
        outer_converter = (
            ImComponentImmittanceConverterFactory.create_secondary_converter(
                circuit_model=im_series_dto.secondary_models[outer_branch],
                config=self._config,
                logger=self._logger,
            )
        )
        inner_current = resolve_secondary_current_for_branch(
            model_array_layout,
            inner_branch,
        )
        outer_current = resolve_secondary_current_for_branch(
            model_array_layout,
            outer_branch,
        )
        inner_partial = inner_converter.convert(
            im_series_dto,
            model_array_layout,
            secondary_cage_branch_type=inner_branch,
            secondary_current=inner_current,
        )
        outer_partial = outer_converter.convert(
            im_series_dto,
            model_array_layout,
            secondary_cage_branch_type=outer_branch,
            secondary_current=outer_current,
        )
        return merge_double_cage_itm_im_secondary_dto(
            inner_partial=inner_partial,
            outer_partial=outer_partial,
        )

    def _convert_im_total_immittance(
        self,
        circuit: ItmImCircuitDto,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """全範囲イミタンスを計算する。"""
        circuit_type = circuit.circuit_type
        synthesizer = (
            DoubleCageImTotalImmittanceSynthesizerFactory.create_synthesizer(
                topology=circuit_type,
                config=self._config,
                logger=self._logger,
            )
        )
        return synthesizer.synthesize(
            primary_model=primary_model,
            excitation_model=excitation_model,
            secondary_model=secondary_model,
        )
