"""``predicate.cable`` の単体テスト。

- ケーブル状態判定 3 関数（完全絶縁・地絡・理想導体）の真偽を、
  典型シリーズ（完全絶縁・地絡・通常）の組合せで確認する。
- ``has_current_dependent_conductor_model``: 導体モデルタイプ別に
  電流依存判定が真偽を返すことを確認する。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.domain.predicate import (
    check_all_conductor_ideal,
    check_all_ground_insulated,
    check_any_ground_shorted,
    has_current_dependent_conductor_model,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    CableDto,
    CableName,
    CableSectionDto,
    CableSectionDtos,
    CableSectionName,
    CableSeriesDto,
    CableSeriesName,
    CableShapeTypeDto,
    ConductorModelType,
    FloatParamDto,
    FloatParamDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)
from tests.test_domain._domain_helpers import (
    TEST_EPS,
    TEST_MAX_MAG,
)

_CONDUCTOR_MODEL = CableConductorModelDto(
    name=ConductorModelType.BASIC, params=None
)


def _make_series(
    *,
    name: str,
    cond_r_per_len: float,
    cond_l_per_len: float,
    gnd_r_len: float,
    gnd_c_per_len: float,
) -> CableSeriesDto:
    return CableSeriesDto(
        name=CableSeriesName(value=name),
        shape_type=CableShapeTypeDto(value="ROUND"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=cond_r_per_len, unit="Ω/m"
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=cond_l_per_len, unit="H/m"
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=gnd_r_len, unit="Ω*m"
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=gnd_c_per_len, unit="F/m"
        ),
    )


_INSULATED = _make_series(
    name="INSULATED",
    cond_r_per_len=0.0,
    cond_l_per_len=0.0,
    gnd_r_len=np.inf,
    gnd_c_per_len=0.0,
)
_SHORTED = _make_series(
    name="SHORTED",
    cond_r_per_len=1e-3,
    cond_l_per_len=1e-3,
    gnd_r_len=0.0,
    gnd_c_per_len=1e-6,
)
_NORMAL = _make_series(
    name="NORMAL",
    cond_r_per_len=1e-2,
    cond_l_per_len=1e-2,
    gnd_r_len=100.0,
    gnd_c_per_len=1e-5,
)


def _make_single_section_cable(series: CableSeriesDto) -> CableDto:
    sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=100.0, unit="m"),
                series=series,
            ),
        ]
    )
    return CableDto(
        name=CableName(value="TEST_CABLE"),
        sections=sections,
        conductor_model=_CONDUCTOR_MODEL,
    )


def _make_multi_section_cable(
    series_list: list[CableSeriesDto],
) -> CableDto:
    sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value=f"S{i}"),
                length=FloatLengthDto(value=10.0 * (i + 1), unit="m"),
                series=series,
            )
            for i, series in enumerate(series_list)
        ]
    )
    return CableDto(
        name=CableName(value="MULTI_CABLE"),
        sections=sections,
        conductor_model=_CONDUCTOR_MODEL,
    )


def _params_for_conductor_model_type(
    model_type: ConductorModelType,
) -> FloatParamDtos | None:
    """導体モデルタイプ別に CURRENT_DEPENDENT 用 params を組み立てる。"""
    if model_type == ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1:
        return FloatParamDtos(
            objects=[
                FloatParamDto(name=n, value=0.1)
                for n in (
                    "alpha_conductor_r",
                    "beta_conductor_r",
                    "alpha_conductor_x",
                    "beta_conductor_x",
                )
            ]
        )
    return None


def _make_cable_with_conductor_model(
    conductor_model_type: ConductorModelType,
) -> CableDto:
    """指定の導体モデルタイプを持つ ``CableDto`` を最小構成で組み立てる。

    CURRENT_DEPENDENT_* モデルの ``params`` は本ヘルパが必要分を自動で埋める。
    """
    sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=100.0, unit="m"),
                series=_NORMAL,
            ),
        ]
    )
    return CableDto(
        name=CableName(value="TEST_CABLE"),
        sections=sections,
        conductor_model=CableConductorModelDto(
            name=conductor_model_type,
            params=_params_for_conductor_model_type(conductor_model_type),
        ),
    )


class TestCheckAllGroundInsulated:
    """``check_all_ground_insulated`` の真偽。"""

    def test_returns_true_when_all_sections_are_insulated(self) -> None:
        cable = _make_single_section_cable(_INSULATED)
        assert (
            check_all_ground_insulated(cable_dto=cable, max_mag=TEST_MAX_MAG)
            is True
        )

    def test_returns_false_when_section_is_normal(self) -> None:
        cable = _make_single_section_cable(_NORMAL)
        assert (
            check_all_ground_insulated(cable_dto=cable, max_mag=TEST_MAX_MAG)
            is False
        )

    def test_returns_false_when_any_section_is_not_insulated(self) -> None:
        """1 セクションでも非絶縁なら False。"""
        cable = _make_multi_section_cable([_INSULATED, _NORMAL])
        assert (
            check_all_ground_insulated(cable_dto=cable, max_mag=TEST_MAX_MAG)
            is False
        )


class TestCheckAnyGroundShorted:
    """``check_any_ground_shorted`` の真偽。"""

    def test_returns_true_when_any_section_is_shorted(self) -> None:
        cable = _make_single_section_cable(_SHORTED)
        assert check_any_ground_shorted(cable_dto=cable, eps=TEST_EPS) is True

    def test_returns_false_when_no_section_is_shorted(self) -> None:
        cable = _make_single_section_cable(_NORMAL)
        assert check_any_ground_shorted(cable_dto=cable, eps=TEST_EPS) is False

    def test_returns_true_when_mixed_sections_include_shorted(self) -> None:
        cable = _make_multi_section_cable([_NORMAL, _SHORTED])
        assert check_any_ground_shorted(cable_dto=cable, eps=TEST_EPS) is True


class TestCheckAllConductorIdeal:
    """``check_all_conductor_ideal`` の真偽。"""

    def test_returns_true_when_all_sections_have_ideal_conductor(self) -> None:
        cable = _make_single_section_cable(_INSULATED)
        assert check_all_conductor_ideal(cable_dto=cable, eps=TEST_EPS) is True

    def test_returns_false_when_section_has_finite_conductor_loss(self) -> None:
        cable = _make_single_section_cable(_NORMAL)
        assert check_all_conductor_ideal(cable_dto=cable, eps=TEST_EPS) is False


class TestMixedSectionScenarios:
    """複数 series が混在する場合の各述語の挙動。"""

    def test_insulated_then_normal_is_not_all_insulated(self) -> None:
        cable = _make_multi_section_cable([_INSULATED, _NORMAL])
        assert (
            check_all_ground_insulated(cable_dto=cable, max_mag=TEST_MAX_MAG)
            is False
        )
        assert check_any_ground_shorted(cable_dto=cable, eps=TEST_EPS) is False
        assert check_all_conductor_ideal(cable_dto=cable, eps=TEST_EPS) is False

    def test_insulated_then_shorted_is_shorted_and_not_insulated(self) -> None:
        cable = _make_multi_section_cable([_INSULATED, _SHORTED])
        assert (
            check_all_ground_insulated(cable_dto=cable, max_mag=TEST_MAX_MAG)
            is False
        )
        assert check_any_ground_shorted(cable_dto=cable, eps=TEST_EPS) is True
        assert check_all_conductor_ideal(cable_dto=cable, eps=TEST_EPS) is False


class TestHasCurrentDependentConductorModel:
    """``has_current_dependent_conductor_model`` の真偽。"""

    def test_returns_false_when_conductor_model_is_basic(self) -> None:
        cable = _make_cable_with_conductor_model(ConductorModelType.BASIC)
        assert has_current_dependent_conductor_model(cable_dto=cable) is False

    def test_returns_true_when_conductor_model_is_current_dependent(
        self,
    ) -> None:
        cable = _make_cable_with_conductor_model(
            ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1
        )
        assert has_current_dependent_conductor_model(cable_dto=cable) is True
