"""``loader._build_system_name`` / ``_build_im_name`` の単体テスト。

内部実装（非公開）の単体テスト。8 インデックス（rev.2 で friction_windage /
stray_load の 2 軸が増えた）の並び順を直接検証する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    EstimateParamsModelCombo,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.loader import (  # noqa: E501
    _build_im_name,
    _build_system_name,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (
    CableConductorModelName,
    ImExcitationModelName,
    ImFrictionWindageModelName,
    ImPrimaryModelName,
    ImSecondaryModelName,
    ImStrayLoadModelName,
)


def _make_combo(**overrides: object) -> EstimateParamsModelCombo:
    base: dict[str, object] = {
        "primary": ImPrimaryModelName("BASIC"),
        "excitation": ImExcitationModelName("BASIC"),
        "secondary_inner": None,
        "secondary_outer": ImSecondaryModelName("BASIC"),
        "cable_conductor": CableConductorModelName("BASIC"),
        "friction_windage": ImFrictionWindageModelName("CONSTANT_V1"),
        "stray_load": ImStrayLoadModelName("CURRENT_DEPENDENT_QUADRATIC_V1"),
        "primary_index": 1,
        "excitation_index": 2,
        "secondary_single_index": 3,
        "secondary_double_outer_index": 4,
        "secondary_double_inner_index": 5,
        "cable_conductor_index": 6,
        "friction_windage_index": 7,
        "stray_load_index": 8,
    }
    base.update(overrides)
    return EstimateParamsModelCombo(**base)  # type: ignore[arg-type]


def test_build_system_name_has_eight_indices_in_order() -> None:
    combo = _make_combo()
    name = _build_system_name(perf_curve_name="Perf", combo=combo)
    assert name == "Perf_1_2_3_4_5_7_8_6"


def test_build_im_name_has_five_plus_two_indices_in_order() -> None:
    combo = _make_combo()
    name = _build_im_name(combo)
    assert name == "IM_1_2_3_4_5_7_8"


def test_build_system_name_none_axes_fallback_to_index_one() -> None:
    """fw/sl に ``NONE`` のみを書いた TSV では index=1。"""
    combo = _make_combo(
        friction_windage=ImFrictionWindageModelName("NONE"),
        stray_load=ImStrayLoadModelName("NONE"),
        friction_windage_index=1,
        stray_load_index=1,
    )
    name = _build_system_name(perf_curve_name="Perf", combo=combo)
    assert name == "Perf_1_2_3_4_5_1_1_6"
