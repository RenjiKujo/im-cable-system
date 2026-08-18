"""基本誘導電動機（IM）モデル構築器。

このモジュールは、ImDtoからItmImModelDtoを構築し、回路情報（イミタンス計算）
をまとめる処理を提供します。標準的なカゴ型誘導電動機の基本形を構築します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.i_im_model_builder import (  # noqa: E501
    IImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance import (  # noqa: E501
    ImComponentImmittanceConverterFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary import (  # noqa: E501
    resolve_secondary_current_for_layout,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance import (  # noqa: E501
    SingleCageImTotalImmittanceSynthesizerFactory,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
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


class SingleCageImModelBuilder(IImModelBuilder):
    """基本誘導電動機（IM）モデル構築器。

    ImDtoからItmImModelDtoを構築し、モデル情報（イミタンス計算）をまとめます。
    標準的なカゴ型誘導電動機の基本形を構築する実装です。

    ストレタジーパターンを用いることで、励磁飽和や表皮効果といった、各種スリップや電流依存の効果を考慮したイミタンス計算も行うことができるようになっています。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """基本誘導電動機（IM）モデル構築器のインスタンスを初期化する。

        Args:
            config: 回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> IImModelBuilder:
        """基本誘導電動機（IM）モデル構築器のインスタンスを生成する
        ファクトリーメソッド。

        Args:
            config: 回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImModelBuilder: 生成された回路モデル構築器インスタンス。
        """
        return cls(config=config, logger=logger)

    @timer(logger=None, line="=", min_duration=0.1)
    def build(
        self,
        im_dto: ImDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImModelDto:
        """ImDtoからItmImModelDtoを構築する。

        Args:
            im_dto: 誘導電動機（IM）DTO（必須）。
            model_array_layout: 配列レイアウトDTO（必須）。

        Returns:
            ItmImModelDto: 中間DTO。

        Raises:
            ValueError: 必須引数がNoneの場合。
        """
        self._validate_build_arguments(
            im_dto=im_dto,
            model_array_layout=model_array_layout,
        )

        # ImDto にシリーズ詳細が埋め込まれている前提とする
        im_series_dto = im_dto.im_series
        if im_series_dto is None:
            raise ValueError(
                "ImSeriesDto is not embedded in im_dto. "
                "Please set ImDto.im_series."
            )

        # 基本情報を変換
        basic = self._convert_im_basic(
            im_series_dto=im_series_dto,
        )

        # 回路情報を変換
        circuit = self._convert_im_circuit(im_series_dto=im_series_dto)

        # 一次側イミタンスを変換
        primary_model = self._convert_im_primary_immittance(
            im_series_dto=im_series_dto,
            model_array_layout=model_array_layout,
        )

        # 励磁回路イミタンスを変換
        excitation_model = self._convert_im_excitation_immittance(
            im_series_dto=im_series_dto,
            model_array_layout=model_array_layout,
        )

        # 二次側イミタンスを変換
        secondary_model = self._convert_im_secondary_immittance(
            im_series_dto=im_series_dto,
            model_array_layout=model_array_layout,
        )

        # 全範囲イミタンスを計算
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
            friction_windage_model=im_series_dto.friction_windage_model,
            stray_load_model=im_series_dto.stray_load_model,
        )

    def _validate_build_arguments(
        self,
        im_dto: ImDto,
        model_array_layout: ArrayLayoutDto,
    ) -> None:
        """buildメソッドの引数をバリデーションする。

        Args:
            im_dto: 誘導電動機（IM）DTO。
            model_array_layout: 配列レイアウトDTO。

        Raises:
            ValueError: 必須引数がNoneの場合。
        """
        if im_dto is None:
            raise ValueError("im_dtoは必須です。")
        if model_array_layout is None:
            raise ValueError("model_array_layoutは必須です。")

    def _convert_im_basic(
        self,
        im_series_dto: ImSeriesDto,
    ) -> ItmImBasicDto:
        """基本情報を変換する。

        Args:
            im_series_dto: 誘導電動機（IM）シリーズDTO。

        Returns:
            ItmImBasicDto: 基本情報DTO。以下の属性を持つ:
                - series_name: 誘導電動機シリーズ名
                - poles: 極数
                - nameplate_voltage: 定格電圧[V]（基本単位に変換済み）
                - nameplate_current: 定格電流[A]（基本単位に変換済み）
                - nameplate_power: 定格電力[W]（基本単位に変換済み）
                - nameplate_frequency: 定格周波数[Hz]（基本単位に変換済み）
        """
        # シリーズ名
        series_name = im_series_dto.name

        # 極数
        poles = im_series_dto.poles

        # 定格情報（基本単位に変換済み）
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
        self, im_series_dto: ImSeriesDto
    ) -> ItmImCircuitDto:
        """回路情報を変換する。

        Args:
            im_series_dto: モーターシリーズDTO。

        Returns:
            ItmImCircuitDto: 回路情報DTO。以下の属性を持つ:
                - connection_type: 結線方式（DELTA/STAR）
                - circuit_type: 回路タイプ（T/L）

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
        """一次側イミタンスを変換する。

        Args:
            im_series_dto: モーターシリーズDTO。
            model_array_layout: 配列レイアウトDTO。

        Returns:
            ItmImPrimaryDto: 一次側モデル情報DTO（モデルタイプ、インピーダンス、アドミタンス、パラメータを含む）

        Raises:
            ValueError: モデルタイプがDTOのバリデーションに適合しない場合、
                またはマッピングに存在しない一次回路タイプが指定された場合。
        """
        circuit_model = im_series_dto.primary_model

        # ファクトリークラスはインスタンス生成のみを責務とする
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
        """励磁回路のイミタンスを変換する。

        Args:
            im_series_dto: モーターシリーズDTO。
            model_array_layout: 配列レイアウトDTO。

        Returns:
            ItmImExcitationDto: 励磁モデル情報DTO（モデルタイプ、インピーダンス、アドミタンス、パラメータを含む）

        Raises:
            ValueError: モデルタイプがDTOのバリデーションに適合しない場合、
                またはマッピングに存在しない励磁モデルタイプが指定された場合。
        """
        circuit_model = im_series_dto.excitation_model

        # ファクトリークラスはインスタンス生成のみを責務とする
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
        """二次回路のイミタンスを変換する。

        Args:
            im_series_dto: モーターシリーズDTO。
            model_array_layout: 配列レイアウトDTO。

        Returns:
            ItmImSecondaryDto: 二次側モデル情報DTO（モデルタイプ、インピーダンス、アドミタンス、パラメータを含む）

        Raises:
            ValueError: モデルタイプがDTOのバリデーションに適合しない場合、
                またはマッピングに存在しない二次側モデルタイプが指定された場合。
        """
        secondary_branch = ImSecondaryCageBranchType.SINGLE
        circuit_model = im_series_dto.secondary_models[secondary_branch]

        # ファクトリークラスはインスタンス生成のみを責務とする
        converter = (
            ImComponentImmittanceConverterFactory.create_secondary_converter(
                circuit_model=circuit_model,
                config=self._config,
                logger=self._logger,
            )
        )
        secondary_current = resolve_secondary_current_for_layout(
            model_array_layout,
        )
        return converter.convert(
            im_series_dto,
            model_array_layout,
            secondary_cage_branch_type=secondary_branch,
            secondary_current=secondary_current,
        )

    def _convert_im_total_immittance(
        self,
        circuit: ItmImCircuitDto,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """全範囲イミタンスを計算する。

        Args:
            circuit: 回路情報DTO（回路トポロジー（T or L）などの情報を含む）。
            primary_model: 一次側モデル情報DTO（インピーダンス、アドミタンスを含む）。
            excitation_model: 励磁モデル情報DTO（インピーダンス、アドミタンスを含む）。
            secondary_model: 二次側モデル情報DTO（インピーダンス、アドミタンスを含む）。

        Returns:
            ItmImTotalDto: 全範囲モデル情報DTO（総合インピーダンス、総合アドミタンスを含む）。

        Raises:
            ValueError: 未対応の回路トポロジーが指定された場合。
        """
        circuit_type = circuit.circuit_type
        synthesizer = (
            SingleCageImTotalImmittanceSynthesizerFactory.create_synthesizer(
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
