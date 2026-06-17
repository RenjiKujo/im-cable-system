"""Unit conversion short-circuit tests for physical quantity DTOs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayApparentPowerDto,
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
    ArrayCurrentMagnitudeDto,
    ArrayCurvePerUnitDto,
    ArrayEfficiencyDto,
    ArrayFrequencyDto,
    ArrayPowerFactorDto,
    ArrayReactivePowerDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatActivePowerDto,
    FloatApparentPowerDto,
    FloatCapacitanceDto,
    FloatCapacitancePerLengthDto,
    FloatConductanceDto,
    FloatCurrentDto,
    FloatEfficiencyDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatPowerFactorDto,
    FloatReactivePowerDto,
    FloatResistanceDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
    FloatRotationalSpeedDto,
    FloatVoltageDto,
)

DtoFactory = Callable[[], Any]


@pytest.mark.parametrize(
    ("factory", "base_unit"),
    [
        (lambda: ArrayComplexAdmittanceDto(np.array([1.0 + 0.0j]), "S"), "S"),
        (lambda: ArrayComplexImpedanceDto(np.array([1.0 + 0.0j]), "Ω"), "Ω"),
        (lambda: FloatCurrentDto(1.0, "A"), "A"),
        (lambda: ArrayComplexCurrentDto(np.array([1.0 + 0.0j]), "A"), "A"),
        (lambda: ArrayCurrentMagnitudeDto(np.array([1.0]), "A"), "A"),
        (lambda: FloatVoltageDto(1.0, "V"), "V"),
        (lambda: ArrayComplexVoltageDto(np.array([1.0 + 0.0j]), "V"), "V"),
        (lambda: FloatFrequencyDto(1.0, "Hz"), "Hz"),
        (lambda: ArrayFrequencyDto(np.array([1.0]), "Hz"), "Hz"),
        (lambda: FloatEfficiencyDto(1.0, "-"), "-"),
        (lambda: ArrayEfficiencyDto(np.array([1.0]), "-"), "-"),
        (lambda: FloatPowerFactorDto(1.0, "-"), "-"),
        (lambda: ArrayPowerFactorDto(np.array([1.0]), "-"), "-"),
        (lambda: ArraySlipDto(np.array([0.5]), "-"), "-"),
        (lambda: ArrayCurvePerUnitDto(np.array([1.0]), "[-]"), "[-]"),
        (lambda: ArrayTorqueDto(np.array([1.0]), "Nm"), "Nm"),
        (lambda: FloatLengthDto(1.0, "m"), "m"),
        (lambda: FloatResistanceDto(1.0, "Ω"), "Ω"),
        (lambda: FloatConductanceDto(1.0, "S"), "S"),
        (lambda: FloatInductanceDto(1.0, "H"), "H"),
        (lambda: FloatCapacitanceDto(1.0, "F"), "F"),
        (lambda: FloatActivePowerDto(1.0, "W"), "W"),
        (lambda: FloatReactivePowerDto(1.0, "var"), "var"),
        (lambda: FloatApparentPowerDto(1.0, "VA"), "VA"),
        (lambda: ArrayComplexPowerDto(np.array([1.0 + 0.0j]), "VA"), "VA"),
        (lambda: ArrayActivePowerDto(np.array([1.0]), "W"), "W"),
        (lambda: ArrayReactivePowerDto(np.array([1.0]), "var"), "var"),
        (lambda: ArrayApparentPowerDto(np.array([1.0]), "VA"), "VA"),
        (lambda: FloatResistancePerLengthDto(1.0, "Ω/m"), "Ω/m"),
        (lambda: FloatResistanceLengthDto(1.0, "Ω*m"), "Ω*m"),
        (lambda: FloatInductancePerLengthDto(1.0, "H/m"), "H/m"),
        (lambda: FloatCapacitancePerLengthDto(1.0, "F/m"), "F/m"),
        (lambda: FloatRotationalSpeedDto(1.0, "rad/s"), "rad/s"),
        (lambda: ArrayRotationalSpeedDto(np.array([1.0]), "rad/s"), "rad/s"),
    ],
)
def test_base_and_same_unit_conversion_return_self(
    factory: DtoFactory, base_unit: str
) -> None:
    """Base-unit and same-unit conversions reuse the original DTO."""
    dto = factory()

    assert dto.get_unit() == base_unit
    assert dto.to_base_unit() is dto
    assert dto.convert_to_unit(base_unit) is dto
