"""電圧・電流シミュレーション結果DTOクラス。

このモジュールは、IM＋ケーブル系シミュレーションにおける各地点の電圧・電流を
保持するDTOを定義します。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    PieCableConductorKey,
    PieCableGroundKey,
    expected_branch_keys_for_cage_multiplicity,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)


@dataclass(frozen=True)
class ItmImVoltageCurrentDto:
    """IM各地点の電圧・電流DTO。

    シミュレーション計算で得られたIMの各地点の電圧・電流を保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。

    位相規約（本プロジェクトの正本）:
        本エンジンの Execute ステージは「平衡三相・正相の per-phase 等価回路」
        として計算する。本DTOが保持する全ての電圧・電流は、結線（STAR/DELTA）に
        依らず常に **スター等価相量** である。

        - 線間↔相は大きさ換算のみ（相 = 線間 / √3、線電流 = 相電流）。線間と相は
          同位相として扱い、L-L / L-N の 30° 位相差は意図的に省略する
          （`line_to_phase_voltage_star_balanced` 参照）。これは教科書的な
          per-phase 等価に合わせた balanced 規約であり、平衡正相では大きさ・
          三相電力・力率が厳密値と一致する。
        - 位相角は内部基準であり、実三相の絶対位相は追わない。
        - InputDto のインピーダンスはスター結線相当の per-phase 値とみなす。
        - 実巻線相（デルタ巻線の相電圧・相電流など）や ±30° を厳密に扱う出力は、
          Output ステージで `convert_*_star_to_delta`（rotation-aware）または
          `convert_*_star_to_delta_balanced` を用いて別途算出する。
        - 不平衡三相・零相・相間結合・中性点変位は対象外。

    電流は最初から dict にはせず、属性として持たせている。属性ごとに中身が
    分かりやすく、IM の回路モデルで必ず存在する地点（一次・励磁・二次など）を
    明示するためである。一方で、インピーダンスが電流に依存して変化するモデルを
    表現するには build と simulate を反復するため、次イテレーションの build では
    ArrayLayout.arrays のデータの持ち方（軸名をキーとする dict）に合わせる必要が
    あり、get_currents_for_array_layout() で電流を dict 化して返す。

    Attributes:
        im_input_voltage (ArrayComplexVoltageDto): IM入力電圧[V]。
        im_input_current (ArrayComplexCurrentDto): IM入力電流[A]。
        im_primary_voltage (ArrayComplexVoltageDto): IM一次側電圧[V]。
        im_primary_current (ArrayComplexCurrentDto): IM一次側電流[A]。
        im_excitation_voltage (ArrayComplexVoltageDto): IM励磁回路電圧[V]。
        im_excitation_current (ArrayComplexCurrentDto): IM励磁回路電流[A]。
        cage_multiplicity (ImCageMultiplicityType): かごの重数（単一／二重）。
        secondary_base_voltage (dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto]):
            二次側ベース（R2_base 等）枝ごとの電圧降下[V]。
        secondary_load_voltage (dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto]):
            二次側ロード（R2_load 等）枝ごとの電圧降下[V]。
        secondary_branch_current (dict[ImSecondaryCageBranchType, ArrayComplexCurrentDto]):
            二次側枝（base+load の直列枝）ごとの電流[A]。
    """

    # NOTE: 以下の電圧・電流は全て「スター等価相量」（結線に依らず）。
    #   規約の詳細はクラス docstring「位相規約」を参照。
    im_input_voltage: ArrayComplexVoltageDto  # スター等価相電圧[V]
    im_input_current: ArrayComplexCurrentDto  # スター等価相電流[A]
    im_primary_voltage: ArrayComplexVoltageDto  # スター等価相電圧[V]
    im_primary_current: ArrayComplexCurrentDto  # スター等価相電流[A]
    im_excitation_voltage: ArrayComplexVoltageDto  # スター等価相電圧[V]
    im_excitation_current: ArrayComplexCurrentDto  # スター等価相電流[A]

    cage_multiplicity: ImCageMultiplicityType
    # 以下の二次側 dict も全て「スター等価相量」。
    secondary_base_voltage: dict[
        ImSecondaryCageBranchType, ArrayComplexVoltageDto
    ]
    secondary_load_voltage: dict[
        ImSecondaryCageBranchType, ArrayComplexVoltageDto
    ]
    secondary_branch_current: dict[
        ImSecondaryCageBranchType, ArrayComplexCurrentDto
    ]

    def __post_init__(self) -> None:
        """二次辞書のキーが cage_multiplicity と一致することを検証する。

        Raises:
            ValueError: 期待する枝キー集合と一致しない場合。
        """
        expected = expected_branch_keys_for_cage_multiplicity(
            self.cage_multiplicity
        )
        for label, branch_map in (
            ("secondary_base_voltage", self.secondary_base_voltage),
            ("secondary_load_voltage", self.secondary_load_voltage),
            ("secondary_branch_current", self.secondary_branch_current),
        ):
            keys = frozenset(branch_map.keys())
            if keys != expected:
                raise ValueError(
                    f"{label} のキーが cage_multiplicity={self.cage_multiplicity!s} "
                    "に対し不正です。"
                    f" 期待: {sorted(b.value for b in expected)}, "
                    f"実際: {sorted(b.value for b in keys)}"
                )

    def get_secondary_branch_voltage(
        self,
    ) -> dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto]:
        """二次側枝（base+load）の枝電圧を導出して返す。

        Returns:
            dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto]:
                枝キーごとの枝電圧[V]（base+load）。
        """
        result: dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto] = {}
        for branch in self.secondary_base_voltage:
            base_v = self.secondary_base_voltage[branch].to_base_unit()
            load_v = self.secondary_load_voltage[branch].to_base_unit()
            result[branch] = ArrayComplexVoltageDto(
                value=base_v.value + load_v.value,
                unit=base_v.get_unit(),
            )
        return result

    def get_secondary_voltage(self) -> ArrayComplexVoltageDto:
        """二次側（枝の合流点）の電圧を導出して返す。

        単一かご: 枝電圧（base+load）をそのまま返す。
        二重かご: INNER/OUTER の枝電圧が一致することを検証し、一致する電圧を返す。

        Returns:
            ArrayComplexVoltageDto: 二次側電圧[V]。

        Raises:
            ValueError: 二重かごで枝電圧が一致しない場合。
        """
        branch_v = self.get_secondary_branch_voltage()
        expected = expected_branch_keys_for_cage_multiplicity(
            self.cage_multiplicity
        )
        if expected == frozenset({ImSecondaryCageBranchType.SINGLE}):
            return branch_v[ImSecondaryCageBranchType.SINGLE]

        inner_v = branch_v[ImSecondaryCageBranchType.INNER].to_base_unit()
        outer_v = branch_v[ImSecondaryCageBranchType.OUTER].to_base_unit()
        if not np.allclose(
            inner_v.value,
            outer_v.value,
            rtol=1e-10,
            atol=1e-12,
        ):
            raise ValueError(
                "二重かごの二次枝電圧が一致しません。"
                " INNER vs OUTER (rtol=1e-10, atol=1e-12)"
            )
        return inner_v

    def get_secondary_total_current(self) -> ArrayComplexCurrentDto:
        """二次側の枝電流から合計電流を導出して返す。

        Returns:
            ArrayComplexCurrentDto: 二次側合計電流[A]（枝電流の総和）。
        """
        total: ArrayComplexCurrentDto | None = None
        for current in self.secondary_branch_current.values():
            cur = current.to_base_unit()
            total = (
                cur
                if total is None
                else ArrayComplexCurrentDto(
                    value=total.value + cur.value,
                    unit=total.get_unit(),
                )
            )
        if total is None:
            raise ValueError("secondary_branch_current が空です。")
        return total

    def get_currents_for_array_layout(
        self,
    ) -> dict[ArrayKey, ArrayComplexCurrentDto]:
        """IM の電流属性をすべて dict 化して返す。

        :class:`ArrayLayoutDto.arrays` のキー型（:class:`ArrayKey`）に合わせ、
        次イテレーションの build などで利用するための view を提供する。

        Returns:
            dict[ArrayKey, ArrayComplexCurrentDto]: 軸キーをキーとする電流DTOの辞書。
        """
        result: dict[ArrayKey, ArrayComplexCurrentDto] = {
            ArrayKey.IM_INPUT_CURRENT: self.im_input_current,
            ArrayKey.IM_PRIMARY_CURRENT: self.im_primary_current,
            ArrayKey.IM_EXCITATION_CURRENT: self.im_excitation_current,
        }
        expected = expected_branch_keys_for_cage_multiplicity(
            self.cage_multiplicity
        )
        if expected == frozenset({ImSecondaryCageBranchType.SINGLE}):
            result[ArrayKey.SINGLE_CAGE_IM_SECONDARY_CURRENT] = (
                self.secondary_branch_current[ImSecondaryCageBranchType.SINGLE]
            )
        else:
            result[ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT] = (
                self.secondary_branch_current[ImSecondaryCageBranchType.INNER]
            )
            result[ArrayKey.DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT] = (
                self.secondary_branch_current[ImSecondaryCageBranchType.OUTER]
            )
        return result


@dataclass(frozen=True)
class ItmCableVoltageCurrentDto:
    """ケーブル各地点の電圧・電流DTO。

    シミュレーション計算で得られたケーブルの各地点の電圧・電流を保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。

    電流のうち、単一のものは属性で、導体・アースなどモデルで可変なものは
    dict で保持している。最初から電流をすべて dict にしなかったのは、
    属性ごとに中身が分かりやすく、ケーブル回路モデルで必ず存在する地点
    （入力線・相・終点など）を明示するためである。一方で、インピーダンスが
    電流に依存して変化するモデルを表現するには build と simulate を反復するため、
    次イテレーションの build では ArrayLayout.arrays のデータの持ち方
    （軸名をキーとする dict）に合わせる必要があり、
    get_currents_for_array_layout() で電流を dict 化して返す。

    `ItmCableImmittanceDto`と同じデータ構造（dict形式）で保持します。
    ケーブルは常に π 型等価回路を想定する。

    Attributes:
        input_line_voltage (ArrayComplexVoltageDto): 入力線間電圧[V]。
            常に設定されます。
        input_line_current (ArrayComplexCurrentDto): 入力線間電流[A]。
            常に設定されます。
        input_phase_voltage (ArrayComplexVoltageDto): 入力相電圧[V]。
            ケーブル入力電圧と同じ（相電圧）。
        input_phase_current (ArrayComplexCurrentDto): 入力相電流[A]。
            ケーブル入力電流と同じ（相電流）。
        conductor_voltage (dict[PieCableConductorKey, ArrayComplexVoltageDto]):
            導線の電圧の辞書。π型回路の場合、以下のキーを持つ:
                - PieCableConductorKey.SINGLE: 上流と下流の間の導線（電流が流れる導体）の
                    電圧降下 [V]。`ItmCableImmittanceDto`の`conductor_impedance`に対応する。
        conductor_current (dict[PieCableConductorKey, ArrayComplexCurrentDto]):
            導線の電流の辞書。π型回路の場合、以下のキーを持つ:
                - PieCableConductorKey.SINGLE: 導線の電流 [A]。`ItmCableImmittanceDto`の`conductor_impedance`に対応する。
        ground_voltage (dict[PieCableGroundKey, ArrayComplexVoltageDto]):
            アース接続の電圧の辞書。π型回路の場合、以下のキーを持つ:
                - PieCableGroundKey.UPSTREAM: 上流側アース電圧 [V]。
                    `ItmCableImmittanceDto`の`ground_impedance[PieCableGroundKey.UPSTREAM]`に対応する。
                - PieCableGroundKey.DOWNSTREAM: 下流側アース電圧 [V]。
                    `ItmCableImmittanceDto`の`ground_impedance[PieCableGroundKey.DOWNSTREAM]`に対応する。
        ground_current (dict[PieCableGroundKey, ArrayComplexCurrentDto]):
            アース接続の電流の辞書。π型回路の場合、以下のキーを持つ:
                - PieCableGroundKey.UPSTREAM: 上流側アース電流 [A]。
                    `ItmCableImmittanceDto`の`ground_admittance[PieCableGroundKey.UPSTREAM]`に対応する。
                - PieCableGroundKey.DOWNSTREAM: 下流側アース電流 [A]。
                    `ItmCableImmittanceDto`の`ground_admittance[PieCableGroundKey.DOWNSTREAM]`に対応する。
        end_point_phase_voltage (ArrayComplexVoltageDto): 終点相電圧[V]。
            IMの入力電圧でもある。結線に依らず「スター等価相」（balanced 規約。
            線間電圧と同位相で大きさ 1/√3）。詳細は ItmImVoltageCurrentDto の
            クラス docstring「位相規約」を参照。
        end_point_phase_current (ArrayComplexCurrentDto): 終点相電流[A]。
            IMの入力電流でもある。結線に依らず「スター等価相」（balanced 規約。
            スターでは線電流に等しい）。詳細は ItmImVoltageCurrentDto の
            クラス docstring「位相規約」を参照。
    """

    input_line_voltage: ArrayComplexVoltageDto
    input_line_current: ArrayComplexCurrentDto
    input_phase_voltage: ArrayComplexVoltageDto
    input_phase_current: ArrayComplexCurrentDto
    conductor_voltage: dict[PieCableConductorKey, ArrayComplexVoltageDto]
    conductor_current: dict[PieCableConductorKey, ArrayComplexCurrentDto]
    ground_voltage: dict[PieCableGroundKey, ArrayComplexVoltageDto]
    ground_current: dict[PieCableGroundKey, ArrayComplexCurrentDto]
    end_point_phase_voltage: ArrayComplexVoltageDto
    end_point_phase_current: ArrayComplexCurrentDto

    def __post_init__(self) -> None:
        """π型ケーブルとして辞書キーの整合性をバリデーションする。

        以下のキー構成を前提とする:

        - conductor_voltage / conductor_current:
            keys == {PieCableConductorKey.SINGLE}
        - ground_voltage / ground_current:
            keys == {PieCableGroundKey.UPSTREAM, PieCableGroundKey.DOWNSTREAM}
        """
        expected_conductor_keys = frozenset({PieCableConductorKey.SINGLE})
        expected_ground_keys = frozenset(
            {PieCableGroundKey.UPSTREAM, PieCableGroundKey.DOWNSTREAM}
        )

        conductor_v_keys = frozenset(self.conductor_voltage.keys())
        conductor_i_keys = frozenset(self.conductor_current.keys())
        ground_v_keys = frozenset(self.ground_voltage.keys())
        ground_i_keys = frozenset(self.ground_current.keys())

        if conductor_v_keys != expected_conductor_keys:
            raise ValueError(
                "ケーブル（π型）の conductor_voltage のキーが不正です: "
                f"{conductor_v_keys}. 期待値: {expected_conductor_keys}"
            )
        if conductor_i_keys != expected_conductor_keys:
            raise ValueError(
                "ケーブル（π型）の conductor_current のキーが不正です: "
                f"{conductor_i_keys}. 期待値: {expected_conductor_keys}"
            )
        if ground_v_keys != expected_ground_keys:
            raise ValueError(
                "ケーブル（π型）の ground_voltage のキーが不正です: "
                f"{ground_v_keys}. 期待値: {expected_ground_keys}"
            )
        if ground_i_keys != expected_ground_keys:
            raise ValueError(
                "ケーブル（π型）の ground_current のキーが不正です: "
                f"{ground_i_keys}. 期待値: {expected_ground_keys}"
            )

    def get_currents_for_array_layout(
        self,
    ) -> dict[ArrayKey, ArrayComplexCurrentDto]:
        """ケーブルの電流属性をすべて dict 化して返す。

        :class:`ArrayLayoutDto.arrays` のキー型（:class:`ArrayKey`）に合わせ、
        次イテレーションの build などで利用するための view を提供する。

        Returns:
            dict[ArrayKey, ArrayComplexCurrentDto]: 軸キーをキーとする電流DTOの辞書。
        """
        result: dict[ArrayKey, ArrayComplexCurrentDto] = {
            ArrayKey.INPUT_LINE_CURRENT: self.input_line_current,
            ArrayKey.INPUT_PHASE_CURRENT: self.input_phase_current,
            ArrayKey.END_POINT_PHASE_CURRENT: self.end_point_phase_current,
            ArrayKey.CONDUCTOR_CURRENT_PIE_SINGLE: self.conductor_current[
                PieCableConductorKey.SINGLE
            ],
            ArrayKey.GROUND_CURRENT_PIE_UPSTREAM: self.ground_current[
                PieCableGroundKey.UPSTREAM
            ],
            ArrayKey.GROUND_CURRENT_PIE_DOWNSTREAM: self.ground_current[
                PieCableGroundKey.DOWNSTREAM
            ],
        }
        return result


@dataclass(frozen=True)
class ItmVoltageCurrentDto:
    """電圧・電流シミュレーション結果DTO。

    シミュレーション計算で得られた電圧・電流（IM電圧・電流、ケーブル電圧・電流）を保持します。

    Attributes:
        im_voltage_current (ItmImVoltageCurrentDto): IM各地点の電圧・電流DTO。
        cable_voltage_current (ItmCableVoltageCurrentDto): ケーブル各地点の電圧・電流DTO。
            ケーブルが存在しない場合でも、擬似ケーブルモデルが作成されるため、常に存在する。
    """

    im_voltage_current: ItmImVoltageCurrentDto
    cable_voltage_current: ItmCableVoltageCurrentDto
