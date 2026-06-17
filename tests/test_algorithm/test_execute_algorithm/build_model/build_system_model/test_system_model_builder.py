"""
NOTE: このテストファイルについて

このテストファイルは、SystemModelBuilderのアルゴリズムレベルの単体テストです。
ただし、executeステージでの包括的なテスト（test_build_model.py）で
同様の検証が行われるため、そちらを優先してください。

このファイルは、アルゴリズムレベルの詳細な検証が必要な場合にのみ使用してください。
"""

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model import (  # noqa: E501
    PieCableModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model import (  # noqa: E501
    SingleCageImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_system_model import (  # noqa: E501
    ImPieCableSystemModelBuilder,
)
from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos,
)


@pytest.fixture
def input_im_cable_system_dtos():
    """テスト用のInputDtos fixture."""
    return make_input_im_cable_system_dtos().get_all()


def _build_dependencies(dto, config, logger):
    """SystemModelBuilderの依存DTOを構築する。"""
    im_builder = SingleCageImModelBuilder.create(config=config, logger=logger)  # type: ignore
    cable_builder = PieCableModelBuilder.create(config=config, logger=logger)  # type: ignore

    # InputDto.array_layoutを直接使用
    model_array_layout = dto.array_layout

    # ItmImModelDtoを構築
    itm_im_model_dto = im_builder.build(
        im_dto=dto.im,
        model_array_layout=model_array_layout,
    )

    # ItmCableModelDtoを構築
    # ケーブルがNoneの場合は、build()メソッド内で完全導体かつ完全絶縁の擬似ケーブルモデルを作成
    itm_cable_model_dto = cable_builder.build(
        cable_dto=dto.cable,
        model_array_layout=model_array_layout,
    )

    return model_array_layout, itm_im_model_dto, itm_cable_model_dto


class TestSystemModelBuilder:
    def test_build_system_shapes(
        self,
        input_im_cable_system_dtos,
        config,
        logger,
    ) -> None:
        """build()の戻りDTOの形状を検証する。

        - システム位相インピーダンス/アドミタンスが (num_slips, num_freqs)
          の形状であること
        """
        system_builder = ImPieCableSystemModelBuilder.create(
            config=config,
            logger=logger,
        )  # type: ignore

        for dto in input_im_cable_system_dtos:
            (
                model_array_layout,
                itm_im_model_dto,
                itm_cable_model_dto,
            ) = _build_dependencies(dto=dto, config=config, logger=logger)

            system_model = system_builder.build(
                itm_im_model_dto=itm_im_model_dto,
                itm_cable_model_dto=itm_cable_model_dto,
            )

            expected_shape = model_array_layout.shape
            assert (
                system_model.system_phase_impedance.value.shape
                == expected_shape
            )
            assert (
                system_model.system_phase_admittance.value.shape
                == expected_shape
            )

    def test_impedance_admittance_relationship(
        self,
        input_im_cable_system_dtos,
        config,
        logger,
    ) -> None:
        """システム位相アドミタンスがインピーダンスの逆数になることを検証。"""
        system_builder = ImPieCableSystemModelBuilder.create(
            config=config,
            logger=logger,
        )  # type: ignore

        for dto in input_im_cable_system_dtos:
            (
                model_array_layout,
                itm_im_model_dto,
                itm_cable_model_dto,
            ) = _build_dependencies(dto=dto, config=config, logger=logger)

            system_model = system_builder.build(
                itm_im_model_dto=itm_im_model_dto,
                itm_cable_model_dto=itm_cable_model_dto,
            )

            admittance_from_impedance_dto = admittance_from_impedance(
                eps=config.numerical_guard_config.eps,
                max_mag=1.0 / config.numerical_guard_config.eps,
                impedance=system_model.system_phase_impedance,
            )

            np.testing.assert_allclose(
                system_model.system_phase_admittance.get_value(),
                admittance_from_impedance_dto.get_value(),
                rtol=1e-10,
                atol=1e-12,
            )

    def test_ideal_cable_system_equals_im_impedance(
        self,
        input_im_cable_system_dtos,
        config,
        logger,
    ) -> None:
        """理想ケーブル（完全絶縁かつ理想導体）の場合、システムインピーダンスがIMインピーダンスと一致することを検証。

        理想ケーブルの場合、ケーブルの影響が無視できるため、
        システムインピーダンスは誘導電動機のインピーダンスそのものになる。
        """
        system_builder = ImPieCableSystemModelBuilder.create(
            config=config,
            logger=logger,
        )  # type: ignore

        # システム1は理想ケーブル（MAIN_IDEAL + MLE_IDEAL）を使用
        dto = input_im_cable_system_dtos[0]

        (
            model_array_layout,
            itm_im_model_dto,
            itm_cable_model_dto,
        ) = _build_dependencies(dto=dto, config=config, logger=logger)

        system_model = system_builder.build(
            itm_im_model_dto=itm_im_model_dto,
            itm_cable_model_dto=itm_cable_model_dto,
        )

        # 理想ケーブルの場合、システムインピーダンスはIMのインピーダンスそのもの
        im_impedance = itm_im_model_dto.total_model.impedance.to_base_unit()
        system_impedance = system_model.system_phase_impedance.to_base_unit()

        np.testing.assert_allclose(
            system_impedance.get_value(),
            im_impedance.get_value(),
            rtol=1e-10,
            atol=1e-12,
        )

        # システムアドミタンスもIMのアドミタンスそのもの
        im_admittance = itm_im_model_dto.total_model.admittance.to_base_unit()
        system_admittance = system_model.system_phase_admittance.to_base_unit()

        np.testing.assert_allclose(
            system_admittance.get_value(),
            im_admittance.get_value(),
            rtol=1e-10,
            atol=1e-12,
        )
