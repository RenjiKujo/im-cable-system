"""統合 TSV のパース結果と探索境界から ``ImLoadedData`` を構築する。

責務:
    - :func:`build_nameplate`: ``nameplate`` セクションから
      :class:`ImNameplateLoadedData` を構築する。
    - :func:`build_im_loaded_data`: 1 直積要素分の :class:`ImLoadedData` を
      構築する。R/L とモデル係数の数値は
      :class:`ImParameterFitDescriptorBounds` の bounds + init 仕様
      （:mod:`bounds_initializer`）から決定する。

単位は :class:`ImParameterFitDescriptorBounds` の YAML 規約に準拠する SI
基本単位（Ω / H）で固定する。

値レベルの妥当性（正値・有限性、単位文字列の妥当性、配列長一致など）は
本層では検証せず、DTO ``__post_init__`` と ``_validate_input_dto`` に
寄せる（:class:`...load_data.i_data_loader.IInputDataLoader` の契約に従う）。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImBranchLoadedData,
    ImLoadedData,
    ImLossBranchLoadedData,
    ImNameplateLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.bounds_initializer import (  # noqa: E501
    im_fixed_initial,
    im_model_param_initials,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    EstimateParamsModelCombo,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.fixed_section_helpers import (  # noqa: E501
    fixed_required_int,
    fixed_required_str,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,  # load_data 生成定数（DTO 語彙同期。入力 parse ではない）
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    ImParameterFitDescriptorBounds,
    ImSecondaryModelName,
)

_RES_UNIT = "Ω"
_IND_UNIT = "H"

_NAMEPLATE_REQUIRED_KEYS = (
    "input_line_voltage",
    "input_line_current",
    "output_power",
    "frequency",
)


def build_nameplate(
    parsed: EstimateParamsParsedTables,
) -> ImNameplateLoadedData:
    """``nameplate`` セクションから ``ImNameplateLoadedData`` を構築する。

    Args:
        parsed: 統合 TSV のパース結果。

    Returns:
        ImNameplateLoadedData: 銘板中間表現。

    Raises:
        ValueError: ``input_line_voltage`` / ``input_line_current`` /
            ``output_power`` / ``frequency`` のいずれかが
            ``nameplate_block`` に無い場合。
    """
    nameplate = parsed.nameplate_block
    for required_key in _NAMEPLATE_REQUIRED_KEYS:
        if required_key not in nameplate:
            raise ValueError(
                f"統合 TSV nameplate セクションに必須キー "
                f"{required_key!r} がありません: "
                f"{parsed.im_performance_curve_name}"
            )
    voltage_v, voltage_unit = nameplate["input_line_voltage"]
    current_v, current_unit = nameplate["input_line_current"]
    power_v, power_unit = nameplate["output_power"]
    frequency_v, frequency_unit = nameplate["frequency"]
    return ImNameplateLoadedData(
        voltage=float(voltage_v),
        voltage_unit=str(voltage_unit),
        current=float(current_v),
        current_unit=str(current_unit),
        power=float(power_v),
        power_unit=str(power_unit),
        frequency=float(frequency_v),
        frequency_unit=str(frequency_unit),
    )


def _build_branch(
    *,
    model_value: str,
    model_params: dict[str, float],
    resistance: float,
    inductance: float,
) -> ImBranchLoadedData:
    return ImBranchLoadedData(
        model=model_value,
        model_params=model_params,
        resistance=resistance,
        resistance_unit=_RES_UNIT,
        inductance=inductance,
        inductance_unit=_IND_UNIT,
    )


def _build_primary_branch(
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
) -> ImBranchLoadedData:
    return _build_branch(
        model_value=combo.primary,
        model_params=im_model_param_initials("primary", combo.primary, bounds),
        resistance=im_fixed_initial("primary_resistance", bounds),
        inductance=im_fixed_initial("primary_inductance", bounds),
    )


def _build_excitation_branch(
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
) -> ImBranchLoadedData:
    return _build_branch(
        model_value=combo.excitation,
        model_params=im_model_param_initials(
            "excitation", combo.excitation, bounds
        ),
        resistance=im_fixed_initial("excitation_resistance", bounds),
        inductance=im_fixed_initial("excitation_inductance", bounds),
    )


def _build_secondary_branches_double_cage(
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
    total_resistance: float,
    total_inductance: float,
    *,
    inner_model: ImSecondaryModelName,
) -> tuple[ImBranchLoadedData, ImBranchLoadedData]:
    """二重かご時の内側・外側 secondary を構築する（R/L は半分ずつ）。"""
    half_r = total_resistance / 2.0
    half_l = total_inductance / 2.0
    inner = _build_branch(
        model_value=inner_model,
        model_params=im_model_param_initials("secondary", inner_model, bounds),
        resistance=half_r,
        inductance=half_l,
    )
    outer = _build_branch(
        model_value=combo.secondary_outer,
        model_params=im_model_param_initials(
            "secondary", combo.secondary_outer, bounds
        ),
        resistance=half_r,
        inductance=half_l,
    )
    return inner, outer


def _build_secondary_branch_single_cage(
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
    total_resistance: float,
    total_inductance: float,
) -> ImBranchLoadedData:
    return _build_branch(
        model_value=combo.secondary_outer,
        model_params=im_model_param_initials(
            "secondary", combo.secondary_outer, bounds
        ),
        resistance=total_resistance,
        inductance=total_inductance,
    )


def _build_friction_windage(
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
) -> ImLossBranchLoadedData:
    return ImLossBranchLoadedData(
        model=combo.friction_windage,
        model_params=im_model_param_initials(
            "friction_windage", combo.friction_windage, bounds
        ),
    )


def _build_stray_load(
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
) -> ImLossBranchLoadedData:
    return ImLossBranchLoadedData(
        model=combo.stray_load,
        model_params=im_model_param_initials(
            "stray_load", combo.stray_load, bounds
        ),
    )


def build_im_loaded_data(
    *,
    parsed: EstimateParamsParsedTables,
    combo: EstimateParamsModelCombo,
    bounds: ImParameterFitDescriptorBounds,
    nameplate: ImNameplateLoadedData,
    im_name: str,
) -> ImLoadedData:
    """1 直積要素分の ``ImLoadedData`` を構築する。

    ``combo.secondary_inner`` が ``None`` のとき単一かご、それ以外は二重
    かごとして ``secondary_resistance`` / ``secondary_inductance`` を内側・
    外側に半分ずつ割り当てる。

    Args:
        parsed: 統合 TSV のパース結果（``fixed_model_key`` を参照する）。
        combo: 1 直積要素（候補モデル種別の組み合わせ）。
        bounds: IM 探索境界。R/L とモデル係数は bounds + init 仕様で
            初期化する。
        nameplate: 銘板中間表現（:func:`build_nameplate` の戻り値）。
        im_name: ``ImLoadedData.name`` に割り当てる識別子。

    Returns:
        ImLoadedData: IM の中間表現。

    Raises:
        ValueError: ``fixed_model_key`` に ``im_poles`` / ``im_circuit_type``
            / ``im_connection_type`` のいずれかが無い、または ``im_poles``
            が整数化できない場合。
    """
    poles = fixed_required_int(parsed, "im_poles")
    circuit_type = fixed_required_str(parsed, "im_circuit_type").strip()
    connection_type = fixed_required_str(parsed, "im_connection_type").strip()

    primary = _build_primary_branch(combo, bounds)
    excitation = _build_excitation_branch(combo, bounds)
    friction_windage = _build_friction_windage(combo, bounds)
    stray_load = _build_stray_load(combo, bounds)

    secondary_total_r = im_fixed_initial("secondary_resistance", bounds)
    secondary_total_l = im_fixed_initial("secondary_inductance", bounds)

    if combo.secondary_inner is not None:
        inner, outer = _build_secondary_branches_double_cage(
            combo=combo,
            bounds=bounds,
            total_resistance=secondary_total_r,
            total_inductance=secondary_total_l,
            inner_model=combo.secondary_inner,
        )
        return ImLoadedData(
            name=im_name,
            poles=poles,
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE.value,
            connection_type=connection_type,
            circuit_type=circuit_type,
            nameplate=nameplate,
            primary=primary,
            excitation=excitation,
            secondary=None,
            secondary_inner=inner,
            secondary_outer=outer,
            friction_windage=friction_windage,
            stray_load=stray_load,
        )

    secondary = _build_secondary_branch_single_cage(
        combo=combo,
        bounds=bounds,
        total_resistance=secondary_total_r,
        total_inductance=secondary_total_l,
    )
    return ImLoadedData(
        name=im_name,
        poles=poles,
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE.value,
        connection_type=connection_type,
        circuit_type=circuit_type,
        nameplate=nameplate,
        primary=primary,
        excitation=excitation,
        secondary=secondary,
        secondary_inner=None,
        secondary_outer=None,
        friction_windage=friction_windage,
        stray_load=stray_load,
    )
