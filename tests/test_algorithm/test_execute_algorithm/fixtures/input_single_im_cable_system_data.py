"""InputDto を構築するためのテストデータ生成モジュール（単一かご）。

Execute アルゴリズムテスト用の InputDto 組み立て（単一かご）。

``tests/test_algorithm/test_execute_algorithm`` 配下のテストからのみ import する。
IM・ケーブル物性は execute 入力契約に合わせ SI 基本単位（V, W, H, Ω/m 等）で記載する。
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
    CableSeriesDtos,
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

# ケーブル「現実」系が旧 mΩ/ft 等で表していた物性と等価な SI 基本単位（Ω/m, H/m, Ω·m, F/m）
_SI_CABLE_COND_R_OHM_PER_M: float = 3.280839895013123e-06
_SI_CABLE_COND_L_H_PER_M: float = 3.280839895013123e-06
_SI_CABLE_GROUND_RLEN_OHM_M: float = 3048.0
_SI_CABLE_GROUND_C_F_PER_M: float = 3.2808398950131233e-09


def _create_base_im_series_dto(
    name: str,
    connection_type: str,
    circuit_type: str,
    primary_model: ImPrimaryModelDto,
    excitation_model: ImExcitationModelDto,
    secondary_model: ImSecondaryModelDto,
) -> ImSeriesDto:
    """共通パラメータを使用してImSeriesDtoを作成するヘルパー関数。

    Args:
        name: シリーズ名
        connection_type: 結線方式（"STAR" or "DELTA"）
        circuit_type: 回路タイプ（"L" or "T"）
        primary_model: 一次回路モデル
        excitation_model: 励磁回路モデル
        secondary_model: 二次回路モデル

    Returns:
        ImSeriesDto: 作成されたImSeriesDto
    """
    branch = ImSecondaryCageBranchType.SINGLE
    secondary_resistance = FloatResistanceDto(value=0.3398, unit="Ω")
    secondary_inductance = FloatInductanceDto(
        value=0.001785650652,
        unit="H",
    )
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
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_models={branch: secondary_model},
        secondary_resistances={branch: secondary_resistance},
        secondary_inductances={branch: secondary_inductance},
        friction_windage_model=ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.NONE
        ),
        stray_load_model=ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
    )


def make_single_cage_im_series_dtos() -> list[ImSeriesDto]:
    """テスト用の ImSeriesDto リスト（単一かご）を生成する。

    Returns:
        list[ImSeriesDto]: すべてのIMモデルタイプを含むリスト。
            同じようなモデルの組み合わせが多いため、必要最小限の7個のImSeriesDtoを作成。
    """
    # TEST1: 基本モデル（すべてBASIC）
    im_series_1 = _create_base_im_series_dto(
        name="TEST1",
        connection_type="STAR",
        circuit_type="L",
        primary_model=ImPrimaryModelDto(
            name=ImPrimaryModelType.BASIC, params=None
        ),
        excitation_model=ImExcitationModelDto(
            name=ImExcitationModelType.BASIC, params=None
        ),
        secondary_model=ImSecondaryModelDto(
            name=ImSecondaryModelType.BASIC, params=None
        ),
    )

    # TEST2: すべてSlip_dependent（一次、励磁、二次）
    im_series_2 = _create_base_im_series_dto(
        name="TEST2",
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
        secondary_model=ImSecondaryModelDto(
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
    )

    # TEST3: Current_dependentの2次側（SKIN_EFFECT）+ 一次・励磁も電流依存
    im_series_3 = _create_base_im_series_dto(
        name="TEST3",
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
        secondary_model=ImSecondaryModelDto(
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
    )

    # TEST4: Current_dependentの2次側（LEAKAGE_SATURATION）+ 一次・励磁も電流依存
    im_series_4 = _create_base_im_series_dto(
        name="TEST4",
        connection_type="STAR",
        circuit_type="T",
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
        secondary_model=ImSecondaryModelDto(
            name=ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_secondary_leakage_x", value=0.15),
                    FloatParamDto(name="beta_secondary_leakage_x", value=0.25),
                ]
            ),
        ),
    )

    # TEST5: Current_dependentの2次側（SKIN_EFFECT_AND_LEAKAGE_SATURATION）+ 一次・励磁も電流依存
    im_series_5 = _create_base_im_series_dto(
        name="TEST5",
        connection_type="DELTA",
        circuit_type="T",
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
        secondary_model=ImSecondaryModelDto(
            name=ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_secondary_r", value=0.4),
                    FloatParamDto(name="beta_secondary_r", value=0.2),
                    FloatParamDto(name="alpha_secondary_x", value=0.3),
                    FloatParamDto(name="beta_secondary_x", value=0.1),
                    FloatParamDto(name="alpha_secondary_leakage_x", value=0.15),
                    FloatParamDto(name="beta_secondary_leakage_x", value=0.25),
                ]
            ),
        ),
    )

    # TEST6では、一次側をCurrent_dependent、励磁・二次側をSlip_dependentとする
    im_series_6 = _create_base_im_series_dto(
        name="TEST6",
        connection_type="STAR",
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
            name=ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_excitation_r", value=0.1),
                    FloatParamDto(name="alpha_excitation_x", value=0.2),
                    FloatParamDto(name="beta_excitation_x", value=0.3),
                ]
            ),
        ),
        secondary_model=ImSecondaryModelDto(
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
    )

    # TEST7では、一次側をSlip_dependent、励磁・二次側をCurrent_dependentとする
    im_series_7 = _create_base_im_series_dto(
        name="TEST7",
        connection_type="DELTA",
        circuit_type="L",
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
            name=ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_excitation_r", value=0.1),
                    FloatParamDto(name="alpha_excitation_x", value=0.2),
                    FloatParamDto(name="beta_excitation_x", value=0.3),
                ]
            ),
        ),
        secondary_model=ImSecondaryModelDto(
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
    )

    return [
        im_series_1,
        im_series_2,
        im_series_3,
        im_series_4,
        im_series_5,
        im_series_6,
        im_series_7,
    ]


def make_cable_series_dtos() -> CableSeriesDtos:
    """テスト用のCableSeriesDtosを生成する。

    Returns:
        CableSeriesDtos: 9つのCableSeriesDtoを含むCableSeriesDtos。
            - MAIN_IDEAL: 完全理想ケーブル（R'/X' ゼロ、接地 R 無限、C' ゼロ、SI 基本単位）
            - MAIN_REAL: 現実ケーブル（物性は _SI_CABLE_* 定数、旧 ft 系と等価）
            - MAIN_CONDUCTOR_IDEAL: 導線だけ理想
            - MAIN_INSULATED: 完全絶縁
            - MLE_IDEAL / MLE_REAL / MLE_CONDUCTOR_IDEAL / MLE_INSULATED: MLE 形状で同上
            - POTHEAD_REAL: MAIN_REAL と同型物性
    """
    # ケーブルシリーズ1: MAIN_IDEAL（理想ケーブル）
    cable_series_main_ideal = CableSeriesDto(
        name=CableSeriesName(value="MAIN_IDEAL"),
        shape_type=CableShapeTypeDto(value="ROUND"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.0,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=0.0,
            unit="H/m",
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=np.inf,
            unit="Ω*m",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=0.0,
            unit="F/m",
        ),
    )

    # ケーブルシリーズ2: MAIN_REAL（現実ケーブル）
    cable_series_main_real = CableSeriesDto(
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

    # ケーブルシリーズ3: MLE_IDEAL（理想ケーブル）
    cable_series_mle_ideal = CableSeriesDto(
        name=CableSeriesName(value="MLE_IDEAL"),
        shape_type=CableShapeTypeDto(value="FLAT"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.0,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=0.0,
            unit="H/m",
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=np.inf,
            unit="Ω*m",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=0.0,
            unit="F/m",
        ),
    )

    # ケーブルシリーズ4: MLE_REAL（現実ケーブル）
    cable_series_mle_real = CableSeriesDto(
        name=CableSeriesName(value="MLE_REAL"),
        shape_type=CableShapeTypeDto(value="FLAT"),
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

    # ケーブルシリーズ3: MAIN_CONDUCTOR_IDEAL（導線だけ理想）
    cable_series_main_conductor_ideal = CableSeriesDto(
        name=CableSeriesName(value="MAIN_CONDUCTOR_IDEAL"),
        shape_type=CableShapeTypeDto(value="ROUND"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.0,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=0.0,
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

    # ケーブルシリーズ4: MAIN_INSULATED（完全絶縁）
    cable_series_main_insulated = CableSeriesDto(
        name=CableSeriesName(value="MAIN_INSULATED"),
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
            value=np.inf,
            unit="Ω*m",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=0.0,
            unit="F/m",
        ),
    )

    # ケーブルシリーズ5: MLE_CONDUCTOR_IDEAL（導線だけ理想）
    cable_series_mle_conductor_ideal = CableSeriesDto(
        name=CableSeriesName(value="MLE_CONDUCTOR_IDEAL"),
        shape_type=CableShapeTypeDto(value="FLAT"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.0,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=0.0,
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

    # ケーブルシリーズ6: MLE_INSULATED（完全絶縁）
    cable_series_mle_insulated = CableSeriesDto(
        name=CableSeriesName(value="MLE_INSULATED"),
        shape_type=CableShapeTypeDto(value="FLAT"),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=_SI_CABLE_COND_R_OHM_PER_M,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=_SI_CABLE_COND_L_H_PER_M,
            unit="H/m",
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=np.inf,
            unit="Ω*m",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=0.0,
            unit="F/m",
        ),
    )

    # ケーブルシリーズ7: POTHEAD_REAL（現実ケーブル）
    cable_series_pothead_real = CableSeriesDto(
        name=CableSeriesName(value="POTHEAD_REAL"),
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

    return CableSeriesDtos(
        objects=[
            cable_series_main_ideal,
            cable_series_main_real,
            cable_series_main_conductor_ideal,
            cable_series_main_insulated,
            cable_series_mle_ideal,
            cable_series_mle_real,
            cable_series_mle_conductor_ideal,
            cable_series_mle_insulated,
            cable_series_pothead_real,
        ]
    )


def make_single_cage_im_dtos() -> tuple[ImDto, ...]:
    """テスト用のImDto（単一かご）を生成する。

    Returns:
        tuple[ImDto, ...]: 7個のImDtoを含むタプル。
            TEST1-TEST7に対応するすべてのIM種を返す。
    """
    im_series_dtos = make_single_cage_im_series_dtos()
    im_dtos_list = []
    for i in range(1, 8):
        series_name = f"TEST{i}"
        im_series_name = ImSeriesName.create(
            value=series_name,
        )
        im_series_dto = get_im_series_by_name(im_series_dtos, im_series_name)
        im_dtos_list.append(
            ImDto(
                name=ImName(value=series_name),
                im_series=im_series_dto,
            )
        )
    return tuple(im_dtos_list)


def make_cable_dtos() -> tuple[CableDto | None, ...]:
    """テスト用のCableDtoを生成する。

    Returns:
        tuple[CableDto | None, ...]: 7要素のタプル（6個のCableDtoとケーブルなしを表すNone）。
            BASIC（理想版・現実版）、FREQUENCY_DEPENDENT_SKIN_EFFECT_V1（現実版のみ）、
            CURRENT_DEPENDENT_SKIN_EFFECT_V1（現実版のみ）、
            完全絶縁、理想導体のすべてのケーブル種を返す。
    """
    cable_series_dtos = make_cable_series_dtos()

    # CableSeriesDtoを取得
    cable_series_main_ideal = cable_series_dtos.get_by_name("MAIN_IDEAL")
    cable_series_main_real = cable_series_dtos.get_by_name("MAIN_REAL")
    cable_series_mle_ideal = cable_series_dtos.get_by_name("MLE_IDEAL")
    cable_series_mle_real = cable_series_dtos.get_by_name("MLE_REAL")
    cable_series_main_conductor_ideal = cable_series_dtos.get_by_name(
        "MAIN_CONDUCTOR_IDEAL"
    )
    cable_series_main_insulated = cable_series_dtos.get_by_name(
        "MAIN_INSULATED"
    )
    cable_series_mle_conductor_ideal = cable_series_dtos.get_by_name(
        "MLE_CONDUCTOR_IDEAL"
    )
    cable_series_mle_insulated = cable_series_dtos.get_by_name("MLE_INSULATED")
    cable_series_pothead_real = cable_series_dtos.get_by_name("POTHEAD_REAL")
    if (
        cable_series_main_ideal is None
        or cable_series_main_real is None
        or cable_series_mle_ideal is None
        or cable_series_mle_real is None
        or cable_series_main_conductor_ideal is None
        or cable_series_main_insulated is None
        or cable_series_mle_conductor_ideal is None
        or cable_series_mle_insulated is None
        or cable_series_pothead_real is None
    ):
        raise ValueError("CableSeriesDto not found")

    cable_dtos_list: list[CableDto | None] = []

    # ケーブル1: BASICモデル（完全理想ケーブル）
    cable_basic_ideal_sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=4000.0, unit="ft"),
                series=cable_series_main_ideal,
            ),
            CableSectionDto(
                name=CableSectionName(value="MLE"),
                length=FloatLengthDto(value=200.0, unit="ft"),
                series=cable_series_mle_ideal,
            ),
        ]
    )
    cable_dtos_list.append(
        CableDto(
            name=CableName(value="ALL_BASIC_IDEAL"),
            sections=cable_basic_ideal_sections,
            conductor_model=CableConductorModelDto(
                name=ConductorModelType.BASIC, params=None
            ),
        )
    )

    # ケーブル2: BASICモデル（現実ケーブル）
    cable_basic_real_sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=4000.0, unit="ft"),
                series=cable_series_main_real,
            ),
            CableSectionDto(
                name=CableSectionName(value="MLE"),
                length=FloatLengthDto(value=200.0, unit="ft"),
                series=cable_series_mle_real,
            ),
        ]
    )
    cable_dtos_list.append(
        CableDto(
            name=CableName(value="cable_basic_real"),
            sections=cable_basic_real_sections,
            conductor_model=CableConductorModelDto(
                name=ConductorModelType.BASIC, params=None
            ),
        )
    )

    # ケーブル3: FREQUENCY_DEPENDENT_SKIN_EFFECT_V1モデル（現実ケーブル）
    cable_freq_dep_real_sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=5000.0, unit="ft"),
                series=cable_series_main_real,
            ),
            CableSectionDto(
                name=CableSectionName(value="MLE"),
                length=FloatLengthDto(value=200.0, unit="ft"),
                series=cable_series_mle_real,
            ),
            CableSectionDto(
                name=CableSectionName(value="POTHEAD"),
                length=FloatLengthDto(value=3.0, unit="ft"),
                series=cable_series_pothead_real,
            ),
        ]
    )
    cable_dtos_list.append(
        CableDto(
            name=CableName(value="cable_frequency_dependent"),
            sections=cable_freq_dep_real_sections,
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
    )
    # ケーブル4: CURRENT_DEPENDENT_SKIN_EFFECT_V1モデル（現実ケーブル）
    cable_current_dep_real_sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=6000.0, unit="ft"),
                series=cable_series_main_real,
            ),
            CableSectionDto(
                name=CableSectionName(value="MLE"),
                length=FloatLengthDto(value=200.0, unit="ft"),
                series=cable_series_mle_real,
            ),
            CableSectionDto(
                name=CableSectionName(value="POTHEAD"),
                length=FloatLengthDto(value=3.0, unit="ft"),
                series=cable_series_pothead_real,
            ),
        ]
    )
    cable_dtos_list.append(
        CableDto(
            name=CableName(value="CURRENT_DEP_REAL"),
            sections=cable_current_dep_real_sections,
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
    )
    # ケーブル5: 完全絶縁（MAINとMLEの両方が完全絶縁）
    cable_insulated_sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=4000.0, unit="ft"),
                series=cable_series_main_insulated,
            ),
            CableSectionDto(
                name=CableSectionName(value="MLE"),
                length=FloatLengthDto(value=200.0, unit="ft"),
                series=cable_series_mle_insulated,
            ),
        ]
    )
    cable_dtos_list.append(
        CableDto(
            name=CableName(value="cable_insulated"),
            sections=cable_insulated_sections,
            conductor_model=CableConductorModelDto(
                name=ConductorModelType.BASIC, params=None
            ),
        )
    )

    # ケーブル6: 理想導体（MAINとMLEの両方が導線理想）
    cable_conductor_ideal_sections = CableSectionDtos(
        objects=[
            CableSectionDto(
                name=CableSectionName(value="MAIN"),
                length=FloatLengthDto(value=4000.0, unit="ft"),
                series=cable_series_main_conductor_ideal,
            ),
            CableSectionDto(
                name=CableSectionName(value="MLE"),
                length=FloatLengthDto(value=200.0, unit="ft"),
                series=cable_series_mle_conductor_ideal,
            ),
        ]
    )
    cable_dtos_list.append(
        CableDto(
            name=CableName(value="cable_conductor_ideal"),
            sections=cable_conductor_ideal_sections,
            conductor_model=CableConductorModelDto(
                name=ConductorModelType.BASIC, params=None
            ),
        )
    )

    # ケーブル7（ケーブルなし）は、Noneで表現する
    cable_dtos_list.append(None)

    return tuple(cable_dtos_list)


def make_array_layout_dtos() -> tuple[ArrayLayoutDto, ...]:  # noqa: PLR0915
    """テスト用のArrayLayoutDtoを生成する。

    測定電圧・周波数・すべり配列は共通とし、以下の3種類の配列レイアウトを
    あらかじめ生成して返す。いずれも参照軸（reference_axes）で定義する CARTESIAN 専用。

    - 0: 参照軸のみ（非参照軸なし）:
        slip, frequency, input_line_voltage のみを軸に持ち、
        reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY, ArrayKey.INPUT_LINE_VOLTAGE]。
    - 1: 参照軸 slip のみ、各すべり点ごとの電流値あり:
        参照軸を[ArrayKey.SLIP]とし、各すべり点ごとに電圧・周波数・電流値が定義された
        配列レイアウト。
    - 2: 参照軸 slip, frequency, input_line_voltage、各地点ごとの電流値あり:
        参照軸を[ArrayKey.SLIP, ArrayKey.FREQUENCY, ArrayKey.INPUT_LINE_VOLTAGE]とし、各地点
        （すべり×周波数×線間電圧）の組み合わせごとに電流値が定義された
        配列レイアウト。

    Returns:
        tuple[ArrayLayoutDto, ...]: 以下の順序でArrayLayoutDtoを含むタプル。
            0: 参照軸のみ（slip, frequency, input_line_voltage）
            1: 参照軸: slip、各すべり点ごとの電流値あり
            2: 参照軸: slip, frequency, input_line_voltage、各地点ごとの電流値あり
    """
    # 測定電圧配列を作成（複素数配列）
    # NOTE: Execute ステージは balanced 規約（線間→相は大きさ 1/√3 のみで
    #   30° の位相回転を付与しない）を採用する。よって線間電圧を角度 0°
    #   （純実数）で与えると、相電圧も角度 0°（教科書の基準フェーザ）になり、
    #   電流の有効分・無効分（real/imag）が教科書値と一致する。
    line_voltage_array = np.array([200.0, 100.0, 300.0], dtype=np.complex128)

    measured_voltage = ArrayComplexVoltageDto(
        value=line_voltage_array, unit="V"
    )

    # 測定周波数配列を作成
    measured_frequency = ArrayFrequencyDto(
        value=np.array([50.0, 60.0]), unit="Hz"
    )

    # すべり配列を作成（0, 0.036, 1を含む1次配列）
    # test_simulate.pyで使用されている0.036を含む
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

    # CARTESIANモード用の配列を作成
    # 参照軸: slip (4要素) × frequency (2要素) × line_voltage (3要素) = 24要素
    # CARTESIANモードでは、参照軸は元の長さのまま（展開しない）
    # 参照軸以外の配列（電流配列）のみ、参照軸の組み合わせ（直積）の長さ（24要素）の1次配列
    slip_values = slip_array.get_value()
    frequency_values = measured_frequency.get_value()
    line_voltage_values = measured_voltage.get_value()

    # test_simulate.pyの値（すべり0.036, 周波数50Hz, 線間電圧200V）を基準に電流値を設定
    # 入力電流: 13.86A（大きさ）、有効12.08A、無効6.79A
    # IM入力電流: 13.86A
    # 励磁電流: 有効0.49A、無効5.47A
    # 二次電流: 11.66A（大きさ）
    # 線電流: 13.86A（大きさ）

    # 基準値（すべり0.036, 周波数50Hz, 線間電圧200V）
    base_slip = 0.036
    base_frequency = 50.0
    base_voltage_magnitude = 200.0

    def _create_all_current_arrays() -> tuple[
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
        ArrayComplexCurrentDto,
    ]:
        """一次・励磁・二次・線電流・導体電流の配列をまとめて作成するヘルパー関数。

        CARTESIAN（参照軸: slip, frequency, input_line_voltage）用に、
        ref_shape = (num_slip, num_freq, num_voltage) と同じshapeを持つ
        多次元配列を直接生成する。

        Returns:
            tuple[ArrayComplexCurrentDto, ...]: 順にprimary, excitation,
                secondary, line, conductorの電流配列DTO。π型ではconductor＝line。
        """
        num_slip = slip_values.size
        num_freq = frequency_values.size
        num_voltage = line_voltage_values.size
        ref_shape = (num_slip, num_freq, num_voltage)

        primary_values = np.zeros(ref_shape, dtype=np.complex128)
        excitation_values = np.zeros(ref_shape, dtype=np.complex128)
        secondary_values = np.zeros(ref_shape, dtype=np.complex128)
        line_values = np.zeros(ref_shape, dtype=np.complex128)
        conductor_values = np.zeros(ref_shape, dtype=np.complex128)

        for i_slip, slip_val in enumerate(slip_values):
            for i_freq, freq_val in enumerate(frequency_values):
                for i_volt, voltage_val in enumerate(line_voltage_values):
                    voltage_magnitude = np.abs(voltage_val)
                    voltage_phase = np.angle(voltage_val)

                    # すべり、周波数、電圧に応じて電流値をスケール
                    voltage_factor = voltage_magnitude / base_voltage_magnitude
                    slip_factor = 1.0 + (slip_val - base_slip) * 0.2
                    frequency_factor = (
                        1.0 + (freq_val - base_frequency) / base_frequency * 0.1
                    )

                    # primary_current: IM入力電流 ≈ 13.86A（大きさ）
                    primary_magnitude = (
                        13.86 * voltage_factor * slip_factor * frequency_factor
                    )
                    primary_values[i_slip, i_freq, i_volt] = (
                        primary_magnitude * np.exp(1j * voltage_phase)
                    )

                    # excitation_current: 励磁電流 ≈ 0.49 + j*5.47 A
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

                    # secondary_current: 二次電流 ≈ 11.66A（大きさ）
                    secondary_magnitude = (
                        11.66 * voltage_factor * slip_factor * frequency_factor
                    )
                    secondary_phase_offset = -slip_val * np.pi / 4.0
                    secondary_values[i_slip, i_freq, i_volt] = (
                        secondary_magnitude
                        * np.exp(1j * (voltage_phase + secondary_phase_offset))
                    )

                    # input_line_current: 入力線電流 ≈ 13.86A（大きさ）
                    line_magnitude = (
                        13.86 * voltage_factor * slip_factor * frequency_factor
                    )
                    line_values[i_slip, i_freq, i_volt] = (
                        line_magnitude * np.exp(1j * voltage_phase)
                    )
                    # conductor_current: π型では入力線電流と同じ  # noqa: ERA001
                    conductor_values[i_slip, i_freq, i_volt] = (
                        line_magnitude * np.exp(1j * voltage_phase)
                    )

        primary_array = ArrayComplexCurrentDto(value=primary_values, unit="A")
        excitation_array = ArrayComplexCurrentDto(
            value=excitation_values, unit="A"
        )
        secondary_array = ArrayComplexCurrentDto(
            value=secondary_values, unit="A"
        )
        line_array = ArrayComplexCurrentDto(value=line_values, unit="A")
        conductor_array = ArrayComplexCurrentDto(
            value=conductor_values, unit="A"
        )

        return (
            primary_array,
            excitation_array,
            secondary_array,
            line_array,
            conductor_array,
        )

    slip_key = ArrayKey.SLIP
    frequency_key = ArrayKey.FREQUENCY
    input_line_voltage_key = ArrayKey.INPUT_LINE_VOLTAGE
    input_line_current_key = ArrayKey.INPUT_LINE_CURRENT
    conductor_current_key = ArrayKey.CONDUCTOR_CURRENT_PIE_SINGLE
    im_primary_current_key = ArrayKey.IM_PRIMARY_CURRENT
    im_excitation_current_key = ArrayKey.IM_EXCITATION_CURRENT
    single_cage_secondary_current_key = (
        ArrayKey.SINGLE_CAGE_IM_SECONDARY_CURRENT
    )

    # --- 0: 参照軸のみ（slip, frequency, input_line_voltage） ---
    reference_only_array_layout = ArrayLayoutDto(
        arrays={
            slip_key: slip_array,
            frequency_key: measured_frequency,
            input_line_voltage_key: measured_voltage,
        },
        reference_axes=[slip_key, frequency_key, input_line_voltage_key],
    )

    # --- 1: 参照軸 [ArrayKey.SLIP]、各すべり点ごとの電流値あり ---
    # π型では導体電流＝入力線電流とみなす。キーは実装契約に合わせて conductor_current.pie_single とする。
    conductor_current_array = input_line_current_array
    slip_cartesian_array_layout = ArrayLayoutDto(
        arrays={
            slip_key: slip_array,
            frequency_key: frequency_array,
            input_line_voltage_key: input_line_voltage_array,
            input_line_current_key: input_line_current_array,
            conductor_current_key: conductor_current_array,
            im_primary_current_key: primary_current_array,
            im_excitation_current_key: excitation_current_array,
            single_cage_secondary_current_key: secondary_current_array,
        },
        reference_axes=[slip_key],
    )

    # --- 2: 参照軸 [ArrayKey.SLIP, ArrayKey.FREQUENCY, ArrayKey.INPUT_LINE_VOLTAGE]、各地点ごとの電流値あり ---
    (
        primary_current_array,
        excitation_current_array,
        secondary_current_array,
        input_line_current_array,
        conductor_current_array,
    ) = _create_all_current_arrays()

    full_cartesian_array_layout = ArrayLayoutDto(
        arrays={
            slip_key: slip_array,
            frequency_key: measured_frequency,
            input_line_voltage_key: measured_voltage,
            input_line_current_key: input_line_current_array,
            conductor_current_key: conductor_current_array,
            im_primary_current_key: primary_current_array,
            im_excitation_current_key: excitation_current_array,
            single_cage_secondary_current_key: secondary_current_array,
        },
        reference_axes=[slip_key, frequency_key, input_line_voltage_key],
    )

    array_layout_dtos_list: list[ArrayLayoutDto] = [
        reference_only_array_layout,
        slip_cartesian_array_layout,
        full_cartesian_array_layout,
    ]

    return tuple(array_layout_dtos_list)


def make_input_im_cable_system_dtos() -> InputDtos:
    """テスト用のInputDtosを生成する。

    ImDto, CableDto, ArrayLayoutDtoの全組み合わせでInputDtoを生成する。
    電流依存モデルでも参照軸のみの配列レイアウトでは電流0で計算できるため、フィルタは行わない。

    Returns:
        InputDtos: 全組み合わせから構成されるInputDtoを含む
            InputDtos。
    """
    im_dtos = make_single_cage_im_dtos()
    cable_dtos = make_cable_dtos()
    array_layout_dtos = make_array_layout_dtos()

    # ArrayLayoutDtoごとの識別名を定義しておく
    array_layout_name_pairs: list[tuple[str, ArrayLayoutDto]] = [
        ("broadcast", array_layout_dtos[0]),
        ("slip_cartesian", array_layout_dtos[1]),
        ("full_cartesian", array_layout_dtos[2]),
    ]

    systems: list[InputDto] = []

    for im_dto in im_dtos:
        im_name = im_dto.im_series.name.get_value()
        im_dto_with_series = im_dto

        for cable_dto in cable_dtos:
            cable_dto_with_series = cable_dto
            if cable_dto is not None:
                new_sections: list[CableSectionDto] = []
                for section in cable_dto.sections.get_all():
                    new_sections.append(
                        CableSectionDto(
                            name=section.name,
                            length=section.length,
                            series=section.series,
                        )
                    )
                cable_dto_with_series = CableDto(
                    name=cable_dto.name,
                    sections=CableSectionDtos(objects=new_sections),
                    conductor_model=cable_dto.conductor_model,
                )
            cable_name = (
                "no_cable"
                if cable_dto_with_series is None
                else cable_dto_with_series.name.get_value()
            )
            for array_layout_name, array_layout_dto in array_layout_name_pairs:
                system_name_value = (
                    f"{array_layout_name}_{im_name}_{cable_name}"
                )
                system_name = ImCableSystemName(base=system_name_value)
                systems.append(
                    InputDto(
                        name=system_name,
                        im=im_dto_with_series,
                        cable=cable_dto_with_series,
                        array_layout=array_layout_dto,
                    )
                )

    return InputDtos(
        objects=systems,
    )
