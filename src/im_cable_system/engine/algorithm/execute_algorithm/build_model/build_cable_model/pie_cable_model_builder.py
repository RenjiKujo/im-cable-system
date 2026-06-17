"""π型ケーブル回路モデル構築器。

このモジュールは、CableDtoからItmCableModelDtoを構築し、回路情報（イミタンス計算）
をまとめる処理を提供します。π型回路モデルを想定しています。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance import (
    ConductorImmittanceConverterFactory,
    IConductorImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.i_cable_model_builder import (  # noqa: E501
    ICableModelBuilder,
)
from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
)
from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
    combine_impedances_parallel,
    combine_impedances_series,
    impedance_from_ground_line_density,
)
from im_cable_system.engine.domain.predicate import (
    check_all_conductor_ideal,
    check_all_ground_insulated,
    check_any_ground_shorted,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    CableConductorModelDto,
    CableDto,
    ConductorModelType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableBasicDto,
    ItmCableImmittanceDto,
    ItmCableLineDensityDto,
    ItmCableModelDto,
    ItmCableSectionDto,
    ItmCableSectionDtos,
)


class PieCableModelBuilder(ICableModelBuilder):
    """π型ケーブル回路モデル構築器。

    CableDtosからItmCableModelDtoを構築し、回路情報（イミタンス計算）をまとめます。
    π型回路モデルを想定しています。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """回路モデル構築器のインスタンスを初期化する。

        Args:
            config: 回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> ICableModelBuilder:
        """回路モデル構築器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ICableModelBuilder: 生成された回路モデル構築器インスタンス。
        """
        return cls(
            config=config,
            logger=logger,
        )

    @timer(logger=None, line="=", min_duration=0.1)
    def build(
        self,
        cable_dto: CableDto | None,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmCableModelDto:
        """CableDtoからItmCableModelDtoを構築する。

        Args:
            cable_dto: ケーブルDTO。Noneの場合は、完全導体かつ完全絶縁の擬似ケーブルモデルを作成する。
            model_array_layout: 配列レイアウトDTO（必須）。

        Returns:
            ItmCableModelDto: 中間DTO。
                cable_dtoがNoneの場合、cable_infoはNoneとなる。

        Raises:
            ValueError: model_array_layoutがNoneの場合。
        """
        if model_array_layout is None:
            raise ValueError("model_array_layoutは必須です。")

        # ケーブルがNoneの場合は、完全導体かつ完全絶縁の擬似ケーブルモデルを作成
        if cable_dto is None:
            return self._build_ideal_cable_model(
                model_array_layout=model_array_layout,
            )

        # ケーブル情報を変換（セクションごとにItmCableSectionDtoを作成）
        itm_cable_dtos = self._convert_itm_cable_info_dtos(
            cable_dto=cable_dto,
        )

        # インピーダンス・アドミタンス情報を構築
        itm_cable_immittance = self._convert_cable_immittance(
            itm_cable_dtos=itm_cable_dtos,
            cable_dto=cable_dto,
            model_array_layout=model_array_layout,
        )

        # 中間DTOを作成して返す
        return ItmCableModelDto(
            name=cable_dto.name,
            cable_info=ItmCableSectionDtos(objects=itm_cable_dtos),
            cable_immittance=itm_cable_immittance,
        )

    def _convert_itm_cable_info_dtos(
        self,
        cable_dto: CableDto,
    ) -> list[ItmCableSectionDto]:
        """ケーブル情報を変換する。

        1本のケーブルの情報を与えられると、そのセクションごとに使われている
        ケーブルのシリーズ情報を検索し、そこからItmCableSectionDtoの各パラメータを取得する。

        Args:
            cable_dto: ケーブルDTO。

        Returns:
            list[ItmCableSectionDto]: ケーブルセクション情報DTOのリスト。
                各セクションごとに1つのItmCableSectionDtoが作成される。

        Raises:
            ValueError: セクションにシリーズ詳細が埋め込まれていない場合。
        """
        cable_list: list[ItmCableSectionDto] = []

        # 各セクションごとに処理
        for section_dto in cable_dto.sections.get_all():
            cable_series_dto = section_dto.series
            if cable_series_dto is None:
                raise ValueError(
                    "CableSeriesDto is not embedded in cable_dto.sections[]. "
                    "Please set CableSectionDto.series."
                )

            # 基本情報を変換（セクション名とシリーズ名を含む）
            basic = ItmCableBasicDto(
                name=section_dto.name,
                series_name=section_dto.series.name,
                shape_type=cable_series_dto.shape_type,
                length=section_dto.length,
            )

            # 線密度情報を変換
            line_density = ItmCableLineDensityDto(
                conductor_resistance_per_length=(
                    cable_series_dto.conductor_resistance_per_length
                ),
                conductor_inductance_per_length=(
                    cable_series_dto.conductor_inductance_per_length
                ),
                ground_resistance_length=cable_series_dto.ground_resistance_length,
                ground_capacitance_per_length=(
                    cable_series_dto.ground_capacitance_per_length
                ),
            )

            # ItmCableSectionDtoを作成
            cable = ItmCableSectionDto(
                basic_info=basic,
                line_density_info=line_density,
            )
            cable_list.append(cable)

        return cable_list

    def _convert_cable_immittance(
        self,
        itm_cable_dtos: list[ItmCableSectionDto],
        cable_dto: CableDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmCableImmittanceDto:
        """インピーダンス・アドミタンス情報を変換する。

        コンダクターはケーブルが直列接続されており、接地点との抵抗とキャパシタは
        ケーブルが並列で合成される。π型回路を最終的に想定するため、最終的な
        ground_impedanceについては、並列合成して入力のインピーダンス/長さ*長さになるように
        ItmCableImmittanceDtoを構築する。

        Args:
            itm_cable_dtos: ケーブル情報DTOのコレクション。
            cable_dto: ケーブルDTO。
            model_array_layout: 配列レイアウトDTO。

        Returns:
            ItmCableImmittanceDto: インピーダンス・アドミタンス情報DTO。
        """
        # CableDtoからconductor_modelを取得
        conductor_model = cable_dto.conductor_model

        # 特殊ケースの判定
        eps = self._config.numerical_guard_config.eps
        special_cases = self._check_special_cases(
            cable_dto=cable_dto,
            eps=eps,
        )

        # 配列形状を取得（[num_slips, num_frequencies]）
        array_shape = model_array_layout.shape

        # 周波数DTOを作成（ブロードキャスト済みの配列を使用）
        frequency_nd_dto = self._create_frequency_dto(model_array_layout)

        # 各ケーブルのインピーダンスを計算
        # 導線は直列接続、アースは並列接続として合成する
        (
            conductor_impedance_total,
            ground_impedance_total,
        ) = self._calculate_and_combine_cable_impedances(
            itm_cable_dtos=itm_cable_dtos,
            conductor_model=conductor_model,
            frequency_dto=frequency_nd_dto,
            conductor_current_dto=self._create_conductor_current_dto(
                model_array_layout=model_array_layout
            ),
            eps=eps,
        )

        # アースインピーダンス・アドミタンスを計算
        # 特殊ケースに応じて以下の3つの場合分けを行う:
        # 1. 完全絶縁: アース抵抗が極めて大きい場合（実質的に絶縁）
        # 2. 地絡: アース抵抗が極めて小さい場合（実質的に短絡）
        # 3. 通常ケース: 合成されたアースインピーダンスからπ型回路の等価変換を行う
        (
            upstream_ground_impedance,
            upstream_ground_admittance,
            downstream_ground_impedance,
            downstream_ground_admittance,
        ) = self._create_ground_impedance_admittance(
            is_ground_insulated=special_cases["is_ground_insulated"],
            is_ground_shorted=special_cases["is_ground_shorted"],
            ground_impedance_total=ground_impedance_total,
            array_shape=array_shape,
            eps=eps,
        )

        # 導線インピーダンス・アドミタンスを計算
        # 特殊ケースに応じて以下の2つの場合分けを行う:
        # 1. 理想導体: 導線抵抗が極めて小さい場合（実質的に無抵抗）
        # 2. 通常ケース: 合成された導線インピーダンスからアドミタンスを計算
        (
            conductor_impedance_total,
            conductor_admittance_total,
        ) = self._create_conductor_impedance_admittance(
            is_conductor_ideal=special_cases["is_conductor_ideal"],
            conductor_impedance_total=conductor_impedance_total,
            array_shape=array_shape,
            eps=eps,
        )

        # イミタンスをDict形式で構築
        conductor_impedance_dict = {
            PieCableConductorKey.SINGLE: conductor_impedance_total,
        }
        conductor_admittance_dict = {
            PieCableConductorKey.SINGLE: conductor_admittance_total,
        }
        ground_impedance_dict = {
            PieCableGroundKey.UPSTREAM: upstream_ground_impedance,
            PieCableGroundKey.DOWNSTREAM: downstream_ground_impedance,
        }
        ground_admittance_dict = {
            PieCableGroundKey.UPSTREAM: upstream_ground_admittance,
            PieCableGroundKey.DOWNSTREAM: downstream_ground_admittance,
        }

        return ItmCableImmittanceDto(
            conductor_model=conductor_model,
            conductor_impedance=conductor_impedance_dict,
            conductor_admittance=conductor_admittance_dict,
            ground_impedance=ground_impedance_dict,
            ground_admittance=ground_admittance_dict,
            is_ground_insulated=special_cases["is_ground_insulated"],
            is_ground_shorted=special_cases["is_ground_shorted"],
            is_conductor_ideal=special_cases["is_conductor_ideal"],
        )

    def _check_special_cases(
        self,
        cable_dto: CableDto,
        eps: float,
    ) -> dict[str, bool]:
        """特殊ケースを判定する。

        Args:
            cable_dto: ケーブルDTO。
            eps: EPS値（config.yamlから、デフォルト値は1e-12）。

        Returns:
            dict[str, bool]: 特殊ケースの判定結果。以下のキーを持つ:
                - is_ground_insulated: 完全絶縁かどうか
                - is_ground_shorted: 地絡かどうか
                - is_conductor_ideal: 理想導体かどうか
        """
        max_mag = 1.0 / eps

        is_ground_insulated = check_all_ground_insulated(
            cable_dto=cable_dto,
            max_mag=max_mag,
        )
        is_ground_shorted = check_any_ground_shorted(
            cable_dto=cable_dto,
            eps=eps,
        )
        is_conductor_ideal = check_all_conductor_ideal(
            cable_dto=cable_dto,
            eps=eps,
        )

        return {
            "is_ground_insulated": is_ground_insulated,
            "is_ground_shorted": is_ground_shorted,
            "is_conductor_ideal": is_conductor_ideal,
        }

    def _create_frequency_dto(
        self, model_array_layout: ArrayLayoutDto
    ) -> ArrayFrequencyDto:
        """周波数DTOを作成する。

        Args:
            model_array_layout: 配列レイアウトDTO。

        Returns:
            ArrayFrequencyDto: 周波数DTO（ブロードキャスト済みの配列を使用）。
        """
        frequency_key = ArrayKey.FREQUENCY
        extended_arrays = create_extended_arrays(model_array_layout)
        return ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=model_array_layout.arrays[frequency_key].get_unit(),
        )

    def _create_conductor_current_dto(
        self,
        model_array_layout: ArrayLayoutDto,
    ) -> ArrayComplexCurrentDto | None:
        """導体電流DTOを作成する。

        配列レイアウトにconductor_current軸が存在する場合はその値からDTOを作成し、
        存在しない場合はNoneを返す。

        Args:
            model_array_layout: 配列レイアウトDTO。

        Returns:
            ArrayComplexCurrentDto | None: 導体電流DTO。軸が無い場合はNone。
        """
        extended_arrays = create_extended_arrays(model_array_layout)

        # NOTE: PIE 型の場合、ItmCableVoltageCurrentDto の dict キーは
        # "conductor_current.pie_single" で固定されているため、
        # ArrayLayout 側の軸名もそれに合わせる。
        axis_name = ArrayKey.CONDUCTOR_CURRENT_PIE_SINGLE

        if axis_name not in extended_arrays:
            return None

        return ArrayComplexCurrentDto(
            value=extended_arrays[axis_name],
            unit=model_array_layout.arrays[axis_name].get_unit(),
        )

    def _create_conductor_converter(
        self,
        conductor_model: CableConductorModelDto,
    ) -> IConductorImmittanceConverter:
        """導線イミタンス計算コンバーター（PIE用）を作成する。

        conductor_immittance のファクトリーを呼び、
        conductor_model（ConductorModelType）に応じた PIE 用コンバーターを返す。

        Args:
            conductor_model: 導線回路モデルDTO。

        Returns:
            IConductorImmittanceConverter: PIE用導線イミタンス計算コンバーター。
        """
        return ConductorImmittanceConverterFactory.create_pie_converter(
            conductor_model=conductor_model,
            config=self._config,
            logger=self._logger,
        )

    def _calculate_and_combine_cable_impedances(
        self,
        itm_cable_dtos: list[ItmCableSectionDto],
        conductor_model: CableConductorModelDto,
        frequency_dto: ArrayFrequencyDto,
        conductor_current_dto: ArrayComplexCurrentDto | None,
        eps: float,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexImpedanceDto]:
        """各ケーブルのインピーダンスを計算し、合成する。

        ケーブルは複数のセクションから構成され、各セクションは異なる特性を持つ。
        物理的な接続に基づいて以下のように合成する:
        - 導線インピーダンス: セクション間は直列接続のため、直列合成する
        - アースインピーダンス: セクション間は並列接続のため、並列合成する

        Args:
            itm_cable_dtos: ケーブル情報DTOのコレクション。
                各要素は1つのセクションを表す。
            conductor_model: 導線回路モデルDTO。
                導線インピーダンス計算に使用するモデルタイプとパラメータを含む。
            frequency_dto: 周波数DTO。
                アースインピーダンスおよび導線インピーダンス計算に使用。
            conductor_current_dto: 導体電流DTO。
                電流依存モデルで導線インピーダンス計算に使用する。
            eps: 近接ゼロ判定のしきい値。ドメイン層の合成・変換へ伝播する。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexImpedanceDto]:
                導線インピーダンス（直列合成）とアースインピーダンス（並列合成）のタプル。
        """
        max_mag = 1.0 / eps
        # 導線インピーダンス計算コンバーターを作成
        conductor_converter = self._create_conductor_converter(
            conductor_model=conductor_model
        )

        conductor_impedances: list[ArrayComplexImpedanceDto] = []
        ground_impedances: list[ArrayComplexImpedanceDto] = []

        # 各セクションのインピーダンスを計算
        for cable in itm_cable_dtos:
            # 基準抵抗・インダクタンスを計算（線密度 × 長さ）
            resistance_per_length_base = cable.line_density_info.conductor_resistance_per_length.to_base_unit()
            inductance_per_length_base = cable.line_density_info.conductor_inductance_per_length.to_base_unit()
            length_base = cable.basic_info.length.to_base_unit()

            base_resistance_total = FloatResistanceDto(
                value=resistance_per_length_base.value * length_base.value,
                unit="Ω",
            )
            base_inductance_total = FloatInductanceDto(
                value=inductance_per_length_base.value * length_base.value,
                unit="H",
            )

            conductor_impedance = conductor_converter.convert(
                conductor_model=conductor_model,
                base_resistance_total=base_resistance_total,
                base_inductance_total=base_inductance_total,
                frequency=frequency_dto,
                conductor_current=conductor_current_dto,
            )
            conductor_impedances.append(conductor_impedance)

            ground_impedance = impedance_from_ground_line_density(
                resistance_length=cable.line_density_info.ground_resistance_length,
                capacitance_per_length=cable.line_density_info.ground_capacitance_per_length,
                length=cable.basic_info.length,
                frequency=frequency_dto,
                eps=eps,
                max_mag=max_mag,
            )
            ground_impedances.append(ground_impedance)

        # 導線インピーダンスを直列合成（セクション間は直列接続）
        conductor_impedance_total = combine_impedances_series(
            impedances=conductor_impedances,
            eps=eps,
            max_mag=max_mag,
        )
        # アースインピーダンスを並列合成（セクション間は並列接続）
        ground_impedance_total = combine_impedances_parallel(
            impedances=ground_impedances,
            eps=eps,
            max_mag=max_mag,
        )

        return conductor_impedance_total, ground_impedance_total

    def _create_ground_impedance_admittance(
        self,
        is_ground_insulated: bool,
        is_ground_shorted: bool,
        ground_impedance_total: ArrayComplexImpedanceDto,
        array_shape: tuple[int, ...],
        eps: float,
    ) -> tuple[
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
    ]:
        """アースインピーダンス・アドミタンスを作成する。

        π型等価回路を想定し、上流と下流のアースインピーダンス・アドミタンスを計算する。
        特殊ケース（完全絶縁、地絡）の場合は極端な値を使用し、
        通常ケースでは合成されたアースインピーダンスから計算する。

        π型回路では、アースインピーダンスは2倍、アースアドミタンスは1/2になる。
        これは、π型回路の等価変換に基づく。

        Args:
            is_ground_insulated: 完全絶縁かどうか。
            is_ground_shorted: 地絡かどうか。
            ground_impedance_total: アースインピーダンス（並列合成済み）。
                通常ケースでのみ使用される。
            array_shape: 配列形状（[num_slips, num_frequencies]）。
            eps: EPS値。特殊ケースでの極端な値の計算に使用。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto,
                  ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                上流アースインピーダンス、上流アースアドミタンス、
                下流アースインピーダンス、下流アースアドミタンスのタプル。
        """
        if is_ground_insulated:
            return self._create_ground_impedance_for_insulated(
                array_shape=array_shape, eps=eps
            )
        if is_ground_shorted:
            return self._create_ground_impedance_for_shorted(
                array_shape=array_shape, eps=eps
            )
        return self._create_ground_impedance_for_normal(
            ground_impedance_total=ground_impedance_total,
            eps=eps,
        )

    def _create_ground_impedance_for_insulated(
        self, array_shape: tuple[int, ...], eps: float
    ) -> tuple[
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
    ]:
        """完全絶縁の場合のアースインピーダンス・アドミタンスを作成する。

        完全絶縁の場合、アース抵抗が極めて大きいため、実質的に絶縁状態となる。
        数値計算の安定性を保つため、以下の極端な値を使用する:
        - インピーダンス: 1/EPS（極めて大きい値、実質的に開放）
        - アドミタンス: EPS（極めて小さい値、実質的に0）

        Args:
            array_shape: 配列形状（[num_slips, num_frequencies]）。
            eps: EPS値。数値計算の安定性を保つための閾値。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto,
                  ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                上流アースインピーダンス、上流アースアドミタンス、
                下流アースインピーダンス、下流アースアドミタンスのタプル。
                上流と下流は同じ値（π型回路の対称性）。
        """
        # 完全絶縁: インピーダンス = 1/EPS（極めて大きい値）
        insulated_impedance_value = np.full(
            array_shape, 1.0 / eps, dtype=np.complex128
        )
        upstream_ground_impedance = ArrayComplexImpedanceDto(
            value=insulated_impedance_value, unit="Ω"
        )
        downstream_ground_impedance = ArrayComplexImpedanceDto(
            value=insulated_impedance_value, unit="Ω"
        )

        # アドミタンスはインピーダンスの逆数: EPS（極めて小さい値）
        insulated_admittance_value = np.full(
            array_shape, eps, dtype=np.complex128
        )
        upstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=insulated_admittance_value, unit="S"
        )
        downstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=insulated_admittance_value, unit="S"
        )

        return (
            upstream_ground_impedance,
            upstream_ground_admittance,
            downstream_ground_impedance,
            downstream_ground_admittance,
        )

    def _create_ground_impedance_for_shorted(
        self, array_shape: tuple[int, ...], eps: float
    ) -> tuple[
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
    ]:
        """地絡の場合のアースインピーダンス・アドミタンスを作成する。

        地絡の場合、アース抵抗が極めて小さいため、実質的に短絡状態となる。
        数値計算の安定性を保つため、以下の極端な値を使用する:
        - インピーダンス: EPS（極めて小さい値、実質的に0）
        - アドミタンス: 1/EPS（極めて大きい値、実質的に無限大）

        Args:
            array_shape: 配列形状（[num_slips, num_frequencies]）。
            eps: EPS値。数値計算の安定性を保つための閾値。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto,
                  ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                上流アースインピーダンス、上流アースアドミタンス、
                下流アースインピーダンス、下流アースアドミタンスのタプル。
                上流と下流は同じ値（π型回路の対称性）。
        """
        # 地絡: インピーダンス = EPS（極めて小さい値）
        shorted_impedance_value = np.full(array_shape, eps, dtype=np.complex128)
        upstream_ground_impedance = ArrayComplexImpedanceDto(
            value=shorted_impedance_value, unit="Ω"
        )
        downstream_ground_impedance = ArrayComplexImpedanceDto(
            value=shorted_impedance_value, unit="Ω"
        )

        # アドミタンスはインピーダンスの逆数: 1/EPS（極めて大きい値）
        shorted_admittance_value = np.full(
            array_shape, 1.0 / eps, dtype=np.complex128
        )
        upstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=shorted_admittance_value, unit="S"
        )
        downstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=shorted_admittance_value, unit="S"
        )

        return (
            upstream_ground_impedance,
            upstream_ground_admittance,
            downstream_ground_impedance,
            downstream_ground_admittance,
        )

    def _create_ground_impedance_for_normal(
        self,
        ground_impedance_total: ArrayComplexImpedanceDto,
        eps: float,
    ) -> tuple[
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
        ArrayComplexImpedanceDto,
        ArrayComplexAdmittanceDto,
    ]:
        """通常ケースのアースインピーダンス・アドミタンスを作成する。

        π型等価回路では、合成されたアースインピーダンスを上流と下流に分配する。
        等価変換の結果、以下の関係が成り立つ:
        - 上流/下流アースインピーダンス = 2 × 合成アースインピーダンス
        - 上流/下流アースアドミタンス = 0.5 × 合成アースアドミタンス

        これは、π型回路の等価変換に基づく（T型回路からπ型回路への変換）。

        Args:
            ground_impedance_total: アースインピーダンス（並列合成済み）。
                全セクションのアースインピーダンスを並列合成した値。
            eps: 近接ゼロ判定のしきい値。アドミタンス変換のクランプへ伝播する。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto,
                  ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                上流アースインピーダンス、上流アースアドミタンス、
                下流アースインピーダンス、下流アースアドミタンスのタプル。
                上流と下流は同じ値（π型回路の対称性）。
        """
        # アースアドミタンスを計算（インピーダンスの逆数）
        ground_admittance_total = admittance_from_impedance(
            impedance=ground_impedance_total,
            eps=eps,
            max_mag=1.0 / eps,
        )

        # π型回路の等価変換: インピーダンスは2倍、アドミタンスは1/2
        upstream_ground_impedance = ArrayComplexImpedanceDto(
            value=2 * ground_impedance_total.get_value(),
            unit=ground_impedance_total.get_unit(),
        )
        upstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=0.5 * ground_admittance_total.get_value(),
            unit=ground_admittance_total.get_unit(),
        )
        downstream_ground_impedance = ArrayComplexImpedanceDto(
            value=2 * ground_impedance_total.get_value(),
            unit=ground_impedance_total.get_unit(),
        )
        downstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=0.5 * ground_admittance_total.get_value(),
            unit=ground_admittance_total.get_unit(),
        )

        return (
            upstream_ground_impedance,
            upstream_ground_admittance,
            downstream_ground_impedance,
            downstream_ground_admittance,
        )

    def _create_conductor_impedance_admittance(
        self,
        is_conductor_ideal: bool,
        conductor_impedance_total: ArrayComplexImpedanceDto,
        array_shape: tuple[int, ...],
        eps: float,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """導線インピーダンス・アドミタンスを作成する。

        理想導体の場合は極端な値を使用し、通常ケースでは合成された導線インピーダンスから
        アドミタンスを計算する。

        Args:
            is_conductor_ideal: 理想導体かどうか。
                導線抵抗が極めて小さい場合にTrueとなる。
            conductor_impedance_total: 導線インピーダンス（直列合成済み）。
                全セクションの導線インピーダンスを直列合成した値。
                通常ケースでのみ使用される。
            array_shape: 配列形状（[num_slips, num_frequencies]）。
            eps: EPS値。理想導体の場合の極端な値の計算に使用。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                導線インピーダンスと導線アドミタンスのタプル。
        """
        if is_conductor_ideal:
            return self._create_conductor_impedance_for_ideal(
                array_shape=array_shape, eps=eps
            )
        return self._create_conductor_impedance_for_normal(
            conductor_impedance_total=conductor_impedance_total,
            eps=eps,
        )

    def _create_conductor_impedance_for_ideal(
        self, array_shape: tuple[int, ...], eps: float
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """理想導体の場合の導線インピーダンス・アドミタンスを作成する。

        理想導体の場合、導線抵抗が極めて小さいため、実質的に無抵抗となる。
        数値計算の安定性を保つため、以下の極端な値を使用する:
        - インピーダンス: EPS（極めて小さい値、実質的に0）
        - アドミタンス: 1/EPS（極めて大きい値、実質的に無限大）

        Args:
            array_shape: 配列形状（[num_slips, num_frequencies]）。
            eps: EPS値。数値計算の安定性を保つための閾値。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                導線インピーダンスと導線アドミタンスのタプル。
        """
        # 理想導体: インピーダンス = EPS（極めて小さい値）
        ideal_impedance_value = np.full(array_shape, eps, dtype=np.complex128)
        conductor_impedance_total = ArrayComplexImpedanceDto(
            value=ideal_impedance_value, unit="Ω"
        )

        # アドミタンスはインピーダンスの逆数: 1/EPS（極めて大きい値）
        ideal_admittance_value = np.full(
            array_shape, 1.0 / eps, dtype=np.complex128
        )
        conductor_admittance_total = ArrayComplexAdmittanceDto(
            value=ideal_admittance_value, unit="S"
        )

        return conductor_impedance_total, conductor_admittance_total

    def _create_conductor_impedance_for_normal(
        self,
        conductor_impedance_total: ArrayComplexImpedanceDto,
        eps: float,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """通常ケースの導線インピーダンス・アドミタンスを作成する。

        合成された導線インピーダンスから、アドミタンス（インピーダンスの逆数）を計算する。
        導線インピーダンスはそのまま使用する。

        Args:
            conductor_impedance_total: 導線インピーダンス（直列合成済み）。
                全セクションの導線インピーダンスを直列合成した値。
            eps: 近接ゼロ判定のしきい値。アドミタンス変換のクランプへ伝播する。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                導線インピーダンスと導線アドミタンスのタプル。
        """
        # アドミタンスはインピーダンスの逆数
        conductor_admittance_total = admittance_from_impedance(
            impedance=conductor_impedance_total,
            eps=eps,
            max_mag=1.0 / eps,
        )
        return conductor_impedance_total, conductor_admittance_total

    def _build_ideal_cable_model(
        self,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmCableModelDto:
        """完全導体かつ完全絶縁の擬似ケーブルモデルを作成する（プライベートメソッド）。

        ケーブルが存在しない場合、完全導体かつ完全絶縁の擬似ケーブルモデルを
        作成します。このモデルは、ケーブルがない状態を物理的に表現するために
        使用されます。

        完全導体: 導線インピーダンスが0（Z_c ≈ 0）
        完全絶縁: アースアドミタンスが0（Y_up ≈ 0, Y_down ≈ 0）

        この場合、システムモデル構築時にケーブルの影響が無視され、
        システムイミタンスは誘導電動機のイミタンスそのものになります。

        Args:
            model_array_layout: 配列レイアウトDTO（必須）。

        Returns:
            ItmCableModelDto: 完全導体かつ完全絶縁の擬似ケーブルモデルDTO。
                cable_infoはNone（ケーブル情報は存在しないため）。
        """

        # 配列形状を取得（[num_slips, num_frequencies]）
        array_shape = model_array_layout.shape

        # EPS値を取得
        eps = self._config.numerical_guard_config.eps

        # 完全絶縁: アースインピーダンス = 1/EPS（極めて大きい値）
        insulated_impedance_value = np.full(
            array_shape, 1.0 / eps, dtype=np.complex128
        )
        upstream_ground_impedance = ArrayComplexImpedanceDto(
            value=insulated_impedance_value, unit="Ω"
        )
        downstream_ground_impedance = ArrayComplexImpedanceDto(
            value=insulated_impedance_value, unit="Ω"
        )

        # 完全絶縁: アースアドミタンス = EPS（極めて小さい値）
        insulated_admittance_value = np.full(
            array_shape, eps, dtype=np.complex128
        )
        upstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=insulated_admittance_value, unit="S"
        )
        downstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=insulated_admittance_value, unit="S"
        )

        # 理想導体: 導線インピーダンス = EPS（極めて小さい値）
        ideal_impedance_value = np.full(array_shape, eps, dtype=np.complex128)
        conductor_impedance_total = ArrayComplexImpedanceDto(
            value=ideal_impedance_value, unit="Ω"
        )

        # 理想導体: 導線アドミタンス = 1/EPS（極めて大きい値）
        ideal_admittance_value = np.full(
            array_shape, 1.0 / eps, dtype=np.complex128
        )
        conductor_admittance_total = ArrayComplexAdmittanceDto(
            value=ideal_admittance_value, unit="S"
        )

        # イミタンスをDict形式で構築
        conductor_impedance_dict = {
            PieCableConductorKey.SINGLE: conductor_impedance_total,
        }
        conductor_admittance_dict = {
            PieCableConductorKey.SINGLE: conductor_admittance_total,
        }
        ground_impedance_dict = {
            PieCableGroundKey.UPSTREAM: upstream_ground_impedance,
            PieCableGroundKey.DOWNSTREAM: downstream_ground_impedance,
        }
        ground_admittance_dict = {
            PieCableGroundKey.UPSTREAM: upstream_ground_admittance,
            PieCableGroundKey.DOWNSTREAM: downstream_ground_admittance,
        }

        conductor_model = CableConductorModelDto(
            name=ConductorModelType.BASIC,
            params=None,
        )

        cable_immittance = ItmCableImmittanceDto(
            conductor_model=conductor_model,
            conductor_impedance=conductor_impedance_dict,
            conductor_admittance=conductor_admittance_dict,
            ground_impedance=ground_impedance_dict,
            ground_admittance=ground_admittance_dict,
            is_ground_insulated=True,  # 完全絶縁
            is_ground_shorted=False,  # 地絡なし
            is_conductor_ideal=True,  # 理想導体
        )

        # ケーブル情報は存在しないため、Noneを返す
        return ItmCableModelDto(
            name=None,  # 擬似ケーブルは個体名を持たない
            cable_info=None,  # ケーブル情報は存在しない
            cable_immittance=cable_immittance,
        )
