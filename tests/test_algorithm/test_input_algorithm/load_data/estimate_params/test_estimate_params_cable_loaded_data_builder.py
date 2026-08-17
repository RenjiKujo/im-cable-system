"""``cable_loaded_data_builder`` の単体テスト。

ケーブル長 0 / ``cable_conductor`` 未指定での ``None`` 短絡と、通常ケース
で :class:`CableLoadedData` が中点ベースの値・SI 単位・``BASIC`` 系の
``conductor_model_params=None`` を満たして構築されることを確認する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.bounds_yaml_parser import (  # noqa: E501
    load_cable_parameter_fit_descriptor_bounds,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cable_loaded_data_builder import (  # noqa: E501
    build_cable_loaded_data,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    EstimateParamsModelCombo,
)
from im_cable_system.engine.shared.config import IConfig
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ConductorModelType,
    ImExcitationModelType,
    ImFrictionWindageModelType,
    ImPrimaryModelType,
    ImSecondaryModelType,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
)


def _combo(
    cable_conductor: ConductorModelType | None,
) -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelType.BASIC,
        excitation=ImExcitationModelType.BASIC,
        secondary_inner=None,
        secondary_outer=ImSecondaryModelType.BASIC,
        cable_conductor=cable_conductor,
        friction_windage=ImFrictionWindageModelType.NONE,
        stray_load=ImStrayLoadModelType.NONE,
        primary_index=1,
        excitation_index=1,
        secondary_single_index=1,
        secondary_double_outer_index=0,
        secondary_double_inner_index=0,
        cable_conductor_index=0 if cable_conductor is None else 1,
        friction_windage_index=1,
        stray_load_index=1,
    )


@pytest.fixture
def cable_bounds(config: IConfig) -> CableParameterFitDescriptorBounds:
    """テスト用ケーブル探索境界 YAML から構築した境界 DTO。"""
    return load_cable_parameter_fit_descriptor_bounds(
        config.get_cable_bounds_and_init_file_path(),
    )


class TestBuildCableLoadedData:
    """``build_cable_loaded_data`` の正常・異常系。"""

    def test_returns_none_when_cable_length_zero(
        self,
        cable_bounds: CableParameterFitDescriptorBounds,
    ) -> None:
        result = build_cable_loaded_data(
            combo=_combo(ConductorModelType.BASIC),
            cable_length=0.0,
            cable_length_unit="m",
            bounds=cable_bounds,
            cable_name="cable_test",
            section_name="section_0",
        )
        assert result is None

    def test_returns_none_when_cable_conductor_is_none(
        self,
        cable_bounds: CableParameterFitDescriptorBounds,
    ) -> None:
        result = build_cable_loaded_data(
            combo=_combo(None),
            cable_length=100.0,
            cable_length_unit="m",
            bounds=cable_bounds,
            cable_name="cable_test",
            section_name="section_0",
        )
        assert result is None

    def test_returns_cable_for_basic_conductor(
        self,
        cable_bounds: CableParameterFitDescriptorBounds,
    ) -> None:
        result = build_cable_loaded_data(
            combo=_combo(ConductorModelType.BASIC),
            cable_length=100.0,
            cable_length_unit="m",
            bounds=cable_bounds,
            cable_name="cable_test",
            section_name="section_0",
        )
        assert isinstance(result, CableLoadedData)
        assert result.name == "cable_test"
        assert result.conductor_model == ConductorModelType.BASIC.value
        # BASIC は params 不要 → None に丸める
        assert result.conductor_model_params is None
        assert len(result.sections) == 1
        section = result.sections[0]
        assert section.name == "section_0"
        assert section.length == 100.0
        assert section.length_unit == "m"
        assert section.shape_type == "ROUND"
        assert section.conductor_resistance_per_length_unit == "Ω/m"
        assert section.conductor_inductance_per_length_unit == "H/m"
        assert section.ground_resistance_length_unit == "Ω*m"
        assert section.ground_capacitance_per_length_unit == "F/m"
        assert section.conductor_resistance_per_length > 0.0
        assert section.conductor_inductance_per_length > 0.0
        assert section.ground_resistance_length > 0.0
        assert section.ground_capacitance_per_length > 0.0

    def test_returns_cable_with_params_dict_for_non_basic_conductor(
        self,
        cable_bounds: CableParameterFitDescriptorBounds,
    ) -> None:
        """非 BASIC モデルでは ``conductor_model_params`` が dict で残る。"""
        result = build_cable_loaded_data(
            combo=_combo(ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1),
            cable_length=100.0,
            cable_length_unit="m",
            bounds=cable_bounds,
            cable_name="cable_test",
            section_name="section_0",
        )
        assert isinstance(result, CableLoadedData)
        assert (
            result.conductor_model
            == ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1.value
        )
        params = result.conductor_model_params
        assert isinstance(params, dict)
        assert set(params.keys()) == {
            "alpha_conductor_r",
            "beta_conductor_r",
            "alpha_conductor_x",
            "beta_conductor_x",
        }
        assert all(isinstance(value, float) for value in params.values())
