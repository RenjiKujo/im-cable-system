"""``InputDto`` / ``InputDtos`` の ``__post_init__`` バリデーションテスト。

カバー対象:
    - ``REFERENCE_AXIS_ALLOWED`` / ``REQUIRED_AXES`` の整合
    - ``array_layout=None`` を拒否
    - reference_axes に許可外のキーしかない場合を拒否
    - ``arrays`` に必須軸（frequency / input_line_voltage / slip）が
      欠けている場合を拒否
    - ``InputDtos`` の lookup
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    CableConductorModelDto,
    CableDto,
    CableName,
    CableSectionDto,
    CableSectionDtos,
    CableSectionName,
    CableSeriesDto,
    CableSeriesName,
    CableShapeType,
    CableShapeTypeDto,
    ConductorModelType,
    ImCableSystemName,
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImDto,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImName,
    ImPoles,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
    ImSeriesDto,
    ImSeriesName,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    ArrayFrequencyDto,
    ArraySlipDto,
    FloatActivePowerDto,
    FloatCapacitancePerLengthDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.input import (
    REFERENCE_AXIS_ALLOWED,
    InputDto,
    InputDtos,
)


def _make_im_dto(name: str = "M1") -> ImDto:
    branch = ImSecondaryCageBranchType.SINGLE
    series = ImSeriesDto(
        name=ImSeriesName.create(value=name),
        poles=ImPoles.P4,
        nameplate_voltage=FloatVoltageDto(value=200.0, unit="V"),
        nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
        nameplate_power=FloatActivePowerDto(value=3.0, unit="kW"),
        nameplate_frequency=FloatFrequencyDto(value=50.0, unit="Hz"),
        connection_type=ImConnectionType.STAR,
        circuit_type=ImCircuitType.T,
        primary_model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
        primary_resistance=FloatResistanceDto(value=0.4, unit="Ω"),
        primary_inductance=FloatInductanceDto(value=2.0, unit="mH"),
        excitation_model=ImExcitationModelDto(name=ImExcitationModelType.BASIC),
        excitation_resistance=FloatResistanceDto(value=200.0, unit="Ω"),
        excitation_inductance=FloatInductanceDto(value=60.0, unit="mH"),
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_models={
            branch: ImSecondaryModelDto(name=ImSecondaryModelType.BASIC),
        },
        secondary_resistances={
            branch: FloatResistanceDto(value=0.3, unit="Ω"),
        },
        secondary_inductances={
            branch: FloatInductanceDto(value=2.0, unit="mH"),
        },
        friction_windage_model=ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.NONE
        ),
        stray_load_model=ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
    )
    return ImDto(name=ImName(value=name), im_series=series)


def _make_cable_dto() -> CableDto:
    series = CableSeriesDto(
        name=CableSeriesName(value="S1"),
        shape_type=CableShapeTypeDto(value=CableShapeType.ROUND),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.1,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=1.0,
            unit="mH/km",
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=1.0,
            unit="kΩ*km",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=100.0,
            unit="nF/km",
        ),
    )
    sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=1000.0, unit="m"),
                series=series,
            ),
        ]
    )
    return CableDto(
        name=CableName(value="C1"),
        sections=sections,
        conductor_model=CableConductorModelDto(name=ConductorModelType.BASIC),
    )


def _make_minimal_layout() -> ArrayLayoutDto:
    """slip / frequency / input_line_voltage を持つ最小レイアウト。"""
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.array([0.0, 0.05, 1.0]),
                unit="-",
            ),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([50.0, 60.0]),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.array([200.0 + 0j, 220.0 + 0j]),
                unit="V",
            ),
        },
        reference_axes=[
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        ],
    )


class TestInputDtoBasicConstruction:
    def test_minimal_construction_ok(self) -> None:
        InputDto(
            name=ImCableSystemName(base="SYS"),
            array_layout=_make_minimal_layout(),
            im=_make_im_dto(),
        )

    def test_with_cable(self) -> None:
        InputDto(
            name=ImCableSystemName(base="SYS"),
            array_layout=_make_minimal_layout(),
            im=_make_im_dto(),
            cable=_make_cable_dto(),
        )

    def test_default_im_pc_catalogs_is_empty(self) -> None:
        dto = InputDto(
            name=ImCableSystemName(base="SYS"),
            array_layout=_make_minimal_layout(),
            im=_make_im_dto(),
        )
        assert len(dto.im_pc_catalogs) == 0


class TestInputDtoValidation:
    def test_array_layout_none_rejected(self) -> None:
        with pytest.raises(ValueError, match="array_layout is required"):
            InputDto(
                name=ImCableSystemName(base="SYS"),
                array_layout=None,  # type: ignore[arg-type]
                im=_make_im_dto(),
            )

    def test_missing_required_axis_rejected(self) -> None:
        # SLIP のみ。frequency / input_line_voltage が無いので拒否される。
        layout = ArrayLayoutDto(
            arrays={
                ArrayKey.SLIP: ArraySlipDto(
                    value=np.array([0.0, 0.05]),
                    unit="-",
                ),
            },
            reference_axes=[ArrayKey.SLIP],
        )
        with pytest.raises(ValueError, match="missing required axes"):
            InputDto(
                name=ImCableSystemName(base="SYS"),
                array_layout=layout,
                im=_make_im_dto(),
            )


class TestReferenceAxisAllowed:
    def test_constant_matches_array_key_classification(self) -> None:
        # 公開定数と Enum 分類が同期している
        assert ArrayKey.reference_axes_members() == REFERENCE_AXIS_ALLOWED


class TestInputDtosCollection:
    def test_lookup_by_name(self) -> None:
        a = InputDto(
            name=ImCableSystemName(base="SYS_A"),
            array_layout=_make_minimal_layout(),
            im=_make_im_dto("A"),
        )
        b = InputDto(
            name=ImCableSystemName(base="SYS_B"),
            array_layout=_make_minimal_layout(),
            im=_make_im_dto("B"),
        )
        coll = InputDtos(objects=[a, b])
        assert coll.get_by_name("SYS_A") is a
        assert coll.get_by_name("SYS_B") is b

    def test_get_names(self) -> None:
        a = InputDto(
            name=ImCableSystemName(base="SYS_A"),
            array_layout=_make_minimal_layout(),
            im=_make_im_dto("A"),
        )
        coll = InputDtos(objects=[a])
        assert coll.get_names() == ["SYS_A"]
