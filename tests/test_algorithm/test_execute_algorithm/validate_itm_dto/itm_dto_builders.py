"""``validate_itm_dto`` テスト用の ItmDto 手組みビルダー。

設計意図:
    本モジュールは検証器テストのために、シミュレーション計算を一切走らせずに
    「正解（バリデーションを通過する）ItmDto」を手組みで生成する。
    検証器が参照するフィールド（電力収支・IM 入力電圧電流・定格値・結線方式）
    だけを引数で差し替えられるようにし、テスト側で「敢えておかしい値」を注入して
    検証器がエラー／警告を出すかを確認できるようにする。

    検証器が読まないフィールド（イミタンス・特性値・ケーブル詳細など）は、
    DTO 構築（``__post_init__``）を通過する最小限の妥当値で埋める。

注意:
    本ビルダーは純粋な DTO 構築のみで、``build_model`` / ``simulate`` は
    呼び出さない。そのためテスト実行時にシミュレーションロジックは走らない。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import numpy as np

from im_cable_system.engine.shared.config import IConfig, ValidationConfig
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    CableConductorModelDto,
    ConductorModelType,
    ImCableSystemName,
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
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
    ImSeriesName,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
    ArraySlipDto,
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableImmittanceDto,
    ItmCableModelDto,
    ItmCablePowerDto,
    ItmCableVoltageCurrentDto,
    ItmDto,
    ItmImBasicDto,
    ItmImCircuitDto,
    ItmImExcitationDto,
    ItmImModelDto,
    ItmImPowerDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
    ItmImVoltageCurrentDto,
    ItmModelDto,
    ItmPowerDto,
    ItmSimulationDto,
    ItmSystemModelDto,
    ItmVoltageCurrentDto,
)

# 配列長（slip × frequency を模した 1 次元配列でも検証器は形状に依存しない）
_N: int = 2
_SQRT_3: float = float(np.sqrt(3.0))
_SINGLE: ImSecondaryCageBranchType = ImSecondaryCageBranchType.SINGLE
_SINGLE_CAGE: ImCageMultiplicityType = ImCageMultiplicityType.SINGLE_CAGE


def _power(value: complex) -> ArrayComplexPowerDto:
    """複素電力配列 DTO を生成する（単位 VA）。"""
    return ArrayComplexPowerDto(
        value=np.full(_N, value, dtype=np.complex128),
        unit="VA",
    )


def _voltage(value: complex) -> ArrayComplexVoltageDto:
    """複素電圧配列 DTO を生成する（単位 V）。"""
    return ArrayComplexVoltageDto(
        value=np.full(_N, value, dtype=np.complex128),
        unit="V",
    )


def _current(value: complex) -> ArrayComplexCurrentDto:
    """複素電流配列 DTO を生成する（単位 A）。"""
    return ArrayComplexCurrentDto(
        value=np.full(_N, value, dtype=np.complex128),
        unit="A",
    )


def _impedance() -> ArrayComplexImpedanceDto:
    """検証器が読まないダミーのインピーダンス配列 DTO を生成する。"""
    return ArrayComplexImpedanceDto(
        value=np.full(_N, 1.0 + 1.0j, dtype=np.complex128),
        unit="Ω",
    )


def _admittance() -> ArrayComplexAdmittanceDto:
    """検証器が読まないダミーのアドミタンス配列 DTO を生成する。"""
    return ArrayComplexAdmittanceDto(
        value=np.full(_N, 0.5 - 0.5j, dtype=np.complex128),
        unit="S",
    )


def _build_im_power(
    *,
    output_power: complex,
    total_loss_power: complex,
) -> ItmImPowerDto:
    """IM 電力 DTO を生成する（検証器は output / total_loss のみ参照）。"""
    branch_power = _power(1.0 + 0.0j)
    return ItmImPowerDto(
        input_power=_power(13.0 + 3.0j),
        primary_loss_power=_power(0.5 + 0.0j),
        excitation_loss_power=_power(0.5 + 0.0j),
        cage_multiplicity=_SINGLE_CAGE,
        secondary_base_loss_power={_SINGLE: branch_power},
        secondary_load_power={_SINGLE: branch_power},
        secondary_branch_total_power={_SINGLE: branch_power},
        secondary_total_power=_power(1.0 + 0.0j),
        friction_windage_loss_power=_power(0.0 + 0.0j),
        stray_load_loss_power=_power(0.0 + 0.0j),
        output_power=_power(output_power),
        total_loss_power=_power(total_loss_power),
        copper_loss_power=_power(1.0 + 0.0j),
        iron_loss_power=_power(1.0 + 0.0j),
    )


def _build_cable_power(
    *,
    input_phase_power: complex,
    total_loss_power: complex,
) -> ItmCablePowerDto:
    """ケーブル電力 DTO を生成する（検証器は input_phase / total_loss を参照）。"""
    return ItmCablePowerDto(
        system_total_input_power=_power(13.0 + 3.0j),
        input_phase_power=_power(input_phase_power),
        conductor_loss_power={PieCableConductorKey.SINGLE: _power(0.5 + 0.0j)},
        ground_loss_power={
            PieCableGroundKey.UPSTREAM: _power(0.25 + 0.0j),
            PieCableGroundKey.DOWNSTREAM: _power(0.25 + 0.0j),
        },
        end_point_phase_power=_power(11.0 + 2.0j),
        total_loss_power=_power(total_loss_power),
    )


def _build_im_voltage_current(
    *,
    im_input_voltage: complex,
    im_input_current: complex,
) -> ItmImVoltageCurrentDto:
    """IM 電圧電流 DTO を生成する（検証器は im_input_* のみ参照）。"""
    voltage = _voltage(im_input_voltage)
    current = _current(im_input_current)
    return ItmImVoltageCurrentDto(
        im_input_voltage=voltage,
        im_input_current=current,
        im_primary_voltage=voltage,
        im_primary_current=current,
        im_excitation_voltage=voltage,
        im_excitation_current=current,
        cage_multiplicity=_SINGLE_CAGE,
        secondary_base_voltage={_SINGLE: voltage},
        secondary_load_voltage={_SINGLE: voltage},
        secondary_branch_current={_SINGLE: current},
    )


def _build_cable_voltage_current() -> ItmCableVoltageCurrentDto:
    """検証器が読まないケーブル電圧電流 DTO を生成する。"""
    voltage = _voltage(100.0 + 0.0j)
    current = _current(5.0 + 0.0j)
    return ItmCableVoltageCurrentDto(
        input_line_voltage=voltage,
        input_line_current=current,
        input_phase_voltage=voltage,
        input_phase_current=current,
        conductor_voltage={PieCableConductorKey.SINGLE: voltage},
        conductor_current={PieCableConductorKey.SINGLE: current},
        ground_voltage={
            PieCableGroundKey.UPSTREAM: voltage,
            PieCableGroundKey.DOWNSTREAM: voltage,
        },
        ground_current={
            PieCableGroundKey.UPSTREAM: current,
            PieCableGroundKey.DOWNSTREAM: current,
        },
        end_point_phase_voltage=voltage,
        end_point_phase_current=current,
    )


def _build_im_model(
    *,
    nameplate_voltage_line: float,
    nameplate_current_line: float,
    connection_type: ImConnectionType,
) -> ItmImModelDto:
    """IM モデル DTO を生成する（検証器は定格値・結線方式のみ参照）。"""
    basic_info = ItmImBasicDto(
        series_name=ImSeriesName.create("TEST_IM"),
        poles=ImPoles.P4,
        nameplate_voltage=FloatVoltageDto(nameplate_voltage_line, "V"),
        nameplate_current=FloatCurrentDto(nameplate_current_line, "A"),
        nameplate_power=FloatActivePowerDto(1000.0, "W"),
        nameplate_frequency=FloatFrequencyDto(50.0, "Hz"),
    )
    circuit_info = ItmImCircuitDto(
        connection_type=connection_type,
        circuit_type=ImCircuitType.T,
    )
    impedance = _impedance()
    admittance = _admittance()
    resistance = FloatResistanceDto(1.0, "Ω")
    inductance = FloatInductanceDto(1.0, "H")
    primary_model = ItmImPrimaryDto(
        model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
        resistance=resistance,
        inductance=inductance,
        impedance=impedance,
        admittance=admittance,
    )
    excitation_model = ItmImExcitationDto(
        model=ImExcitationModelDto(name=ImExcitationModelType.BASIC),
        resistance=resistance,
        inductance=inductance,
        impedance=impedance,
        admittance=admittance,
    )
    secondary_model = ItmImSecondaryDto(
        cage_multiplicity=_SINGLE_CAGE,
        resistances={_SINGLE: resistance},
        inductances={_SINGLE: inductance},
        models={_SINGLE: ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)},
        impedances={_SINGLE: impedance},
        admittances={_SINGLE: admittance},
        base_impedances={_SINGLE: impedance},
        base_admittances={_SINGLE: admittance},
        load_impedances={_SINGLE: impedance},
        load_admittances={_SINGLE: admittance},
    )
    total_model = ItmImTotalDto(impedance=impedance, admittance=admittance)
    return ItmImModelDto(
        name=ImName(value="SINGLE"),
        basic_info=basic_info,
        circuit_info=circuit_info,
        primary_model=primary_model,
        excitation_model=excitation_model,
        secondary_model=secondary_model,
        total_model=total_model,
        friction_windage_model=ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.NONE
        ),
        stray_load_model=ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
    )


def _build_cable_model() -> ItmCableModelDto:
    """検証器が読まないケーブルモデル DTO を生成する（擬似ケーブル相当）。"""
    impedance = _impedance()
    admittance = _admittance()
    cable_immittance = ItmCableImmittanceDto(
        conductor_model=CableConductorModelDto(name=ConductorModelType.BASIC),
        conductor_impedance={PieCableConductorKey.SINGLE: impedance},
        conductor_admittance={PieCableConductorKey.SINGLE: admittance},
        ground_impedance={
            PieCableGroundKey.UPSTREAM: impedance,
            PieCableGroundKey.DOWNSTREAM: impedance,
        },
        ground_admittance={
            PieCableGroundKey.UPSTREAM: admittance,
            PieCableGroundKey.DOWNSTREAM: admittance,
        },
        is_ground_insulated=True,
        is_ground_shorted=False,
        is_conductor_ideal=True,
    )
    return ItmCableModelDto(
        name=None,
        cable_info=None,
        cable_immittance=cable_immittance,
    )


def _build_array_layout() -> ArrayLayoutDto:
    """検証器が読まない配列レイアウト DTO（slip 軸のみ）を生成する。"""
    slip = ArraySlipDto(value=np.array([0.1, 0.5]), unit="-")
    return ArrayLayoutDto(
        arrays={ArrayKey.SLIP: slip},
        reference_axes=[ArrayKey.SLIP],
    )


def _build_system_model() -> ItmSystemModelDto:
    """検証器が読まないシステムモデル DTO を生成する。"""
    return ItmSystemModelDto(
        system_phase_impedance=_impedance(),
        system_phase_admittance=_admittance(),
    )


def build_valid_itm_dto(
    *,
    connection_type: ImConnectionType = ImConnectionType.STAR,
    nameplate_voltage_line: float = 200.0,
    nameplate_current_line: float = 10.0,
    im_input_voltage: complex | None = None,
    im_input_current: complex | None = None,
    im_output_power: complex = 10.0 + 2.0j,
    im_total_loss_power: complex = 2.0 + 0.5j,
    cable_total_loss_power: complex = 1.0 + 0.5j,
    cable_input_phase_power: complex | None = None,
    with_power: bool = True,
) -> ItmDto:
    """検証を通過する「正解」ItmDto を手組みで生成する。

    既定値は、エネルギー保存則（入力 = 出力 + 損失）と電流電圧レンジ
    （定格 ±許容）の両方を満たすよう調整されている。引数で各値を上書きすると、
    検証器がエラー／警告を出すべき「おかしい」状態を注入できる。

    Args:
        connection_type: IM の結線方式（STAR / DELTA）。検証は結線に依存しない
            （Execute は常にスター等価相）ため、判定には影響しない。
        nameplate_voltage_line: 定格電圧（線間, V）。
        nameplate_current_line: 定格電流（線, A）。
        im_input_voltage: IM 入力相電圧 [V]。None なら結線に依らず
            スター等価の定格相電圧（線間 / √3、レンジ内）を用いる。
        im_input_current: IM 入力相電流 [A]。None なら結線に依らず
            スター等価の定格相電流（線電流、レンジ内）を用いる。
        im_output_power: IM 出力電力 [VA]。
        im_total_loss_power: IM 全損失電力 [VA]。
        cable_total_loss_power: ケーブル全損失電力 [VA]。
        cable_input_phase_power: ケーブル入力相電力 [VA]。None なら
            出力 + IM 損失 + ケーブル損失（収支が成立する値）を用いる。
        with_power: False の場合 ``simulation_result.power`` を None にする。

    Returns:
        ItmDto: 手組みされた中間 DTO。
    """
    # Execute ステージは結線に依らず「スター等価相」で計算する。検証器も定格を
    # 常にスター基準で相換算（相電圧 = 線間 / √3、相電流 = 線電流）するため、
    # 既定の im_input_* も結線に依らずスター等価相（レンジ内）を用いる。
    if im_input_voltage is None:
        rated_voltage_phase = nameplate_voltage_line / _SQRT_3
        im_input_voltage = complex(rated_voltage_phase, 0.0)
    if im_input_current is None:
        rated_current_phase = nameplate_current_line
        im_input_current = complex(rated_current_phase, 0.0)
    if cable_input_phase_power is None:
        cable_input_phase_power = (
            im_output_power + im_total_loss_power + cable_total_loss_power
        )

    model = ItmModelDto(
        array_layout=_build_array_layout(),
        im=_build_im_model(
            nameplate_voltage_line=nameplate_voltage_line,
            nameplate_current_line=nameplate_current_line,
            connection_type=connection_type,
        ),
        cable=_build_cable_model(),
        system=_build_system_model(),
    )

    power = (
        ItmPowerDto(
            im_power=_build_im_power(
                output_power=im_output_power,
                total_loss_power=im_total_loss_power,
            ),
            cable_power=_build_cable_power(
                input_phase_power=cable_input_phase_power,
                total_loss_power=cable_total_loss_power,
            ),
        )
        if with_power
        else None
    )

    simulation_result = ItmSimulationDto(
        voltage_current=ItmVoltageCurrentDto(
            im_voltage_current=_build_im_voltage_current(
                im_input_voltage=im_input_voltage,
                im_input_current=im_input_current,
            ),
            cable_voltage_current=_build_cable_voltage_current(),
        ),
        power=power,
    )

    return ItmDto(
        name=ImCableSystemName(base="test_system"),
        model=model,
        simulation_result=simulation_result,
    )


class _ConfigValidationOverride:
    """``validation_config`` だけを差し替える ``IConfig`` 委譲プロキシ。

    テストで severity / enabled を YAML を編集せずに切り替えるために用いる。
    ``validation_config`` 以外の属性・メソッドは元の config に委譲する。
    """

    def __init__(
        self,
        base: IConfig,
        validation_config: ValidationConfig,
    ) -> None:
        """インスタンスを初期化する。

        Args:
            base: 元の設定オブジェクト。
            validation_config: 差し替える検証設定。
        """
        self._base: IConfig = base
        self._validation_config: ValidationConfig = validation_config

    @property
    def validation_config(self) -> ValidationConfig:
        """差し替えた検証設定を返す。"""
        return self._validation_config

    def __getattr__(self, name: str) -> object:
        """``validation_config`` 以外の属性を元の config に委譲する。"""
        return getattr(self._base, name)


def override_validation_config(
    config: IConfig,
    *,
    energy: dict[str, object] | None = None,
    cv: dict[str, object] | None = None,
) -> IConfig:
    """検証設定（severity / enabled / tolerance）を差し替えた config を返す。

    Args:
        config: 元の設定オブジェクト。
        energy: ``energy_conservation`` に対する ``dataclasses.replace`` の
            キーワード（例: ``{"severity": Severity.WARNING}``）。
        cv: ``current_voltage_range`` に対する ``dataclasses.replace`` の
            キーワード（例: ``{"enabled": False}``）。

    Returns:
        IConfig: 差し替えた検証設定を返す委譲プロキシ。
    """
    validation_config = config.validation_config
    energy_config = validation_config.energy_conservation
    cv_config = validation_config.current_voltage_range
    if energy:
        energy_config = replace(energy_config, **cast(Any, energy))
    if cv:
        cv_config = replace(cv_config, **cast(Any, cv))
    new_validation_config = replace(
        validation_config,
        energy_conservation=energy_config,
        current_voltage_range=cv_config,
    )
    return cast(
        IConfig,
        _ConfigValidationOverride(
            base=config,
            validation_config=new_validation_config,
        ),
    )
