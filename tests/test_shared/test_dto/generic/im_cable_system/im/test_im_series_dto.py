"""``ImSeriesDto`` の secondary dict キー検証テスト。

``__post_init__`` で
    - ``cage_multiplicity == SINGLE_CAGE`` のとき secondary 系の dict
      キー集合 = {SINGLE}
    - ``cage_multiplicity == DOUBLE_CAGE`` のとき secondary 系の dict
      キー集合 = {INNER, OUTER}
を全 3 系 (``secondary_models`` / ``secondary_resistances`` /
``secondary_inductances``) に対して厳密検証する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImExcitationModelDto,
    ImExcitationModelType,
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


def _basic_primary() -> ImPrimaryModelDto:
    return ImPrimaryModelDto(name=ImPrimaryModelType.BASIC)


def _basic_excitation() -> ImExcitationModelDto:
    return ImExcitationModelDto(name=ImExcitationModelType.BASIC)


def _basic_secondary() -> ImSecondaryModelDto:
    return ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)


def _make_series_kwargs(
    cage_multiplicity: ImCageMultiplicityType,
    secondary_models: dict[ImSecondaryCageBranchType, ImSecondaryModelDto],
    secondary_resistances: dict[ImSecondaryCageBranchType, FloatResistanceDto],
    secondary_inductances: dict[ImSecondaryCageBranchType, FloatInductanceDto],
) -> dict[str, object]:
    return {
        "name": ImSeriesName(value="SERIES_A"),
        "poles": ImPoles.P4,
        "nameplate_voltage": FloatVoltageDto(value=400.0, unit="V"),
        "nameplate_current": FloatCurrentDto(value=10.0, unit="A"),
        "nameplate_power": FloatActivePowerDto(value=5.0, unit="kW"),
        "nameplate_frequency": FloatFrequencyDto(value=60.0, unit="Hz"),
        "connection_type": ImConnectionType.STAR,
        "circuit_type": ImCircuitType.T,
        "primary_model": _basic_primary(),
        "primary_resistance": FloatResistanceDto(value=0.5, unit="Ω"),
        "primary_inductance": FloatInductanceDto(value=1.0, unit="mH"),
        "excitation_model": _basic_excitation(),
        "excitation_resistance": FloatResistanceDto(value=10.0, unit="Ω"),
        "excitation_inductance": FloatInductanceDto(value=10.0, unit="mH"),
        "cage_multiplicity": cage_multiplicity,
        "secondary_models": secondary_models,
        "secondary_resistances": secondary_resistances,
        "secondary_inductances": secondary_inductances,
    }


class TestImSeriesDtoSingleCage:
    def test_valid_single_cage(self) -> None:
        kwargs = _make_series_kwargs(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.SINGLE: _basic_secondary(),
            },
            secondary_resistances={
                ImSecondaryCageBranchType.SINGLE: FloatResistanceDto(
                    value=0.3, unit="Ω"
                ),
            },
            secondary_inductances={
                ImSecondaryCageBranchType.SINGLE: FloatInductanceDto(
                    value=0.5, unit="mH"
                ),
            },
        )
        ImSeriesDto(**kwargs)  # type: ignore[arg-type]

    def test_single_cage_with_double_keys_rejected(self) -> None:
        kwargs = _make_series_kwargs(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.INNER: _basic_secondary(),
                ImSecondaryCageBranchType.OUTER: _basic_secondary(),
            },
            secondary_resistances={
                ImSecondaryCageBranchType.SINGLE: FloatResistanceDto(
                    value=0.3, unit="Ω"
                ),
            },
            secondary_inductances={
                ImSecondaryCageBranchType.SINGLE: FloatInductanceDto(
                    value=0.5, unit="mH"
                ),
            },
        )
        with pytest.raises(ValueError, match="secondary_models keys"):
            ImSeriesDto(**kwargs)  # type: ignore[arg-type]

    def test_single_cage_with_extra_branch_rejected(self) -> None:
        kwargs = _make_series_kwargs(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.SINGLE: _basic_secondary(),
                ImSecondaryCageBranchType.INNER: _basic_secondary(),
            },
            secondary_resistances={
                ImSecondaryCageBranchType.SINGLE: FloatResistanceDto(
                    value=0.3, unit="Ω"
                ),
            },
            secondary_inductances={
                ImSecondaryCageBranchType.SINGLE: FloatInductanceDto(
                    value=0.5, unit="mH"
                ),
            },
        )
        with pytest.raises(ValueError, match="secondary_models keys"):
            ImSeriesDto(**kwargs)  # type: ignore[arg-type]


class TestImSeriesDtoDoubleCage:
    def test_valid_double_cage(self) -> None:
        kwargs = _make_series_kwargs(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.INNER: _basic_secondary(),
                ImSecondaryCageBranchType.OUTER: _basic_secondary(),
            },
            secondary_resistances={
                ImSecondaryCageBranchType.INNER: FloatResistanceDto(
                    value=0.2, unit="Ω"
                ),
                ImSecondaryCageBranchType.OUTER: FloatResistanceDto(
                    value=0.4, unit="Ω"
                ),
            },
            secondary_inductances={
                ImSecondaryCageBranchType.INNER: FloatInductanceDto(
                    value=0.3, unit="mH"
                ),
                ImSecondaryCageBranchType.OUTER: FloatInductanceDto(
                    value=0.6, unit="mH"
                ),
            },
        )
        ImSeriesDto(**kwargs)  # type: ignore[arg-type]

    def test_double_cage_with_single_key_rejected(self) -> None:
        kwargs = _make_series_kwargs(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.SINGLE: _basic_secondary(),
            },
            secondary_resistances={
                ImSecondaryCageBranchType.INNER: FloatResistanceDto(
                    value=0.2, unit="Ω"
                ),
                ImSecondaryCageBranchType.OUTER: FloatResistanceDto(
                    value=0.4, unit="Ω"
                ),
            },
            secondary_inductances={
                ImSecondaryCageBranchType.INNER: FloatInductanceDto(
                    value=0.3, unit="mH"
                ),
                ImSecondaryCageBranchType.OUTER: FloatInductanceDto(
                    value=0.6, unit="mH"
                ),
            },
        )
        with pytest.raises(ValueError, match="secondary_models keys"):
            ImSeriesDto(**kwargs)  # type: ignore[arg-type]

    def test_double_cage_missing_outer_rejected(self) -> None:
        kwargs = _make_series_kwargs(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.INNER: _basic_secondary(),
                ImSecondaryCageBranchType.OUTER: _basic_secondary(),
            },
            secondary_resistances={
                ImSecondaryCageBranchType.INNER: FloatResistanceDto(
                    value=0.2, unit="Ω"
                ),
            },
            secondary_inductances={
                ImSecondaryCageBranchType.INNER: FloatInductanceDto(
                    value=0.3, unit="mH"
                ),
                ImSecondaryCageBranchType.OUTER: FloatInductanceDto(
                    value=0.6, unit="mH"
                ),
            },
        )
        with pytest.raises(ValueError, match="secondary_resistances keys"):
            ImSeriesDto(**kwargs)  # type: ignore[arg-type]
