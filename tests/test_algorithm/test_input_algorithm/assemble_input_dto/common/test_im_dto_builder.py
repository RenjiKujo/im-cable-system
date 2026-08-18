"""共通 ``build_im_series_dto`` が、モデル名・係数の不正を
文脈付き ValueError として通知することを確認するテスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.im_dto_builder import (  # noqa: E501
    build_im_series_dto,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImBranchLoadedData,
    ImLoadedData,
    ImLossBranchLoadedData,
    ImNameplateLoadedData,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
)

_NP = ImNameplateLoadedData(
    voltage=400.0,
    voltage_unit="V",
    current=10.0,
    current_unit="A",
    power=5000.0,
    power_unit="W",
    frequency=60.0,
    frequency_unit="Hz",
)


def _basic_branch(model: str = "BASIC") -> ImBranchLoadedData:
    return ImBranchLoadedData(
        model=model,
        model_params={},
        resistance=0.1,
        resistance_unit="Ω",
        inductance=0.001,
        inductance_unit="H",
    )


def _slip_dep_primary_branch(
    *,
    extra: dict[str, float] | None = None,
    drop: set[str] | None = None,
) -> ImBranchLoadedData:
    """SLIP_DEPENDENT_LEAKAGE_SATURATION_V1 の primary ブランチ（パラメータ調整可）。"""
    base: dict[str, float] = {
        "alpha_primary_r": 0.1,
        "alpha_primary_x": 0.2,
        "beta_primary_x": 0.3,
    }
    if drop:
        for key in drop:
            base.pop(key, None)
    if extra:
        base.update(extra)
    return ImBranchLoadedData(
        model="SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
        model_params=base,
        resistance=0.1,
        resistance_unit="Ω",
        inductance=0.001,
        inductance_unit="H",
    )


def _im_loaded(
    *,
    name: str = "im_sample",
    poles: int = 2,
    cage_multiplicity: str = "SINGLE_CAGE",
    connection_type: str = "STAR",
    circuit_type: str = "L",
    primary: ImBranchLoadedData | None = None,
    excitation: ImBranchLoadedData | None = None,
    secondary: ImBranchLoadedData | None = None,
    secondary_inner: ImBranchLoadedData | None = None,
    secondary_outer: ImBranchLoadedData | None = None,
) -> ImLoadedData:
    return ImLoadedData(
        name=name,
        poles=poles,
        cage_multiplicity=cage_multiplicity,
        connection_type=connection_type,
        circuit_type=circuit_type,
        nameplate=_NP,
        primary=primary if primary is not None else _basic_branch(),
        excitation=excitation if excitation is not None else _basic_branch(),
        secondary=secondary if secondary is not None else _basic_branch(),
        secondary_inner=secondary_inner,
        secondary_outer=secondary_outer,
        friction_windage=ImLossBranchLoadedData(model="NONE", model_params={}),
        stray_load=ImLossBranchLoadedData(model="NONE", model_params={}),
    )


class TestImDtoBuilderEnumErrors:
    """モデル名（Enum 変換）が不正なときの文脈付きエラー。"""

    def test_unknown_primary_model_raises_with_series_and_branch(self) -> None:
        im_loaded = _im_loaded(
            name="im_sample",
            primary=_basic_branch(model="NOT_A_MODEL"),
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "'im_sample'" in msg
        assert "primary" in msg
        assert "NOT_A_MODEL" in msg

    def test_unknown_excitation_model_raises_with_series_and_branch(
        self,
    ) -> None:
        im_loaded = _im_loaded(
            excitation=_basic_branch(model="NOT_A_MODEL"),
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "excitation" in msg

    def test_unknown_secondary_model_raises_with_branch_label(self) -> None:
        im_loaded = _im_loaded(
            secondary=_basic_branch(model="NOT_A_MODEL"),
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        assert "secondary" in str(excinfo.value)

    def test_unknown_connection_type_raises_with_context(self) -> None:
        """結線種別の不正もシリーズ名・属性名付きでエラーになる。"""
        im_loaded = _im_loaded(connection_type="NOT_A_CONNECTION")
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "'im_sample'" in msg
        assert "connection_type" in msg
        assert "NOT_A_CONNECTION" in msg

    def test_unknown_circuit_type_raises_with_context(self) -> None:
        """等価回路種別の不正もシリーズ名・属性名付きでエラーになる。"""
        im_loaded = _im_loaded(circuit_type="NOT_A_CIRCUIT")
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "'im_sample'" in msg
        assert "circuit_type" in msg
        assert "NOT_A_CIRCUIT" in msg

    def test_unsupported_poles_raises_with_context(self) -> None:
        """極数の不正はシリーズ名付きでエラーになる。"""
        im_loaded = _im_loaded(poles=999)
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "'im_sample'" in msg
        assert "極数" in msg
        assert "999" in msg

    def test_unknown_cage_multiplicity_raises_with_context(self) -> None:
        """かご段数種別の不正はシリーズ名付きでエラーになる。"""
        im_loaded = _im_loaded(cage_multiplicity="NOT_A_CAGE")
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "'im_sample'" in msg
        assert "cage_multiplicity" in msg
        assert "NOT_A_CAGE" in msg


class TestImDtoBuilderParamErrors:
    """モデル係数が不足・余分なときに、文脈付きで ValueError になる。"""

    def test_missing_primary_param_raises_with_context(self) -> None:
        im_loaded = _im_loaded(
            name="im_sample",
            primary=_slip_dep_primary_branch(drop={"beta_primary_x"}),
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "'im_sample'" in msg
        assert "primary" in msg
        assert "不足" in msg

    def test_extra_primary_param_raises_with_context(self) -> None:
        im_loaded = _im_loaded(
            primary=_slip_dep_primary_branch(extra={"extra_param": 1.0}),
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "primary" in msg
        assert "余分" in msg


class TestImDtoBuilderDoubleCage:
    """DOUBLE_CAGE の二次枝構造を確認する。"""

    def test_double_cage_builds_inner_and_outer_secondary_branches(
        self,
    ) -> None:
        im_loaded = _im_loaded(
            cage_multiplicity="DOUBLE_CAGE",
            secondary=None,
            secondary_inner=_basic_branch(),
            secondary_outer=_basic_branch(),
        )
        dto = build_im_series_dto(im_loaded)
        assert dto.cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE
        assert set(dto.secondary_models) == {
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        }
        assert set(dto.secondary_resistances) == {
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        }
        assert set(dto.secondary_inductances) == {
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        }

    def test_double_cage_missing_inner_raises_with_context(self) -> None:
        im_loaded = _im_loaded(
            cage_multiplicity="DOUBLE_CAGE",
            secondary=None,
            secondary_inner=None,
            secondary_outer=_basic_branch(),
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "二重かご" in msg
        assert "secondary_inner" in msg
        assert "secondary_outer" in msg

    def test_double_cage_missing_outer_raises_with_context(self) -> None:
        im_loaded = _im_loaded(
            cage_multiplicity="DOUBLE_CAGE",
            secondary=None,
            secondary_inner=_basic_branch(),
            secondary_outer=None,
        )
        with pytest.raises(ValueError) as excinfo:
            build_im_series_dto(im_loaded)
        msg = str(excinfo.value)
        assert "二重かご" in msg
        assert "secondary_inner" in msg
        assert "secondary_outer" in msg
