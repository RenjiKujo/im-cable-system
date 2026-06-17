"""``predicate.im`` の単体テスト。

- ``is_delta`` / ``is_star``: ``ImDto`` の ``connection_type`` を見るだけの
  1 行述語なので、両結線・両関数の真偽を網羅する。
- ``has_current_dependent_immittance_model``: 一次・励磁・二次の
  いずれかが電流依存型のとき True を返すことを確認する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.domain.predicate import (
    has_current_dependent_immittance_model,
    is_delta,
    is_star,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImDto,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImName,
    ImPoles,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
    ImSeriesDto,
    ImSeriesName,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)


def _make_params(names: list[str]) -> FloatParamDtos | None:
    """指定の名前集合に対するダミー params を組み立てる。

    BASIC モデル等で空の場合は None を返す（DTO バリデーションが
    ``params is None`` を要求するため）。
    """
    if not names:
        return None
    return FloatParamDtos(
        objects=[FloatParamDto(name=n, value=0.1) for n in names]
    )


def _params_for_primary_model_type(
    model_type: ImPrimaryModelType,
) -> FloatParamDtos | None:
    if model_type == ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1:
        return _make_params(
            ["alpha_primary_leakage_x", "beta_primary_leakage_x"]
        )
    return None


def _params_for_excitation_model_type(
    model_type: ImExcitationModelType,
) -> FloatParamDtos | None:
    if model_type == ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1:
        return _make_params(
            ["alpha_excitation_r", "alpha_excitation_x", "beta_excitation_x"]
        )
    return None


def _params_for_secondary_model_type(
    model_type: ImSecondaryModelType,
) -> FloatParamDtos | None:
    if model_type == ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1:
        return _make_params(
            [
                "alpha_secondary_r",
                "beta_secondary_r",
                "alpha_secondary_x",
                "beta_secondary_x",
            ]
        )
    if (
        model_type
        == ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1
    ):
        return _make_params(
            ["alpha_secondary_leakage_x", "beta_secondary_leakage_x"]
        )
    return None


def _make_im_series(
    *,
    name: str,
    connection_type: ImConnectionType,
    primary_model_type: ImPrimaryModelType = ImPrimaryModelType.BASIC,
    excitation_model_type: ImExcitationModelType = ImExcitationModelType.BASIC,
    secondary_model_types: (
        dict[ImSecondaryCageBranchType, ImSecondaryModelType] | None
    ) = None,
    cage_multiplicity: ImCageMultiplicityType = (
        ImCageMultiplicityType.SINGLE_CAGE
    ),
) -> ImSeriesDto:
    """指定のモデル構成を持つ ``ImSeriesDto`` を最小構成で組み立てる。

    ``secondary_model_types`` を指定しなかった場合は、SINGLE_CAGE 用の
    ``{SINGLE: BASIC}`` を既定値として使う。CURRENT_DEPENDENT_* モデルの
    ``params`` は本ヘルパが必要分を自動で埋める。
    """
    if secondary_model_types is None:
        secondary_model_types = {
            ImSecondaryCageBranchType.SINGLE: ImSecondaryModelType.BASIC,
        }
    secondary_models = {
        branch: ImSecondaryModelDto(
            name=model_type,
            params=_params_for_secondary_model_type(model_type),
        )
        for branch, model_type in secondary_model_types.items()
    }
    secondary_resistances = {
        branch: FloatResistanceDto(value=0.2, unit="Ω")
        for branch in secondary_model_types
    }
    secondary_inductances = {
        branch: FloatInductanceDto(value=0.002, unit="H")
        for branch in secondary_model_types
    }
    return ImSeriesDto(
        name=ImSeriesName.create(value=name),
        poles=ImPoles.P4,
        nameplate_voltage=FloatVoltageDto(value=200.0, unit="V"),
        nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
        nameplate_power=FloatActivePowerDto(value=2000.0, unit="W"),
        nameplate_frequency=FloatFrequencyDto(value=50.0, unit="Hz"),
        connection_type=connection_type,
        circuit_type=ImCircuitType.L,
        primary_model=ImPrimaryModelDto(
            name=primary_model_type,
            params=_params_for_primary_model_type(primary_model_type),
        ),
        primary_resistance=FloatResistanceDto(value=0.1, unit="Ω"),
        primary_inductance=FloatInductanceDto(value=0.001, unit="H"),
        excitation_model=ImExcitationModelDto(
            name=excitation_model_type,
            params=_params_for_excitation_model_type(excitation_model_type),
        ),
        excitation_resistance=FloatResistanceDto(value=100.0, unit="Ω"),
        excitation_inductance=FloatInductanceDto(value=0.01, unit="H"),
        cage_multiplicity=cage_multiplicity,
        secondary_models=secondary_models,
        secondary_resistances=secondary_resistances,
        secondary_inductances=secondary_inductances,
    )


def _make_im_dto(connection_type: ImConnectionType) -> ImDto:
    return ImDto(
        name=ImName(value="TEST_IM"),
        im_series=_make_im_series(
            name="SERIES", connection_type=connection_type
        ),
    )


def _make_im_dto_with_models(
    *,
    primary_model_type: ImPrimaryModelType = ImPrimaryModelType.BASIC,
    excitation_model_type: ImExcitationModelType = ImExcitationModelType.BASIC,
    secondary_model_types: (
        dict[ImSecondaryCageBranchType, ImSecondaryModelType] | None
    ) = None,
    cage_multiplicity: ImCageMultiplicityType = (
        ImCageMultiplicityType.SINGLE_CAGE
    ),
) -> ImDto:
    return ImDto(
        name=ImName(value="TEST_IM"),
        im_series=_make_im_series(
            name="SERIES",
            connection_type=ImConnectionType.DELTA,
            primary_model_type=primary_model_type,
            excitation_model_type=excitation_model_type,
            secondary_model_types=secondary_model_types,
            cage_multiplicity=cage_multiplicity,
        ),
    )


class TestIsDelta:
    """``is_delta`` の真偽。"""

    @pytest.mark.parametrize(
        "connection_type, expected",
        [
            (ImConnectionType.DELTA, True),
            (ImConnectionType.STAR, False),
        ],
    )
    def test_returns_true_only_for_delta(
        self, connection_type: ImConnectionType, expected: bool
    ) -> None:
        assert is_delta(im_dto=_make_im_dto(connection_type)) is expected


class TestIsStar:
    """``is_star`` の真偽。"""

    @pytest.mark.parametrize(
        "connection_type, expected",
        [
            (ImConnectionType.STAR, True),
            (ImConnectionType.DELTA, False),
        ],
    )
    def test_returns_true_only_for_star(
        self, connection_type: ImConnectionType, expected: bool
    ) -> None:
        assert is_star(im_dto=_make_im_dto(connection_type)) is expected


class TestDeltaStarAreMutuallyExclusive:
    """同じ DTO で ``is_delta`` と ``is_star`` の片方しか真にならないこと。"""

    @pytest.mark.parametrize(
        "connection_type",
        [ImConnectionType.DELTA, ImConnectionType.STAR],
    )
    def test_only_one_of_delta_star_is_true(
        self, connection_type: ImConnectionType
    ) -> None:
        im = _make_im_dto(connection_type)
        assert is_delta(im_dto=im) != is_star(im_dto=im)


class TestHasCurrentDependentImmittanceModel:
    """``has_current_dependent_immittance_model`` の真偽。"""

    def test_returns_false_when_all_models_are_basic(self) -> None:
        im = _make_im_dto_with_models()
        assert has_current_dependent_immittance_model(im_dto=im) is False

    def test_returns_true_when_primary_is_current_dependent(self) -> None:
        im = _make_im_dto_with_models(
            primary_model_type=(
                ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1
            ),
        )
        assert has_current_dependent_immittance_model(im_dto=im) is True

    def test_returns_true_when_excitation_is_current_dependent(self) -> None:
        im = _make_im_dto_with_models(
            excitation_model_type=(
                ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1
            ),
        )
        assert has_current_dependent_immittance_model(im_dto=im) is True

    def test_returns_true_when_single_secondary_is_current_dependent(
        self,
    ) -> None:
        im = _make_im_dto_with_models(
            secondary_model_types={
                ImSecondaryCageBranchType.SINGLE: (
                    ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1
                ),
            },
        )
        assert has_current_dependent_immittance_model(im_dto=im) is True

    def test_returns_true_when_any_double_cage_branch_is_current_dependent(
        self,
    ) -> None:
        """DOUBLE_CAGE のうち 1 ブランチだけ電流依存でも True。"""
        im = _make_im_dto_with_models(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_model_types={
                ImSecondaryCageBranchType.INNER: ImSecondaryModelType.BASIC,
                ImSecondaryCageBranchType.OUTER: (
                    ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1
                ),
            },
        )
        assert has_current_dependent_immittance_model(im_dto=im) is True

    def test_returns_false_when_all_double_cage_branches_are_basic(
        self,
    ) -> None:
        im = _make_im_dto_with_models(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_model_types={
                ImSecondaryCageBranchType.INNER: ImSecondaryModelType.BASIC,
                ImSecondaryCageBranchType.OUTER: ImSecondaryModelType.BASIC,
            },
        )
        assert has_current_dependent_immittance_model(im_dto=im) is False
