"""誘導電動機（IM）のモデルDTO。

## 重要な設計前提

このモジュールで定義される全てのイミタンス（インピーダンス・アドミタンス）は、
**スター結線の1相換算値**として定義されています。

具体的には：
- `ItmImModelDto`: 誘導電動機のイミタンスは、結線方法（スター/デルタ）に関わらず、
  スター結線の1相換算値として保持されます。
- `ItmCableImmittanceDto`: ケーブルのイミタンスは、π型回路モデルにおける
  相モデル（スター結線の1相換算）として表現されます。
- `ItmSystemModelDto`: システム全体のイミタンスは、誘導電動機とケーブルを統合した
  位相インピーダンス・アドミタンス（スター結線の1相換算）として保持されます。

この設計により、電圧・電流の計算は常にスター結線の1相換算で行われるため、
線間電圧から相電圧への変換は常にスター結線の変換式を使用します。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDtos,
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImExcitationModelDto,
    ImName,
    ImPoles,
    ImPrimaryModelDto,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSeriesName,
    expected_branch_keys_for_cage_multiplicity,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)


# NOTE: グループ1: 基本情報DTO
@dataclass(frozen=True)
class ItmImBasicDto:
    """誘導電動機の基本情報DTO（グループ1）

    モーターの定格情報を保持する。

    Attributes:
        series_name (ImSeriesName): 誘導電動機シリーズ名。
        poles (ImPoles): 極数。
        nameplate_voltage (FloatVoltageDto): 定格電圧[V]。
        nameplate_current (FloatCurrentDto): 定格電流[A]。
        nameplate_power (FloatActivePowerDto): 定格電力[W]。
        nameplate_frequency (FloatFrequencyDto): 定格周波数[Hz]。
    """

    series_name: ImSeriesName
    poles: ImPoles
    nameplate_voltage: FloatVoltageDto
    nameplate_current: FloatCurrentDto
    nameplate_power: FloatActivePowerDto
    nameplate_frequency: FloatFrequencyDto


# NOTE: グループ2: 回路情報DTO
@dataclass(frozen=True)
class ItmImCircuitDto:
    """誘導電動機の回路情報DTO（グループ2）

    回路の接続方法とタイプを保持する。

    Attributes:
        connection_type (ImConnectionType): 結線方式（DELTA/STAR）。
        circuit_type (ImCircuitType): 回路タイプ（T/L）。
    """

    connection_type: ImConnectionType
    circuit_type: ImCircuitType


# NOTE: グループ3: 一次側モデルDTO
@dataclass(frozen=True)
class ItmImPrimaryDto:
    """一次側モデル情報DTO（グループ3）

    一次側の回路モデル（タイプとパラメータ）、計算結果を保持する。

    Attributes:
        model (ImPrimaryModelDto): 一次側回路モデル（モデルタイプとパラメータを含む）。
        resistance (FloatResistanceDto): InputDto 由来の一次抵抗 [Ω]。
            build_model が入力値をそのまま保持する。
        inductance (FloatInductanceDto): InputDto 由来の一次インダクタンス [H]。
            build_model が入力値をそのまま保持する。
        impedance (ArrayComplexImpedanceDto): 計算結果のインピーダンス [Ω]。
        admittance (ArrayComplexAdmittanceDto): 計算結果のアドミタンス [S]。
        params (FloatParamDtos | None): モデルタイプに応じたパラメータ。
            `get_by_name()`でパラメータ名をキーとしてアクセス可能。
    """

    model: ImPrimaryModelDto
    resistance: FloatResistanceDto
    inductance: FloatInductanceDto
    impedance: ArrayComplexImpedanceDto
    admittance: ArrayComplexAdmittanceDto
    params: FloatParamDtos | None = None


# NOTE: グループ4: 励磁モデルDTO
@dataclass(frozen=True)
class ItmImExcitationDto:
    """励磁モデル情報DTO（グループ4）

    励磁回路のモデル（タイプとパラメータ）、計算結果を保持する。

    Attributes:
        model (ImExcitationModelDto): 励磁回路モデル（モデルタイプとパラメータを含む）。
        resistance (FloatResistanceDto): InputDto 由来の励磁抵抗 [Ω]。
            build_model が入力値をそのまま保持する。
        inductance (FloatInductanceDto): InputDto 由来の励磁インダクタンス [H]。
            build_model が入力値をそのまま保持する。
        impedance (ArrayComplexImpedanceDto): 計算結果のインピーダンス [Ω]。
        admittance (ArrayComplexAdmittanceDto): 計算結果のアドミタンス [S]。
        params (FloatParamDtos | None): モデルタイプに応じたパラメータ。
            `get_by_name()`でパラメータ名をキーとしてアクセス可能。
    """

    model: ImExcitationModelDto
    resistance: FloatResistanceDto
    inductance: FloatInductanceDto
    impedance: ArrayComplexImpedanceDto
    admittance: ArrayComplexAdmittanceDto
    params: FloatParamDtos | None = None


# NOTE: グループ5: 二次側モデルDTO
@dataclass(frozen=True)
class ItmImSecondaryDto:
    """二次側モデル情報DTO（グループ5）

    二次側のモデルタイプ、パラメータ、計算結果を
    :class:`ImSecondaryCageBranchType` をキーとする辞書で保持する。
    :attr:`cage_multiplicity` と辞書キー集合は :func:`expected_branch_keys_for_cage_multiplicity`
    の**部分集合**で整合する必要がある。二重かごでは枝ごとの変換結果は INNER または
    OUTER のいずれか一方のキーのみを持ち得る（マージ後に両方を含む完全形となる）。

    Attributes:
        cage_multiplicity (ImCageMultiplicityType): かごの重数（単一／二重）。
        resistances (dict): InputDto 由来の枝ごとの二次抵抗 [Ω]。
            build_model が入力値をそのまま保持する。
        inductances (dict): InputDto 由来の枝ごとの二次インダクタンス [H]。
            build_model が入力値をそのまま保持する。
        models (dict): 枝ごとの二次回路モデル。
        impedances (dict): 枝ごとの計算結果インピーダンス [Ω]。
        admittances (dict): 枝ごとの計算結果アドミタンス [S]。
        base_impedances (dict): 枝ごとの基本インピーダンス [Ω]。
        base_admittances (dict): 枝ごとの基本アドミタンス [S]。
        load_impedances (dict): 枝ごとの負荷依存インピーダンス [Ω]。
        load_admittances (dict): 枝ごとの負荷依存アドミタンス [S]。
    """

    cage_multiplicity: ImCageMultiplicityType
    resistances: dict[ImSecondaryCageBranchType, FloatResistanceDto]
    inductances: dict[ImSecondaryCageBranchType, FloatInductanceDto]
    models: dict[ImSecondaryCageBranchType, ImSecondaryModelDto]
    impedances: dict[ImSecondaryCageBranchType, ArrayComplexImpedanceDto]
    admittances: dict[ImSecondaryCageBranchType, ArrayComplexAdmittanceDto]
    base_impedances: dict[ImSecondaryCageBranchType, ArrayComplexImpedanceDto]
    base_admittances: dict[ImSecondaryCageBranchType, ArrayComplexAdmittanceDto]
    load_impedances: dict[ImSecondaryCageBranchType, ArrayComplexImpedanceDto]
    load_admittances: dict[ImSecondaryCageBranchType, ArrayComplexAdmittanceDto]

    def __post_init__(self) -> None:
        """辞書キーが cage_multiplicity に対し許容される部分集合か検証する。

        各辞書は空でなく、キーは当該重数で許容される枝キー集合の部分集合でなければ
        ならない（二重かごの枝単位計算では 1 キーのみの辞書を許す）。

        Raises:
            ValueError: 空辞書、または許容されない枝キーが含まれる場合。
        """
        expected = expected_branch_keys_for_cage_multiplicity(
            self.cage_multiplicity
        )
        for label, branch_map in (
            ("models", self.models),
            ("impedances", self.impedances),
            ("admittances", self.admittances),
            ("base_impedances", self.base_impedances),
            ("base_admittances", self.base_admittances),
            ("load_impedances", self.load_impedances),
            ("load_admittances", self.load_admittances),
        ):
            keys = frozenset(branch_map.keys())
            if not keys:
                raise ValueError(
                    f"{label} は空であってはなりません。"
                    f" cage_multiplicity={self.cage_multiplicity!s}"
                )
            if not keys <= expected:
                raise ValueError(
                    f"{label} のキーが cage_multiplicity={self.cage_multiplicity!s} "
                    "に対し不正です。"
                    f" 許容される枝キーの集合: {sorted(b.value for b in expected)}, "
                    f"実際: {sorted(b.value for b in keys)}"
                )


# NOTE: グループ6: 全範囲モデルDTO
@dataclass(frozen=True)
class ItmImTotalDto:
    """全範囲モデル情報DTO（グループ6）

    全範囲の計算結果を保持する。

    Attributes:
        impedance (ArrayComplexImpedanceDto): 全範囲インピーダンス [Ω]。
        admittance (ArrayComplexAdmittanceDto): 全範囲アドミタンス [S]。
    """

    impedance: ArrayComplexImpedanceDto
    admittance: ArrayComplexAdmittanceDto


# 統合DTO
@dataclass(frozen=True)
class ItmImModelDto:
    """誘導電動機のモデルDTO（単一かご／二重かごの入力に対応する二次辞書形状）。

    各グループごとのDTOをコンポジションで保持する。
    二次側イミタンスは :attr:`secondary_model` の枝辞書で参照する（例:
    ``secondary_model.impedances[ImSecondaryCageBranchType.SINGLE]``）。

    結線方法が何であれ、スター結線の一相に換算した値を保持する。

    スリップと周波数はItmArrayShapeDtoで管理する。とくにスリップはモーターに関する属性ではあるが、
    IM＋ケーブル系シミュレーションの計算条件全体に影響するため、ItmArrayShapeDtoで管理する。

    期待する配列形状（重要）:
        本DTOが保持する「arrayを期待するDTO」の value は、すべて
        2次元配列であること。行は slip、列は frequency を表す
        形状（shape: [num_slips, num_frequencies]）とする。

    Attributes:
        name (ImName): InputDto 由来の個体名（SINGLE/UPPER/LOWER 等）。
            build_model が ImDto.name をそのまま保持する。
        basic_info (ItmImBasicDto): 基本情報（グループ1）。
        circuit_info (ItmImCircuitDto): 回路情報（グループ2）。
        primary_model (ItmImPrimaryDto): 一次側モデル情報（グループ3）。
        excitation_model (ItmImExcitationDto): 励磁モデル情報（グループ4）。
        secondary_model (ItmImSecondaryDto): 二次側モデル情報（グループ5）。
        total_model (ItmImTotalDto): 全範囲モデル情報（グループ6）。
    """

    name: ImName
    basic_info: ItmImBasicDto
    circuit_info: ItmImCircuitDto
    primary_model: ItmImPrimaryDto
    excitation_model: ItmImExcitationDto
    secondary_model: ItmImSecondaryDto
    total_model: ItmImTotalDto

    @property
    def poles(self) -> ImPoles:
        """極数を取得"""
        return self.basic_info.poles

    @property
    def nameplate_voltage(self) -> FloatVoltageDto:
        """定格電圧を取得"""
        return self.basic_info.nameplate_voltage

    @property
    def nameplate_current(self) -> FloatCurrentDto:
        """定格電流を取得"""
        return self.basic_info.nameplate_current

    @property
    def nameplate_power(self) -> FloatActivePowerDto:
        """定格電力を取得"""
        return self.basic_info.nameplate_power

    @property
    def nameplate_frequency(self) -> FloatFrequencyDto:
        """定格周波数を取得"""
        return self.basic_info.nameplate_frequency

    @property
    def connection_type(self) -> ImConnectionType:
        """結線方式を取得"""
        return self.circuit_info.connection_type

    @property
    def circuit_type(self) -> ImCircuitType:
        """回路タイプを取得"""
        return self.circuit_info.circuit_type

    @property
    def primary_impedance(self) -> ArrayComplexImpedanceDto:
        """一次側インピーダンスを取得"""
        return self.primary_model.impedance

    @property
    def primary_admittance(self) -> ArrayComplexAdmittanceDto:
        """一次側アドミタンスを取得"""
        return self.primary_model.admittance

    @property
    def excitation_impedance(self) -> ArrayComplexImpedanceDto:
        """励磁回路インピーダンスを取得"""
        return self.excitation_model.impedance

    @property
    def excitation_admittance(self) -> ArrayComplexAdmittanceDto:
        """励磁回路アドミタンスを取得"""
        return self.excitation_model.admittance

    @property
    def secondary_impedances(
        self,
    ) -> dict[ImSecondaryCageBranchType, ArrayComplexImpedanceDto]:
        """二次側インピーダンス辞書を取得"""
        return self.secondary_model.impedances

    @property
    def secondary_admittances(
        self,
    ) -> dict[ImSecondaryCageBranchType, ArrayComplexAdmittanceDto]:
        """二次側アドミタンス辞書を取得"""
        return self.secondary_model.admittances

    @property
    def total_impedance(self) -> ArrayComplexImpedanceDto:
        """全範囲インピーダンスを取得"""
        return self.total_model.impedance

    @property
    def total_admittance(self) -> ArrayComplexAdmittanceDto:
        """全範囲アドミタンスを取得"""
        return self.total_model.admittance
