"""SingleCageImModelBuilder の単体テスト（代表 InputDto 1 件）。

``build()`` が返す IM モデル DTO について、各イミタンスの配列形状・単位・有限性を
代表 InputDto で検証する。教科書値（インピーダンス解）や全 InputDto 網羅は
``orchestrate/forward`` および ``test_all_stage`` 側に集約している。
Y=1/Z などの数値変換そのものは domain 層テストで担保する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model import (  # noqa: E501
    SingleCageImModelBuilder,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.input import InputDtos
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos,
)

_SC = ImSecondaryCageBranchType.SINGLE


@pytest.fixture
def input_im_cable_system_dtos() -> InputDtos:
    """テスト用のInputDtos fixture."""
    return make_input_im_cable_system_dtos()


class TestSingleCageImModelBuilder:
    """SingleCageImModelBuilder の build() 契約検証。"""

    def test_build_shapes_units_and_finite(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """代表 InputDto で各イミタンスの形状・単位・有限性を検証する。"""
        builder = SingleCageImModelBuilder.create(config=config, logger=logger)  # type: ignore
        input_dto = input_im_cable_system_dtos.get_all()[0]
        array_layout = input_dto.array_layout

        itm_im = builder.build(
            im_dto=input_dto.im,
            model_array_layout=array_layout,
        )

        secondary = itm_im.secondary_model
        impedances = [
            itm_im.primary_impedance,
            itm_im.excitation_impedance,
            secondary.impedances[_SC],
            secondary.base_impedances[_SC],
            secondary.load_impedances[_SC],
            itm_im.total_impedance,
        ]
        admittances = [
            itm_im.primary_admittance,
            itm_im.excitation_admittance,
            secondary.admittances[_SC],
            secondary.base_admittances[_SC],
            secondary.load_admittances[_SC],
            itm_im.total_admittance,
        ]

        expected_shape = array_layout.shape
        for impedance in impedances:
            assert impedance.unit == "Ω"
            assert impedance.value.shape == expected_shape
            assert np.all(np.isfinite(impedance.value))
        for admittance in admittances:
            assert admittance.unit == "S"
            assert admittance.value.shape == expected_shape
            assert np.all(np.isfinite(admittance.value))

    def test_build_retains_input_name_and_rl(
        self,
        input_im_cable_system_dtos: InputDtos,
        config,
        logger,
    ) -> None:
        """ItmImModelDto が InputDto 由来の個体名・基本 R/L を保持する。"""
        builder = SingleCageImModelBuilder.create(config=config, logger=logger)  # type: ignore
        input_dto = input_im_cable_system_dtos.get_all()[0]
        im_series = input_dto.im.im_series
        assert im_series is not None

        itm_im = builder.build(
            im_dto=input_dto.im,
            model_array_layout=input_dto.array_layout,
        )

        # 個体名（SINGLE/UPPER/LOWER 等）が欠落しない
        assert itm_im.name == input_dto.im.name
        # 一次・励磁の基本 R/L が入力値のまま残る
        assert itm_im.primary_model.resistance == im_series.primary_resistance
        assert itm_im.primary_model.inductance == im_series.primary_inductance
        assert (
            itm_im.excitation_model.resistance
            == im_series.excitation_resistance
        )
        assert (
            itm_im.excitation_model.inductance
            == im_series.excitation_inductance
        )
        # 二次（単一かご）の基本 R/L が枝キー付きで残る
        assert itm_im.secondary_model.resistances is not None
        assert itm_im.secondary_model.inductances is not None
        assert (
            itm_im.secondary_model.resistances[_SC]
            == im_series.secondary_resistances[_SC]
        )
        assert (
            itm_im.secondary_model.inductances[_SC]
            == im_series.secondary_inductances[_SC]
        )
