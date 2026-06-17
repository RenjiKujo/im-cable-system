"""ITM 層テスト用ヘルパー（小さな ArrayComplex* DTO の生成）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)


def make_complex_voltage(unit: str = "V") -> ArrayComplexVoltageDto:
    return ArrayComplexVoltageDto(
        value=np.array([100.0 + 0j], dtype=np.complex128), unit=unit
    )


def make_complex_current(unit: str = "A") -> ArrayComplexCurrentDto:
    return ArrayComplexCurrentDto(
        value=np.array([1.0 + 0j], dtype=np.complex128), unit=unit
    )


def make_complex_impedance(unit: str = "Ω") -> ArrayComplexImpedanceDto:
    return ArrayComplexImpedanceDto(
        value=np.array([1.0 + 0j], dtype=np.complex128), unit=unit
    )


def make_complex_admittance(unit: str = "S") -> ArrayComplexAdmittanceDto:
    return ArrayComplexAdmittanceDto(
        value=np.array([1.0 + 0j], dtype=np.complex128), unit=unit
    )


def make_complex_power(unit: str = "VA") -> ArrayComplexPowerDto:
    return ArrayComplexPowerDto(
        value=np.array([1.0 + 0j], dtype=np.complex128), unit=unit
    )
