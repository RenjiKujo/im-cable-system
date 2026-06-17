"""IMケーブルモデル構築オーケストレーターのテスト。

このモジュールは、ImCableModelBuildOrchestratorのテストを提供します。
"""

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model import (  # noqa: E501
    DoubleCageImModelBuilder,
    ImModelBuilderFactory,
    SingleCageImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ImCageMultiplicityType,
    PieCableConductorKey,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos,
)


@pytest.fixture
def input_im_cable_system_dtos():
    """テスト用のInputDtos fixture."""
    return make_input_im_cable_system_dtos().get_all()


class TestImCableModelBuildOrchestrator:
    """ImCableModelBuildOrchestratorのテストクラス。"""

    def test_im_model_builder_factory_selects_builder_by_cage_multiplicity(
        self,
        config,
        logger,
    ) -> None:
        """かご重数に応じて IM モデルビルダーが選ばれることを確認する。"""
        single_builder = ImModelBuilderFactory.create(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            config=config,
            logger=logger,
        )
        assert isinstance(single_builder, SingleCageImModelBuilder)

        double_builder = ImModelBuilderFactory.create(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            config=config,
            logger=logger,
        )
        assert isinstance(double_builder, DoubleCageImModelBuilder)

    def test_build_creates_model_for_repeated_inputs(
        self,
        config,
        logger,
        input_im_cable_system_dtos,
    ) -> None:
        """buildが入力ごとにモデルDTOを構築できることを確認する。

        - システム1: input_line_currentなし
        - システム2: input_line_currentあり
        """
        orchestrator = ImCableModelBuildOrchestrator.create(
            config=config,
            logger=logger,
        )

        dto_1 = input_im_cable_system_dtos[0]
        result_1 = orchestrator.build(dto_1)
        assert result_1.im is not None
        assert result_1.cable is not None
        assert result_1.system is not None

        dto_2 = input_im_cable_system_dtos[1]
        orchestrator_2 = ImCableModelBuildOrchestrator.create(
            config=config,
            logger=logger,
        )
        result_2 = orchestrator_2.build(dto_2)
        assert result_2.im is not None
        assert result_2.cable is not None
        assert result_2.system is not None

    def test_build_creates_correct_model_dto(
        self,
        config,
        logger,
        input_im_cable_system_dtos,
    ) -> None:
        """buildで正しいモデルDTOが生成されることを確認する。

        - ItmModelDtoが正しく構築されること
        - 配列レイアウトが正しい形状であること
        - 各モデルDTOが正しく構築されること
        """
        orchestrator = ImCableModelBuildOrchestrator.create(
            config=config,
            logger=logger,
        )

        for dto in input_im_cable_system_dtos:
            result = orchestrator.build(dto)

            # ItmModelDtoが正しく構築されること
            assert result is not None
            assert result.array_layout is not None
            assert result.im is not None
            assert result.cable is not None
            assert result.system is not None

            # 配列レイアウトが正しい形状であること
            # InputDto.array_layoutのshapeを直接使用
            expected_shape = dto.array_layout.shape
            assert result.array_layout.shape == expected_shape

            # 各モデルDTOの配列形状が正しいこと
            assert result.im.total_model.impedance.value.shape == expected_shape
            # ケーブルモデルのインピーダンス形状を確認
            # ItmCableImmittanceDtoにはconductor_impedance（辞書）がある
            assert (
                result.cable.cable_immittance.conductor_impedance[
                    PieCableConductorKey.SINGLE
                ].value.shape
                == expected_shape
            )
            assert (
                result.system.system_phase_impedance.value.shape
                == expected_shape
            )

    def test_build_with_none_cable(
        self,
        config,
        logger,
        input_im_cable_system_dtos,
    ) -> None:
        """ケーブルがNoneの場合でもbuildが正常に動作することを確認する。

        - ケーブルがNoneのシステムが少なくとも1つ存在することを前提とする
        - この場合、完全導体かつ完全絶縁の擬似ケーブルモデルが作成される
        """
        orchestrator = ImCableModelBuildOrchestrator.create(
            config=config,
            logger=logger,
        )

        # ケーブルがNoneのシステムを検索する
        dto_no_cable = next(
            dto for dto in input_im_cable_system_dtos if dto.cable is None
        )

        result = orchestrator.build(dto_no_cable)

        # 正常に構築されること
        assert result is not None
        assert result.cable is not None
        assert result.system is not None

        # 配列形状が正しいこと
        # InputDto.array_layoutのshapeを直接使用
        expected_shape = dto_no_cable.array_layout.shape
        assert result.array_layout.shape == expected_shape

    def test_array_layout_matches_input_arrays(
        self,
        config,
        logger,
        input_im_cable_system_dtos,
    ) -> None:
        """配列レイアウトが入力配列と一致することを確認する。

        - slip配列とfrequency配列が正しく反映されること
        """
        orchestrator = ImCableModelBuildOrchestrator.create(
            config=config,
            logger=logger,
        )

        for dto in input_im_cable_system_dtos:
            result = orchestrator.build(dto)

            # 入力配列の値を取得
            input_slip = dto.array_layout.arrays[ArrayKey.SLIP].get_value()
            input_frequency = dto.array_layout.arrays[
                ArrayKey.FREQUENCY
            ].get_value()

            # 配列レイアウトから配列を取得
            layout_slip = result.array_layout.arrays[ArrayKey.SLIP].get_value()
            layout_frequency = result.array_layout.arrays[
                ArrayKey.FREQUENCY
            ].get_value()

            # 値が一致すること
            np.testing.assert_array_equal(layout_slip, input_slip)
            np.testing.assert_array_equal(layout_frequency, input_frequency)
