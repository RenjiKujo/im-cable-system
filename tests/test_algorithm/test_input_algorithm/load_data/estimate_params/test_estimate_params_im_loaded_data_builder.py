"""``im_loaded_data_builder`` の単体テスト。

``build_nameplate`` と ``build_im_loaded_data`` の正常・異常系を、手動で
組み立てた :class:`EstimateParamsParsedTables` および実 YAML から読んだ
:class:`ImParameterFitDescriptorBounds` の下で検証する。

R/L とモデル係数の中点による初期化や、SINGLE_CAGE / DOUBLE_CAGE の R/L
半分割りなど、Loader 内に閉じていたロジックを直接観測できることを確認
する位置付けのテスト。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImNameplateLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.bounds_yaml_parser import (  # noqa: E501
    load_im_parameter_fit_descriptor_bounds,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    EstimateParamsModelCombo,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.im_loaded_data_builder import (  # noqa: E501
    build_im_loaded_data,
    build_nameplate,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
    FixedCell,
)
from im_cable_system.engine.shared.config import IConfig
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImExcitationModelType,
    ImPrimaryModelType,
    ImSecondaryModelType,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    ImParameterFitDescriptorBounds,
)

_VALID_NAMEPLATE_BLOCK = {
    "input_line_voltage": (400.0, "V"),
    "input_line_current": (10.0, "A"),
    "output_power": (5000.0, "W"),
    "frequency": (50.0, "Hz"),
}

_VALID_FIXED = {
    "im_poles": FixedCell(value="4", unit=None),
    "im_circuit_type": FixedCell(value="L", unit=None),
    "im_connection_type": FixedCell(value="STAR", unit=None),
}


def _make_parsed(
    *,
    nameplate_block: dict[str, tuple[float, str]] | None = None,
    fixed: dict[str, FixedCell] | None = None,
) -> EstimateParamsParsedTables:
    """``nameplate_block`` と ``fixed`` セクションのみ意味あるダミー ParsedTables。"""
    return EstimateParamsParsedTables(
        im_performance_curve_name="dummy_curve",
        nameplate_block=(
            nameplate_block
            if nameplate_block is not None
            else _VALID_NAMEPLATE_BLOCK
        ),
        fixed=fixed if fixed is not None else _VALID_FIXED,
        candidate_primary=(),
        candidate_excitation=(),
        candidate_secondary_single=(),
        candidate_secondary_double_inner=(),
        candidate_secondary_double_outer=(),
        candidate_cable_conductor=(),
        supply_block={},
        curve_header_row=[],
        curve_unit_row=[],
        curve_data_rows=[],
    )


def _basic_combo_single_cage() -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelType.BASIC,
        excitation=ImExcitationModelType.BASIC,
        secondary_inner=None,
        secondary_outer=ImSecondaryModelType.BASIC,
        cable_conductor=None,
    )


def _basic_combo_double_cage() -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelType.BASIC,
        excitation=ImExcitationModelType.BASIC,
        secondary_inner=ImSecondaryModelType.BASIC,
        secondary_outer=ImSecondaryModelType.BASIC,
        cable_conductor=None,
    )


def _make_nameplate() -> ImNameplateLoadedData:
    return ImNameplateLoadedData(
        voltage=400.0,
        voltage_unit="V",
        current=10.0,
        current_unit="A",
        power=5000.0,
        power_unit="W",
        frequency=50.0,
        frequency_unit="Hz",
    )


@pytest.fixture
def im_bounds(config: IConfig) -> ImParameterFitDescriptorBounds:
    """テスト用 IM 探索境界 YAML から構築した境界 DTO。"""
    return load_im_parameter_fit_descriptor_bounds(
        config.get_im_bounds_and_init_file_path(),
    )


class TestBuildNameplate:
    """``build_nameplate`` の正常・異常系。"""

    def test_returns_nameplate_when_all_keys_present(self) -> None:
        nameplate = build_nameplate(_make_parsed())
        assert isinstance(nameplate, ImNameplateLoadedData)
        assert nameplate.voltage == 400.0
        assert nameplate.voltage_unit == "V"
        assert nameplate.current == 10.0
        assert nameplate.power == 5000.0
        assert nameplate.frequency == 50.0
        assert nameplate.frequency_unit == "Hz"

    @pytest.mark.parametrize(
        "missing_key",
        [
            "input_line_voltage",
            "input_line_current",
            "output_power",
            "frequency",
        ],
    )
    def test_raises_when_required_key_missing(self, missing_key: str) -> None:
        block = {
            k: v for k, v in _VALID_NAMEPLATE_BLOCK.items() if k != missing_key
        }
        parsed = _make_parsed(nameplate_block=block)
        with pytest.raises(
            ValueError,
            match=f"nameplate セクションに必須キー {missing_key!r}",
        ):
            build_nameplate(parsed)


class TestBuildImLoadedData:
    """``build_im_loaded_data`` の正常・異常系。"""

    def test_returns_single_cage_when_inner_is_none(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
    ) -> None:
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_basic_combo_single_cage(),
            bounds=im_bounds,
            nameplate=_make_nameplate(),
            im_name="im_test",
        )
        assert im.name == "im_test"
        assert im.poles == 4
        assert im.cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE.value
        assert im.connection_type == "STAR"
        assert im.circuit_type == "L"
        assert im.secondary is not None
        assert im.secondary_inner is None
        assert im.secondary_outer is None
        assert im.primary.model == ImPrimaryModelType.BASIC.value
        assert im.excitation.model == ImExcitationModelType.BASIC.value
        assert im.secondary.model == ImSecondaryModelType.BASIC.value
        assert im.primary.resistance_unit == "Ω"
        assert im.primary.inductance_unit == "H"
        assert im.primary.model_params == {}

    def test_returns_double_cage_with_half_rl_when_inner_present(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
    ) -> None:
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_basic_combo_double_cage(),
            bounds=im_bounds,
            nameplate=_make_nameplate(),
            im_name="im_double",
        )
        assert im.cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE.value
        assert im.secondary is None
        assert im.secondary_inner is not None
        assert im.secondary_outer is not None
        assert im.secondary_inner.resistance == pytest.approx(
            im.secondary_outer.resistance,
        )
        assert im.secondary_inner.inductance == pytest.approx(
            im.secondary_outer.inductance,
        )
        assert im.secondary_inner.resistance > 0.0
        assert im.secondary_inner.inductance > 0.0

    @pytest.mark.parametrize(
        "missing_key",
        ["im_poles", "im_circuit_type", "im_connection_type"],
    )
    def test_raises_when_required_fixed_key_missing(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
        missing_key: str,
    ) -> None:
        fixed = {k: v for k, v in _VALID_FIXED.items() if k != missing_key}
        with pytest.raises(ValueError, match=f"必須キー {missing_key!r}"):
            build_im_loaded_data(
                parsed=_make_parsed(fixed=fixed),
                combo=_basic_combo_single_cage(),
                bounds=im_bounds,
                nameplate=_make_nameplate(),
                im_name="im_missing",
            )

    def test_raises_when_im_poles_not_integer(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
    ) -> None:
        fixed = {**_VALID_FIXED, "im_poles": FixedCell(value="4.5", unit=None)}
        with pytest.raises(ValueError, match="整数である必要が"):
            build_im_loaded_data(
                parsed=_make_parsed(fixed=fixed),
                combo=_basic_combo_single_cage(),
                bounds=im_bounds,
                nameplate=_make_nameplate(),
                im_name="im_bad_poles",
            )
