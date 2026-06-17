"""
NOTE: このテストファイルについて

このテストファイルは、PieCableModelBuilderのアルゴリズムレベルの単体テストです。
ただし、executeステージでの包括的なテスト（test_build_model.py）で
同様の検証が行われるため、そちらを優先してください。

このファイルは、アルゴリズムレベルの詳細な検証が必要な場合にのみ使用してください。
"""

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model import (  # noqa: E501
    PieCableModelBuilder,
)
from im_cable_system.engine.domain.numerics import (
    extend_array,
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
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
)
from im_cable_system.engine.shared.dto.input import (  # noqa: E501
    InputDto,
    InputDtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos,
)


@pytest.fixture
def input_im_cable_system_dtos() -> InputDtos:
    """テスト用のInputDtos fixture."""
    return make_input_im_cable_system_dtos()


@pytest.fixture
def sample_input_im_cable_system_dto(
    input_im_cable_system_dtos: InputDtos,
) -> InputDto:
    """テスト用のInputDto fixture.
    サンプルケース（すなわち教科書の問題と同じ条件）のInputDtoを取得する。
    """
    return input_im_cable_system_dtos.get_all()[0]


class TestPieCableModelBuilder:
    def test_build_impedance_shapes(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """build()の戻りDTOの形状を検証する。

        複数のInputDtoに対して、それぞれのbuild()の戻りDTOの
        形状を検証する。

        - 全てのイミタンス配列が配列レイアウトのshapeと一致すること
        """
        # NOTE: テストコードではprivateメソッドにアクセスするため、実装クラスの型を使用
        builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

        # 各InputDtoに対して検証
        for input_dto in input_im_cable_system_dtos.get_all():
            # cable_dtoがNoneの場合はスキップ（build()は擬似ケーブルモデルを作成するが、形状検証はスキップ）
            if input_dto.cable is None:
                continue

            cable_dto = input_dto.cable

            # InputDto.array_layoutを直接使用
            array_layout_dto = input_dto.array_layout

            # 配列レイアウトの形状を決定
            expected_shape = array_layout_dto.shape

            # build()の戻りDTOの形状を検証
            itm_cable_model_dto = builder.build(
                cable_dto=cable_dto,
                model_array_layout=array_layout_dto,
            )
            immittance = itm_cable_model_dto.cable_immittance

            assert (
                immittance.conductor_impedance[
                    PieCableConductorKey.SINGLE
                ].value.shape
                == expected_shape
            )  # type: ignore
            assert (
                immittance.conductor_admittance[
                    PieCableConductorKey.SINGLE
                ].value.shape
                == expected_shape
            )  # type: ignore
            assert (
                immittance.ground_impedance[
                    PieCableGroundKey.UPSTREAM
                ].value.shape
                == expected_shape
            )  # type: ignore
            assert (
                immittance.ground_admittance[
                    PieCableGroundKey.UPSTREAM
                ].value.shape
                == expected_shape
            )  # type: ignore
            assert (
                immittance.ground_impedance[
                    PieCableGroundKey.DOWNSTREAM
                ].value.shape
                == expected_shape
            )  # type: ignore
            assert (
                immittance.ground_admittance[
                    PieCableGroundKey.DOWNSTREAM
                ].value.shape
                == expected_shape
            )  # type: ignore

    def test_build_retains_cable_name(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """実ケーブルでは個体名を保持し、擬似ケーブルでは None になる。"""
        builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

        for input_dto in input_im_cable_system_dtos.get_all():
            itm_cable_model_dto = builder.build(
                cable_dto=input_dto.cable,
                model_array_layout=input_dto.array_layout,
            )
            if input_dto.cable is None:
                assert itm_cable_model_dto.name is None
            else:
                assert itm_cable_model_dto.name == input_dto.cable.name

    def test_impedance_admittance_relationship(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """アドミタンスとインピーダンスの関係（Y = 1/Z）を検証する。

        複数のInputDtoに対して、それぞれのアドミタンスとインピーダンスの
        関係を検証する。

        - 導体アドミタンス = 1 / 導体インピーダンス
        - アースアドミタンス = 1 / アースインピーダンス（合成後）
        """
        builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

        # 各InputDtoに対して検証
        for input_dto in input_im_cable_system_dtos.get_all():
            # cable_dtoがNoneの場合はスキップ
            if input_dto.cable is None:
                continue

            cable_dto = input_dto.cable

            # InputDto.array_layoutを直接使用
            array_layout_dto = input_dto.array_layout

            itm_cable_model_dto = builder.build(
                cable_dto=cable_dto,
                model_array_layout=array_layout_dto,
            )
            immittance = itm_cable_model_dto.cable_immittance

            # 導体: Y = 1/Z の関係を検証
            conductor_y_from_z = admittance_from_impedance(
                eps=config.numerical_guard_config.eps,
                max_mag=1.0 / config.numerical_guard_config.eps,
                impedance=immittance.conductor_impedance[
                    PieCableConductorKey.SINGLE
                ],  # type: ignore
            )
            np.testing.assert_allclose(
                immittance.conductor_admittance[
                    PieCableConductorKey.SINGLE
                ].get_value(),  # type: ignore
                conductor_y_from_z.get_value(),
                rtol=1e-10,
                atol=1e-12,
            )

            # アース: 合成インピーダンスからアドミタンスを計算  # noqa: ERA001
            # 上流アースインピーダンスは合成値の2倍なので、合成値は1/2
            ground_impedance_total = ArrayComplexImpedanceDto(
                value=immittance.ground_impedance[
                    PieCableGroundKey.UPSTREAM
                ].get_value()
                / 2.0,  # type: ignore
                unit=immittance.ground_impedance[
                    PieCableGroundKey.UPSTREAM
                ].get_unit(),  # type: ignore
            )
            ground_y_from_z = admittance_from_impedance(
                eps=config.numerical_guard_config.eps,
                max_mag=1.0 / config.numerical_guard_config.eps,
                impedance=ground_impedance_total,
            )
            # アースアドミタンスは合成値の1/2なので、合成値は2倍
            ground_admittance_total = ArrayComplexAdmittanceDto(
                value=immittance.ground_admittance[
                    PieCableGroundKey.UPSTREAM
                ].get_value()
                * 2.0,  # type: ignore
                unit=immittance.ground_admittance[
                    PieCableGroundKey.UPSTREAM
                ].get_unit(),  # type: ignore
            )
            np.testing.assert_allclose(
                ground_admittance_total.get_value(),
                ground_y_from_z.get_value(),
                rtol=1e-10,
                atol=1e-12,
            )

    def test_pi_circuit_impedance_admittance_scaling(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """π型回路でのインピーダンス・アドミタンスのスケーリングを検証する。

        複数のInputDtoに対して、それぞれのπ型回路でのインピーダンス・
        アドミタンスのスケーリングを検証する。

        - 上流アースインピーダンス = 2 × 合成アースインピーダンス
        - 下流アースインピーダンス = 2 × 合成アースインピーダンス
        - 上流アースアドミタンス = 0.5 × 合成アースアドミタンス
        - 下流アースアドミタンス = 0.5 × 合成アースアドミタンス
        - 上流と下流のアースインピーダンス・アドミタンスが同じ
        """
        builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

        # 各InputDtoに対して検証
        for input_dto in input_im_cable_system_dtos.get_all():
            # cable_dtoがNoneの場合はスキップ
            if input_dto.cable is None:
                continue

            cable_dto = input_dto.cable

            # InputDto.array_layoutを直接使用
            array_layout_dto = input_dto.array_layout

            itm_cable_model_dto = builder.build(
                cable_dto=cable_dto,
                model_array_layout=array_layout_dto,
            )
            immittance = itm_cable_model_dto.cable_immittance

        # 合成アースインピーダンスを計算（上流は2倍なので1/2）
        ground_impedance_total = ArrayComplexImpedanceDto(
            value=immittance.ground_impedance[
                PieCableGroundKey.UPSTREAM
            ].get_value()
            / 2.0,  # type: ignore
            unit=immittance.ground_impedance[
                PieCableGroundKey.UPSTREAM
            ].get_unit(),  # type: ignore
        )

        # 合成アースアドミタンスを計算（上流は0.5倍なので2倍）
        ground_admittance_total = ArrayComplexAdmittanceDto(
            value=immittance.ground_admittance[
                PieCableGroundKey.UPSTREAM
            ].get_value()
            * 2.0,  # type: ignore
            unit=immittance.ground_admittance[
                PieCableGroundKey.UPSTREAM
            ].get_unit(),  # type: ignore
        )

        # 上流アースインピーダンス = 2 × 合成アースインピーダンス
        expected_upstream_ground_impedance = ArrayComplexImpedanceDto(
            value=2.0 * ground_impedance_total.get_value(),
            unit=ground_impedance_total.get_unit(),
        )
        np.testing.assert_allclose(
            immittance.ground_impedance[PieCableGroundKey.UPSTREAM].get_value(),  # type: ignore
            expected_upstream_ground_impedance.get_value(),
            rtol=1e-10,
            atol=1e-12,
        )

        # 下流アースインピーダンス = 2 × 合成アースインピーダンス
        expected_downstream_ground_impedance = ArrayComplexImpedanceDto(
            value=2.0 * ground_impedance_total.get_value(),
            unit=ground_impedance_total.get_unit(),
        )
        np.testing.assert_allclose(
            immittance.ground_impedance[
                PieCableGroundKey.DOWNSTREAM
            ].get_value(),  # type: ignore
            expected_downstream_ground_impedance.get_value(),
            rtol=1e-10,
            atol=1e-12,
        )

        # 上流アースアドミタンス = 0.5 × 合成アースアドミタンス
        expected_upstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=0.5 * ground_admittance_total.get_value(),
            unit=ground_admittance_total.get_unit(),
        )
        np.testing.assert_allclose(
            immittance.ground_admittance[
                PieCableGroundKey.UPSTREAM
            ].get_value(),  # type: ignore
            expected_upstream_ground_admittance.get_value(),
            rtol=1e-10,
            atol=1e-12,
        )

        # 下流アースアドミタンス = 0.5 × 合成アースアドミタンス
        expected_downstream_ground_admittance = ArrayComplexAdmittanceDto(
            value=0.5 * ground_admittance_total.get_value(),
            unit=ground_admittance_total.get_unit(),
        )
        np.testing.assert_allclose(
            immittance.ground_admittance[
                PieCableGroundKey.DOWNSTREAM
            ].get_value(),  # type: ignore
            expected_downstream_ground_admittance.get_value(),
            rtol=1e-10,
            atol=1e-12,
        )

        # 上流と下流のアースインピーダンスが同じ
        np.testing.assert_allclose(
            immittance.ground_impedance[PieCableGroundKey.UPSTREAM].get_value(),  # type: ignore
            immittance.ground_impedance[
                PieCableGroundKey.DOWNSTREAM
            ].get_value(),  # type: ignore
            rtol=1e-10,
            atol=1e-12,
        )

        # 上流と下流のアースアドミタンスが同じ
        np.testing.assert_allclose(
            immittance.ground_admittance[
                PieCableGroundKey.UPSTREAM
            ].get_value(),  # type: ignore
            immittance.ground_admittance[
                PieCableGroundKey.DOWNSTREAM
            ].get_value(),  # type: ignore
            rtol=1e-10,
            atol=1e-12,
        )

    def test_conductor_impedance_series_combination(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """導体インピーダンスの直列合成が正しいことを検証する。

        複数のInputDtoに対して、それぞれの導体インピーダンスの直列合成を
        検証する。

        各ケーブルの導体インピーダンスを個別に計算し、
        それらを直列合成した結果が、build()の戻り値と一致することを確認する。
        理想導体の場合は、期待値も理想導体の結果（EPS値）になる。
        """
        builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

        # 各InputDtoに対して検証
        for input_dto in input_im_cable_system_dtos.get_all():
            # cable_dtoがNoneの場合はスキップ
            if input_dto.cable is None:
                continue

            cable_dto = input_dto.cable

            # InputDto.array_layoutを直接使用
            array_layout_dto = input_dto.array_layout

            itm_cable_model_dto = builder.build(
                cable_dto=cable_dto,
                model_array_layout=array_layout_dto,
            )
            immittance = itm_cable_model_dto.cable_immittance

            # 理想導体かどうかを判定
            is_conductor_ideal = check_all_conductor_ideal(
                cable_dto=cable_dto,
                eps=1e-12,
            )

            if is_conductor_ideal:
                # 理想導体の場合：期待値はEPS値
                eps = config.numerical_guard_config.eps
                array_shape = array_layout_dto.shape
                expected_conductor_impedance = ArrayComplexImpedanceDto(
                    value=np.full(array_shape, eps, dtype=np.complex128),
                    unit="Ω",
                )
            else:
                # cable_infoがNoneでないことを確認
                assert itm_cable_model_dto.cable_info is not None
                cable_info = itm_cable_model_dto.cable_info

                # 実装と同じコンバーターを用いて各セクションの導体インピーダンスを計算
                conductor_model = cable_dto.conductor_model
                converter = builder._create_conductor_converter(  # type: ignore[attr-defined]
                    conductor_model=conductor_model,
                )

                # 実装と同じ周波数・電流DTOを作成
                frequency_dto = builder._create_frequency_dto(  # type: ignore
                    model_array_layout=array_layout_dto,
                )
                conductor_current_dto = builder._create_conductor_current_dto(  # type: ignore  # noqa: E501
                    model_array_layout=array_layout_dto,
                )

                conductor_impedances: list[ArrayComplexImpedanceDto] = []
                for cable in cable_info:
                    # 線密度と長さから基準抵抗・インダクタンスを計算
                    resistance_per_length_base = cable.line_density_info.conductor_resistance_per_length.to_base_unit()
                    inductance_per_length_base = cable.line_density_info.conductor_inductance_per_length.to_base_unit()
                    length_base = cable.basic_info.length.to_base_unit()

                    base_resistance_total = FloatResistanceDto(
                        value=resistance_per_length_base.value
                        * length_base.value,
                        unit="Ω",
                    )
                    base_inductance_total = FloatInductanceDto(
                        value=inductance_per_length_base.value
                        * length_base.value,
                        unit="H",
                    )

                    conductor_impedance = converter.convert(
                        conductor_model=conductor_model,
                        base_resistance_total=base_resistance_total,
                        base_inductance_total=base_inductance_total,
                        frequency=frequency_dto,
                        conductor_current=conductor_current_dto,
                    )
                    conductor_impedances.append(conductor_impedance)

                # 直列合成
                expected_conductor_impedance = combine_impedances_series(
                    eps=config.numerical_guard_config.eps,
                    max_mag=1.0 / config.numerical_guard_config.eps,
                    impedances=conductor_impedances,
                )

            # 検証
            np.testing.assert_allclose(
                immittance.conductor_impedance[
                    PieCableConductorKey.SINGLE
                ].get_value(),  # type: ignore
                expected_conductor_impedance.get_value(),
                rtol=1e-10,
                atol=1e-12,
            )

    def test_ground_impedance_parallel_combination(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """アースインピーダンスの並列合成が正しいことを検証する。

        複数のInputDtoに対して、それぞれのアースインピーダンスの並列合成を
        検証する。

        各ケーブルのアースインピーダンスを個別に計算し、
        それらを並列合成した結果が、build()の戻り値と一致することを確認する。
        完全絶縁または地絡の場合は、期待値も特殊ケースの結果になる。
        """
        builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

        # 各InputDtoに対して検証
        for input_dto in input_im_cable_system_dtos.get_all():
            # cable_dtoがNoneの場合はスキップ
            if input_dto.cable is None:
                continue

            cable_dto = input_dto.cable

            # InputDto.array_layoutを直接使用
            array_layout_dto = input_dto.array_layout

            itm_cable_model_dto = builder.build(
                cable_dto=cable_dto,
                model_array_layout=array_layout_dto,
            )
            immittance = itm_cable_model_dto.cable_immittance

            # 特殊ケースの判定
            is_ground_insulated = check_all_ground_insulated(
                cable_dto=cable_dto,
                max_mag=1e12,
            )
            is_ground_shorted = check_any_ground_shorted(
                cable_dto=cable_dto,
                eps=1e-12,
            )

            if is_ground_insulated:
                # 完全絶縁の場合：upstream_ground_impedanceは既に1/EPS値（2倍されていない）
                # そのまま使用
                expected_ground_impedance = immittance.ground_impedance[
                    PieCableGroundKey.UPSTREAM
                ]
            elif is_ground_shorted:
                # 地絡の場合：upstream_ground_impedanceは既にEPS値（2倍されていない）
                # そのまま使用
                expected_ground_impedance = immittance.ground_impedance[
                    PieCableGroundKey.UPSTREAM
                ]
            else:
                # cable_infoがNoneでないことを確認
                assert itm_cable_model_dto.cable_info is not None
                cable_info = itm_cable_model_dto.cable_info

                # 通常ケース：各ケーブルのアースインピーダンスを個別に計算
                frequency_dto = array_layout_dto.arrays[ArrayKey.FREQUENCY]
                frequency_unit = frequency_dto.get_unit()

                # 周波数配列を配列レイアウトに合わせて拡張
                frequency_values_extended = extend_array(
                    array_layout=array_layout_dto,
                    axis_name=ArrayKey.FREQUENCY,
                    array_dto=frequency_dto,
                )

                frequency_dto_extended = ArrayFrequencyDto(
                    value=frequency_values_extended, unit=frequency_unit
                )

                ground_impedances: list[ArrayComplexImpedanceDto] = []
                for cable in cable_info:
                    length_dto = cable.basic_info.length
                    ground_impedance = impedance_from_ground_line_density(
                        eps=config.numerical_guard_config.eps,
                        max_mag=1.0 / config.numerical_guard_config.eps,
                        resistance_length=cable.line_density_info.ground_resistance_length,
                        capacitance_per_length=cable.line_density_info.ground_capacitance_per_length,
                        length=length_dto,
                        frequency=frequency_dto_extended,
                    )
                    ground_impedances.append(ground_impedance)

                # 並列合成
                ground_impedance_total = combine_impedances_parallel(
                    eps=config.numerical_guard_config.eps,
                    max_mag=1.0 / config.numerical_guard_config.eps,
                    impedances=ground_impedances,
                )

                # 通常ケースでは、upstream_ground_impedanceは2倍されているので
                # 期待値も2倍する
                expected_ground_impedance = ArrayComplexImpedanceDto(
                    value=2.0 * ground_impedance_total.get_value(),
                    unit=ground_impedance_total.get_unit(),
                )

            # 検証（特殊ケースの場合はそのまま、通常ケースは既に2倍済み）
            np.testing.assert_allclose(
                immittance.ground_impedance[
                    PieCableGroundKey.UPSTREAM
                ].get_value(),  # type: ignore
                expected_ground_impedance.get_value(),
                rtol=1e-10,
                atol=1e-12,
            )
