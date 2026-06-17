"""Execute アルゴリズムテスト用 InputDto 組み立て（二重かご）。

二重かご（DOUBLE_CAGE）向け InputDto を **27パターン**
（IM 3種 × ケーブル 3種 × ArrayLayout 3種）生成する。
``test_execute_algorithm`` 配下のテストからのみ import する。

- **IM（3種）**: すべて BASIC / SLIP_DEPENDENT / CURRENT_DEPENDENT
- **ケーブル（3種）**: なし / FREQUENCY_DEPENDENT / CURRENT_DEPENDENT
- **ArrayLayout（3種）**: 単一かごの ``make_array_layout_dtos`` と同様の 0/1/2
  （二次電流キーのみ DOUBLE_CAGE 用に差し替え）
"""

from __future__ import annotations

import numpy as np

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
    CableShapeTypeDto,
    ConductorModelType,
    FloatParamDto,
    FloatParamDtos,
    ImCableSystemName,
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
    ArrayComplexCurrentDto,
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
    InputDto,
    InputDtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.im_series_list import (
    get_im_series_by_name,
)

_SI_CABLE_COND_R_OHM_PER_M: float = 3.280839895013123e-06
_SI_CABLE_COND_L_H_PER_M: float = 3.280839895013123e-06
_SI_CABLE_GROUND_RLEN_OHM_M: float = 3048.0
_SI_CABLE_GROUND_C_F_PER_M: float = 3.2808398950131233e-09


def _create_double_cage_im_series_dto(
    name: str,
    connection_type: str,
    circuit_type: str,
    primary_model: ImPrimaryModelDto,
    excitation_model: ImExcitationModelDto,
    secondary_model_inner: ImSecondaryModelDto,
    secondary_model_outer: ImSecondaryModelDto,
) -> ImSeriesDto:
    """二重かごの ImSeriesDto を作成する。

    Args:
      name: シリーズ名。
      connection_type: 結線方式（"STAR" or "DELTA"）。
      circuit_type: 回路タイプ（"L" or "T"）。
      primary_model: 一次回路モデル。
      excitation_model: 励磁回路モデル。
      secondary_model_inner: 二次 INNER 枝のモデル。
      secondary_model_outer: 二次 OUTER 枝のモデル。

    Returns:
      ImSeriesDto: 二重かご IM シリーズ DTO。
    """
    inner = ImSecondaryCageBranchType.INNER
    outer = ImSecondaryCageBranchType.OUTER
    r2_inner = FloatResistanceDto(value=0.3398, unit="Ω")
    r2_outer = FloatResistanceDto(value=0.42, unit="Ω")
    l2_inner = FloatInductanceDto(value=0.001785650652, unit="H")
    l2_outer = FloatInductanceDto(value=0.00215, unit="H")
    return ImSeriesDto(
        name=ImSeriesName.create(value=name),
        poles=ImPoles.P4,
        nameplate_voltage=FloatVoltageDto(value=200.0, unit="V"),
        nameplate_current=FloatCurrentDto(value=13.86, unit="A"),
        nameplate_power=FloatActivePowerDto(value=3711.0, unit="W"),
        nameplate_frequency=FloatFrequencyDto(value=50.0, unit="Hz"),
        connection_type=ImConnectionType(connection_type),
        circuit_type=ImCircuitType(circuit_type),
        primary_model=primary_model,
        primary_resistance=FloatResistanceDto(value=0.4, unit="Ω"),
        primary_inductance=FloatInductanceDto(value=0.001785650652, unit="H"),
        excitation_model=excitation_model,
        excitation_resistance=FloatResistanceDto(value=235.2941176, unit="Ω"),
        excitation_inductance=FloatInductanceDto(value=0.06709536625, unit="H"),
        cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
        secondary_models={
            inner: secondary_model_inner,
            outer: secondary_model_outer,
        },
        secondary_resistances={
            inner: r2_inner,
            outer: r2_outer,
        },
        secondary_inductances={
            inner: l2_inner,
            outer: l2_outer,
        },
    )


def make_double_cage_im_series_dtos() -> list[ImSeriesDto]:
    """二重かご向けの ImSeriesDto リスト（3種）を生成する。"""
    # 1) すべて BASIC
    basic = _create_double_cage_im_series_dto(
        name="DOUBLE_BASIC",
        connection_type="STAR",
        circuit_type="L",
        primary_model=ImPrimaryModelDto(
            name=ImPrimaryModelType.BASIC, params=None
        ),
        excitation_model=ImExcitationModelDto(
            name=ImExcitationModelType.BASIC, params=None
        ),
        secondary_model_inner=ImSecondaryModelDto(
            name=ImSecondaryModelType.BASIC, params=None
        ),
        secondary_model_outer=ImSecondaryModelDto(
            name=ImSecondaryModelType.BASIC, params=None
        ),
    )

    # 2) すべて SLIP_DEPENDENT
    slip = _create_double_cage_im_series_dto(
        name="DOUBLE_SLIP_DEP",
        connection_type="DELTA",
        circuit_type="T",
        primary_model=ImPrimaryModelDto(
            name=ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_primary_r", value=0.05),
                    FloatParamDto(name="alpha_primary_x", value=0.15),
                    FloatParamDto(name="beta_primary_x", value=0.25),
                ]
            ),
        ),
        excitation_model=ImExcitationModelDto(
            name=ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_excitation_r", value=0.1),
                    FloatParamDto(name="alpha_excitation_x", value=0.2),
                    FloatParamDto(name="beta_excitation_x", value=0.3),
                ]
            ),
        ),
        secondary_model_inner=ImSecondaryModelDto(
            name=ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_secondary_r", value=0.4),
                    FloatParamDto(name="alpha_secondary_x", value=0.3),
                    FloatParamDto(name="beta_secondary_r", value=0.2),
                    FloatParamDto(name="beta_secondary_x", value=0.1),
                ]
            ),
        ),
        secondary_model_outer=ImSecondaryModelDto(
            name=ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_secondary_r", value=0.35),
                    FloatParamDto(name="alpha_secondary_x", value=0.28),
                    FloatParamDto(name="beta_secondary_r", value=0.18),
                    FloatParamDto(name="beta_secondary_x", value=0.09),
                ]
            ),
        ),
    )

    # 3) すべて CURRENT_DEPENDENT
    current = _create_double_cage_im_series_dto(
        name="DOUBLE_CURRENT_DEP",
        connection_type="DELTA",
        circuit_type="L",
        primary_model=ImPrimaryModelDto(
            name=ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_primary_leakage_x", value=0.15),
                    FloatParamDto(name="beta_primary_leakage_x", value=0.25),
                ]
            ),
        ),
        excitation_model=ImExcitationModelDto(
            name=ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_excitation_r", value=0.1),
                    FloatParamDto(name="alpha_excitation_x", value=0.2),
                    FloatParamDto(name="beta_excitation_x", value=0.3),
                ]
            ),
        ),
        secondary_model_inner=ImSecondaryModelDto(
            name=ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_secondary_r", value=0.4),
                    FloatParamDto(name="beta_secondary_r", value=0.2),
                    FloatParamDto(name="alpha_secondary_x", value=0.3),
                    FloatParamDto(name="beta_secondary_x", value=0.1),
                ]
            ),
        ),
        secondary_model_outer=ImSecondaryModelDto(
            name=ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_secondary_r", value=0.36),
                    FloatParamDto(name="beta_secondary_r", value=0.18),
                    FloatParamDto(name="alpha_secondary_x", value=0.27),
                    FloatParamDto(name="beta_secondary_x", value=0.09),
                ]
            ),
        ),
    )

    return [basic, slip, current]


def make_double_cage_im_dtos() -> tuple[ImDto, ...]:
    """二重かご向けの ImDto（3個）を生成する。"""
    series_dtos = make_double_cage_im_series_dtos()
    names = ["DOUBLE_BASIC", "DOUBLE_SLIP_DEP", "DOUBLE_CURRENT_DEP"]
    im_dtos: list[ImDto] = []
    for series_name in names:
        series = get_im_series_by_name(
            series_dtos,
            ImSeriesName.create(value=series_name),
        )
        if series is None:
            raise ValueError(f"ImSeriesDto not found: {series_name}")
        im_dtos.append(
            ImDto(
                name=ImName(value=series_name),
                im_series=series,
            )
        )
    return tuple(im_dtos)


def _make_main_real_cable_series() -> CableSeriesDto:
    """MAIN_REAL 相当の CableSeriesDto（現実ケーブル）を最小構成で返す。"""
    return CableSeriesDto(
        name=CableSeriesName(value="MAIN_REAL"),
        shape_type=CableShapeTypeDto(value="ROUND"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=_SI_CABLE_COND_R_OHM_PER_M,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=_SI_CABLE_COND_L_H_PER_M,
            unit="H/m",
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=_SI_CABLE_GROUND_RLEN_OHM_M,
            unit="Ω*m",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=_SI_CABLE_GROUND_C_F_PER_M,
            unit="F/m",
        ),
    )


def make_cable_dtos() -> tuple[CableDto | None, ...]:
    """二重かご向けのケーブル DTO（3種 + None）を返す。"""
    main_series = _make_main_real_cable_series()
    main_section = CableSectionDto(
        name=CableSectionName(value="MAIN"),
        length=FloatLengthDto(value=5000.0, unit="ft"),
        series=main_series,
    )
    sections = CableSectionDtos(objects=[main_section])

    cable_none = None

    cable_main_freq_dep = CableDto(
        name=CableName(value="double_cable_main_freq_dep"),
        sections=sections,
        conductor_model=CableConductorModelDto(
            name=ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_conductor_r", value=0.3),
                    FloatParamDto(name="beta_conductor_r", value=0.2),
                    FloatParamDto(name="alpha_conductor_x", value=0.25),
                    FloatParamDto(name="beta_conductor_x", value=0.15),
                ]
            ),
        ),
    )

    cable_main_current_dep = CableDto(
        name=CableName(value="DOUBLE_MAIN_CURRENT_DEP"),
        sections=sections,
        conductor_model=CableConductorModelDto(
            name=ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_conductor_r", value=0.3),
                    FloatParamDto(name="beta_conductor_r", value=0.2),
                    FloatParamDto(name="alpha_conductor_x", value=0.25),
                    FloatParamDto(name="beta_conductor_x", value=0.15),
                ]
            ),
        ),
    )

    return (cable_none, cable_main_freq_dep, cable_main_current_dep)


def make_array_layout_dtos() -> tuple[ArrayLayoutDto, ...]:  # noqa: PLR0915
    """二重かご向けの ArrayLayoutDto を 3 種類生成する。

    単一かごの :func:`input_single_im_cable_system_data.make_array_layout_dtos`
    と同型の 0/1/2 パターン。参照軸・直積形状の意味はそちらの docstring
    に同じ。ここでは二次電流キーのみ二重かご用
    （``double_cage_im_secondary_inner_current`` /
    ``double_cage_im_secondary_outer_current``）に差し替える。

    - **0**: 参照軸のみ
      ``reference_axes=[slip, frequency, input_line_voltage]``。
    - **1**: 参照軸 ``[slip]``、各すべり点に周波数・電圧・電流（1 次長）あり。
    - **2**: 参照軸
      ``[slip, frequency, input_line_voltage]``、電流は直積 shape ``(4,2,3)``。

    Returns:
      tuple[ArrayLayoutDto, ...]: ``(broadcast, slip_cartesian, full_cartesian)``。
    """
    phase_rotation = np.exp(1j * np.pi / 6.0)
    line_voltage_magnitudes = np.array([200.0, 100.0, 300.0])
    line_voltage_array = line_voltage_magnitudes * phase_rotation
    measured_voltage = ArrayComplexVoltageDto(
        value=line_voltage_array, unit="V"
    )
    measured_frequency = ArrayFrequencyDto(
        value=np.array([50.0, 60.0]), unit="Hz"
    )

    slip_array = ArraySlipDto(value=np.array([0.0, 0.01, 0.036, 1.0]), unit="-")
    input_line_voltage_array = ArrayComplexVoltageDto(
        value=np.array([200.0, 100.0, 300.0, 250.0]), unit="V"
    )
    frequency_array = ArrayFrequencyDto(
        value=np.array([50.0, 60.0, 50.0, 60.0]), unit="Hz"
    )
    primary_current_array = ArrayComplexCurrentDto(
        value=np.array([13.86, 13.00, 13.86, 13.00]), unit="A"
    )
    excitation_current_array = ArrayComplexCurrentDto(
        value=np.array([5.47, 5.00, 5.47, 5.00]), unit="A"
    )
    secondary_current_array = ArrayComplexCurrentDto(
        value=np.array([11.66, 10.00, 11.66, 10.00]), unit="A"
    )
    input_line_current_array = ArrayComplexCurrentDto(
        value=np.array([14.86, 14.00, 14.86, 14.00]), unit="A"
    )

    def _create_all_current_arrays() -> tuple[
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
    ]:
        slip_values = slip_array.get_value()
        frequency_values = measured_frequency.get_value()
        line_voltage_values = measured_voltage.get_value()
        num_slip = slip_values.size
        num_freq = frequency_values.size
        num_voltage = line_voltage_values.size
        ref_shape = (num_slip, num_freq, num_voltage)

        primary_values = np.zeros(ref_shape, dtype=np.complex128)
        excitation_values = np.zeros(ref_shape, dtype=np.complex128)
        secondary_values = np.zeros(ref_shape, dtype=np.complex128)
        line_values = np.zeros(ref_shape, dtype=np.complex128)
        conductor_values = np.zeros(ref_shape, dtype=np.complex128)

        base_slip = 0.036
        base_frequency = 50.0
        base_voltage_magnitude = 200.0

        for i_slip, slip_val in enumerate(slip_values):
            for i_freq, freq_val in enumerate(frequency_values):
                for i_volt, voltage_val in enumerate(line_voltage_values):
                    voltage_magnitude = np.abs(voltage_val)
                    voltage_phase = np.angle(voltage_val)
                    voltage_factor = voltage_magnitude / base_voltage_magnitude
                    slip_factor = 1.0 + (slip_val - base_slip) * 0.2
                    frequency_factor = (
                        1.0 + (freq_val - base_frequency) / base_frequency * 0.1
                    )

                    primary_magnitude = (
                        13.86 * voltage_factor * slip_factor * frequency_factor
                    )
                    primary_values[i_slip, i_freq, i_volt] = (
                        primary_magnitude * np.exp(1j * voltage_phase)
                    )

                    excitation_active = 0.49 * voltage_factor * frequency_factor
                    excitation_reactive = (
                        5.47 * voltage_factor * frequency_factor
                    )
                    excitation_phase = voltage_phase - np.pi / 2.0
                    excitation_values[i_slip, i_freq, i_volt] = (
                        excitation_active * np.exp(1j * voltage_phase)
                        + 1j
                        * excitation_reactive
                        * np.exp(1j * excitation_phase)
                    )

                    secondary_magnitude = (
                        11.66 * voltage_factor * slip_factor * frequency_factor
                    )
                    secondary_phase_offset = -slip_val * np.pi / 4.0
                    secondary_values[i_slip, i_freq, i_volt] = (
                        secondary_magnitude
                        * np.exp(1j * (voltage_phase + secondary_phase_offset))
                    )

                    line_magnitude = (
                        13.86 * voltage_factor * slip_factor * frequency_factor
                    )
                    line_values[i_slip, i_freq, i_volt] = (
                        line_magnitude * np.exp(1j * voltage_phase)
                    )
                    conductor_values[i_slip, i_freq, i_volt] = (
                        line_magnitude * np.exp(1j * voltage_phase)
                    )

        return (
            ArrayComplexCurrentDto(value=primary_values, unit="A"),
            ArrayComplexCurrentDto(value=excitation_values, unit="A"),
            ArrayComplexCurrentDto(value=secondary_values, unit="A"),
            ArrayComplexCurrentDto(value=line_values, unit="A"),
            ArrayComplexCurrentDto(value=conductor_values, unit="A"),
        )

    slip_key = ArrayKey.SLIP
    frequency_key = ArrayKey.FREQUENCY
    input_line_voltage_key = ArrayKey.INPUT_LINE_VOLTAGE
    input_line_current_key = ArrayKey.INPUT_LINE_CURRENT
    conductor_current_key = ArrayKey.CONDUCTOR_CURRENT_PIE_SINGLE
    im_primary_current_key = ArrayKey.IM_PRIMARY_CURRENT
    im_excitation_current_key = ArrayKey.IM_EXCITATION_CURRENT
    # --- 0 ---
    reference_only = ArrayLayoutDto(
        arrays={
            slip_key: slip_array,
            frequency_key: measured_frequency,
            input_line_voltage_key: measured_voltage,
        },
        reference_axes=[slip_key, frequency_key, input_line_voltage_key],
    )

    # --- 1 ---
    slip_cartesian = ArrayLayoutDto(
        arrays={
            slip_key: slip_array,
            frequency_key: frequency_array,
            input_line_voltage_key: input_line_voltage_array,
            input_line_current_key: input_line_current_array,
            conductor_current_key: input_line_current_array,
            im_primary_current_key: primary_current_array,
            im_excitation_current_key: excitation_current_array,
            ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT: (
                secondary_current_array
            ),
            ArrayKey.DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT: (
                secondary_current_array
            ),
        },
        reference_axes=[slip_key],
    )

    # --- 2 ---
    (
        primary_all,
        excitation_all,
        secondary_all,
        line_all,
        conductor_all,
    ) = _create_all_current_arrays()
    full_cartesian = ArrayLayoutDto(
        arrays={
            slip_key: slip_array,
            frequency_key: measured_frequency,
            input_line_voltage_key: measured_voltage,
            input_line_current_key: line_all,
            conductor_current_key: conductor_all,
            im_primary_current_key: primary_all,
            im_excitation_current_key: excitation_all,
            ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT: (secondary_all),
            ArrayKey.DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT: (secondary_all),
        },
        reference_axes=[slip_key, frequency_key, input_line_voltage_key],
    )

    return (reference_only, slip_cartesian, full_cartesian)


def make_input_im_cable_system_dtos() -> InputDtos:
    """二重かご向けの 27 パターン InputDtos を生成する。"""
    im_dtos = make_double_cage_im_dtos()
    cable_dtos = make_cable_dtos()
    layouts = make_array_layout_dtos()
    layout_pairs: list[tuple[str, ArrayLayoutDto]] = [
        ("broadcast", layouts[0]),
        ("slip_cartesian", layouts[1]),
        ("full_cartesian", layouts[2]),
    ]

    systems: list[InputDto] = []
    for im_dto in im_dtos:
        im_name = im_dto.im_series.name.get_value()
        for cable_dto in cable_dtos:
            cable_name = (
                "no_cable" if cable_dto is None else cable_dto.name.get_value()
            )
            for layout_name, layout in layout_pairs:
                system_name_value = f"{layout_name}_{im_name}_{cable_name}"
                systems.append(
                    InputDto(
                        name=ImCableSystemName(value=system_name_value),
                        array_layout=layout,
                        im=im_dto,
                        cable=cable_dto,
                    )
                )

    if len(systems) != 27:
        raise ValueError(f"期待した 27 ではありません: {len(systems)}")
    return InputDtos(objects=systems)


__all__ = [
    "make_array_layout_dtos",
    "make_cable_dtos",
    "make_double_cage_im_dtos",
    "make_double_cage_im_series_dtos",
    "make_input_im_cable_system_dtos",
]
