"""``im_loaded_data_builder`` の単体テスト。

``build_nameplate`` と ``build_im_loaded_data`` の正常・異常系を、手動で
組み立てた :class:`EstimateParamsParsedTables` および実 YAML から読んだ
:class:`ImParameterFitDescriptorBounds` の下で検証する。

R/L とモデル係数の中点による初期化や、SINGLE_CAGE / DOUBLE_CAGE の R/L
半分割りなど、Loader 内に閉じていたロジックを直接観測できることを確認
する位置付けのテスト。

内部実装の単体テスト。公開窓口に載っていないリーフを直 import する。
とくに ``assemble_input_dto.common.im_dto_builder`` は別責務ツリー（assemble
段）の非公開リーフだが、「load は係数名を絞り込まず、過不足の判定は DTO
``__post_init__`` が持つ」という段またぎの責務分担を検証するために必要。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.im_dto_builder import (  # noqa: E501
    build_im_series_dto,
)
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
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    ImExcitationModelName,
    ImFrictionWindageModelName,
    ImParameterFitDescriptorBounds,
    ImPrimaryModelName,
    ImSecondaryModelName,
    ImStrayLoadModelName,
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
        candidate_friction_windage=(),
        candidate_stray_load=(),
        candidate_cable_conductor=(),
        supply_block={},
        curve_header_row=[],
        curve_unit_row=[],
        curve_data_rows=[],
    )


def _basic_combo_single_cage() -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelName("BASIC"),
        excitation=ImExcitationModelName("BASIC"),
        secondary_inner=None,
        secondary_outer=ImSecondaryModelName("BASIC"),
        cable_conductor=None,
        friction_windage=ImFrictionWindageModelName("NONE"),
        stray_load=ImStrayLoadModelName("NONE"),
        primary_index=1,
        excitation_index=1,
        secondary_single_index=1,
        secondary_double_outer_index=0,
        secondary_double_inner_index=0,
        cable_conductor_index=0,
        friction_windage_index=1,
        stray_load_index=1,
    )


def _basic_combo_double_cage() -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelName("BASIC"),
        excitation=ImExcitationModelName("BASIC"),
        secondary_inner=ImSecondaryModelName("BASIC"),
        secondary_outer=ImSecondaryModelName("BASIC"),
        cable_conductor=None,
        friction_windage=ImFrictionWindageModelName("NONE"),
        stray_load=ImStrayLoadModelName("NONE"),
        primary_index=1,
        excitation_index=1,
        secondary_single_index=0,
        secondary_double_outer_index=1,
        secondary_double_inner_index=1,
        cable_conductor_index=0,
        friction_windage_index=1,
        stray_load_index=1,
    )


def _shaft_output_deduction_combo_single_cage() -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelName("BASIC"),
        excitation=ImExcitationModelName("BASIC"),
        secondary_inner=None,
        secondary_outer=ImSecondaryModelName("BASIC"),
        cable_conductor=None,
        friction_windage=ImFrictionWindageModelName("CONSTANT_V1"),
        stray_load=ImStrayLoadModelName("CURRENT_DEPENDENT_QUADRATIC_V1"),
        primary_index=1,
        excitation_index=1,
        secondary_single_index=1,
        secondary_double_outer_index=0,
        secondary_double_inner_index=0,
        cable_conductor_index=0,
        friction_windage_index=1,
        stray_load_index=1,
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
        assert im.primary.model == "BASIC"
        assert im.excitation.model == "BASIC"
        assert im.secondary.model == "BASIC"
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

    def test_builds_friction_windage_and_stray_load_branches(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
    ) -> None:
        """combo に軸出力控除モデルを指定すると bounds YAML の初期値が入る。"""
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_shaft_output_deduction_combo_single_cage(),
            bounds=im_bounds,
            nameplate=_make_nameplate(),
            im_name="im_deduction",
        )
        assert im.friction_windage.model == "CONSTANT_V1"
        assert "k_friction_windage" in im.friction_windage.model_params
        assert im.stray_load.model == "CURRENT_DEPENDENT_QUADRATIC_V1"
        assert "k_stray_load" in im.stray_load.model_params

    def test_none_combo_yields_empty_shaft_output_deduction_params(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
    ) -> None:
        """既定（NONE）の combo では軸出力控除 params が空辞書のまま。"""
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_basic_combo_single_cage(),
            bounds=im_bounds,
            nameplate=_make_nameplate(),
            im_name="im_test_none",
        )
        assert im.friction_windage.model == "NONE"
        assert im.friction_windage.model_params == {}
        assert im.stray_load.model == "NONE"
        assert im.stray_load.model_params == {}

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


_MIDPOINT = "{ method: midpoint }"

_BASE_IM_BOUNDS_YAML = f"""\
version: 1
primary:
  rl_parameters:
    primary_resistance:
      unit: "Ω"
      bounds: {{ lb: 0.1, ub: 0.5 }}
      init: {_MIDPOINT}
    primary_inductance:
      unit: "H"
      bounds: {{ lb: 0.001, ub: 0.01 }}
      init: {_MIDPOINT}
  model_parameters:
    BASIC:
      params: {{}}
    SLIP_DEPENDENT_LEAKAGE_SATURATION_V1:
      params:
        alpha_primary_r:
          bounds: {{ lb: 0.05, ub: 0.15 }}
          init: {_MIDPOINT}
        alpha_primary_x:
          bounds: {{ lb: 0.05, ub: 0.15 }}
          init: {_MIDPOINT}
        beta_primary_x:
          bounds: {{ lb: 0.1, ub: 0.3 }}
          init: {_MIDPOINT}
excitation:
  rl_parameters:
    excitation_resistance:
      unit: "Ω"
      bounds: {{ lb: 100.0, ub: 200.0 }}
      init: {_MIDPOINT}
    excitation_inductance:
      unit: "H"
      bounds: {{ lb: 0.01, ub: 0.05 }}
      init: {_MIDPOINT}
  model_parameters:
    BASIC:
      params: {{}}
secondary:
  rl_parameters:
    secondary_resistance:
      unit: "Ω"
      bounds: {{ lb: 0.05, ub: 0.4 }}
      init: {_MIDPOINT}
    secondary_inductance:
      unit: "H"
      bounds: {{ lb: 0.001, ub: 0.01 }}
      init: {_MIDPOINT}
  model_parameters:
    BASIC:
      params: {{}}
friction_windage:
  model_parameters:
    NONE:
      params: {{}}
stray_load:
  model_parameters:
    NONE:
      params: {{}}
"""


def _slip_dep_primary_combo() -> EstimateParamsModelCombo:
    return EstimateParamsModelCombo(
        primary=ImPrimaryModelName("SLIP_DEPENDENT_LEAKAGE_SATURATION_V1"),
        excitation=ImExcitationModelName("BASIC"),
        secondary_inner=None,
        secondary_outer=ImSecondaryModelName("BASIC"),
        cable_conductor=None,
        friction_windage=ImFrictionWindageModelName("NONE"),
        stray_load=ImStrayLoadModelName("NONE"),
        primary_index=1,
        excitation_index=1,
        secondary_single_index=1,
        secondary_double_outer_index=0,
        secondary_double_inner_index=0,
        cable_conductor_index=0,
        friction_windage_index=1,
        stray_load_index=1,
    )


def _write_im_bounds_yaml(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "im_bounds.yaml"
    path.write_text(body, encoding="utf-8")
    return path


class TestBuildImLoadedDataDoesNotEnforceParamContract:
    """load は係数名の過不足を判定せず、YAML の params をそのまま載せる。"""

    def test_extra_param_in_yaml_is_kept_in_model_params(
        self,
        tmp_path: Path,
    ) -> None:
        body = _BASE_IM_BOUNDS_YAML.replace(
            "beta_primary_x:\n"
            "          bounds: { lb: 0.1, ub: 0.3 }\n"
            "          init: { method: midpoint }",
            "beta_primary_x:\n"
            "          bounds: { lb: 0.1, ub: 0.3 }\n"
            "          init: { method: midpoint }\n"
            "        alpha_typo:\n"
            "          bounds: { lb: 0.0, ub: 1.0 }\n"
            "          init: { method: midpoint }",
        )
        bounds = load_im_parameter_fit_descriptor_bounds(
            _write_im_bounds_yaml(tmp_path, body),
        )
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_slip_dep_primary_combo(),
            bounds=bounds,
            nameplate=_make_nameplate(),
            im_name="im_extra",
        )
        assert "alpha_typo" in im.primary.model_params
        assert set(im.primary.model_params) == {
            "alpha_primary_r",
            "alpha_primary_x",
            "beta_primary_x",
            "alpha_typo",
        }

    def test_missing_param_in_yaml_is_not_rejected_at_load(
        self,
        tmp_path: Path,
    ) -> None:
        body = _BASE_IM_BOUNDS_YAML.replace(
            "        beta_primary_x:\n"
            "          bounds: { lb: 0.1, ub: 0.3 }\n"
            "          init: { method: midpoint }\n",
            "",
        )
        bounds = load_im_parameter_fit_descriptor_bounds(
            _write_im_bounds_yaml(tmp_path, body),
        )
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_slip_dep_primary_combo(),
            bounds=bounds,
            nameplate=_make_nameplate(),
            im_name="im_missing_param",
        )
        assert set(im.primary.model_params) == {
            "alpha_primary_r",
            "alpha_primary_x",
        }

    def test_missing_model_type_key_raises_key_error(
        self,
        tmp_path: Path,
    ) -> None:
        body = _BASE_IM_BOUNDS_YAML.replace(
            "    SLIP_DEPENDENT_LEAKAGE_SATURATION_V1:\n"
            "      params:\n"
            "        alpha_primary_r:\n"
            "          bounds: { lb: 0.05, ub: 0.15 }\n"
            "          init: { method: midpoint }\n"
            "        alpha_primary_x:\n"
            "          bounds: { lb: 0.05, ub: 0.15 }\n"
            "          init: { method: midpoint }\n"
            "        beta_primary_x:\n"
            "          bounds: { lb: 0.1, ub: 0.3 }\n"
            "          init: { method: midpoint }\n",
            "",
        )
        bounds = load_im_parameter_fit_descriptor_bounds(
            _write_im_bounds_yaml(tmp_path, body),
        )
        with pytest.raises(KeyError, match="unknown IM primary model"):
            build_im_loaded_data(
                parsed=_make_parsed(),
                combo=_slip_dep_primary_combo(),
                bounds=bounds,
                nameplate=_make_nameplate(),
                im_name="im_missing_type",
            )

    def test_extra_param_from_load_is_rejected_at_assemble(
        self,
        tmp_path: Path,
    ) -> None:
        """load が通した余分な係数は assemble の DTO が ``余分`` で弾く。"""

        body = _BASE_IM_BOUNDS_YAML.replace(
            "beta_primary_x:\n"
            "          bounds: { lb: 0.1, ub: 0.3 }\n"
            "          init: { method: midpoint }",
            "beta_primary_x:\n"
            "          bounds: { lb: 0.1, ub: 0.3 }\n"
            "          init: { method: midpoint }\n"
            "        alpha_typo:\n"
            "          bounds: { lb: 0.0, ub: 1.0 }\n"
            "          init: { method: midpoint }",
        )
        bounds = load_im_parameter_fit_descriptor_bounds(
            _write_im_bounds_yaml(tmp_path, body),
        )
        im = build_im_loaded_data(
            parsed=_make_parsed(),
            combo=_slip_dep_primary_combo(),
            bounds=bounds,
            nameplate=_make_nameplate(),
            im_name="im_extra_assemble",
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im)
        msg = str(excinfo.value)
        assert "余分" in msg
        assert "alpha_typo" in msg


class TestBuildImLoadedDataUnknownComboModelName:
    """combo 側の未知名は bounds カタログ照合で KeyError になる。"""

    def test_unknown_primary_in_combo_raises_key_error(
        self,
        im_bounds: ImParameterFitDescriptorBounds,
    ) -> None:
        combo = EstimateParamsModelCombo(
            primary=ImPrimaryModelName("NOT_A_REAL_PRIMARY"),
            excitation=ImExcitationModelName("BASIC"),
            secondary_inner=None,
            secondary_outer=ImSecondaryModelName("BASIC"),
            cable_conductor=None,
            friction_windage=ImFrictionWindageModelName("NONE"),
            stray_load=ImStrayLoadModelName("NONE"),
            primary_index=1,
            excitation_index=1,
            secondary_single_index=1,
            secondary_double_outer_index=0,
            secondary_double_inner_index=0,
            cable_conductor_index=0,
            friction_windage_index=1,
            stray_load_index=1,
        )
        with pytest.raises(KeyError, match="unknown IM primary model"):
            build_im_loaded_data(
                parsed=_make_parsed(),
                combo=combo,
                bounds=im_bounds,
                nameplate=_make_nameplate(),
                im_name="im_unknown_primary",
            )
