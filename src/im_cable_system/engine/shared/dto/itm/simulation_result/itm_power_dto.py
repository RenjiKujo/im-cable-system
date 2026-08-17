"""電力シミュレーション結果DTOクラス。

このモジュールは、IM＋ケーブル系シミュレーションにおける各電力の種類と
その値を保持するDTOを定義します。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    PieCableConductorKey,
    PieCableGroundKey,
    expected_branch_keys_for_cage_multiplicity,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)


@dataclass(frozen=True)
class ItmImPowerDto:
    """IM各電力の種類とその値のDTO。

    シミュレーション計算で得られたIMの各電力の種類とその値を保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。
    電力は`ArrayComplexPowerDto`として**3相合計の複素電力**（$S_{total}$）を保持します。
    相量（スター等価）ベースでも線量ベースでも計算でき、以下が等価です：
    - $S_{total} = 3 \\, V_{\\phi} \\, I_{\\phi}^{*}$
    - $S_{total} = \\sqrt{3} \\, V_{LL} \\, I_{L}^{*}$

    NOTE: 上記2式（相量ベースと線量ベース）が複素数として一致するのは、
        平衡三相かつ線間電圧と相電圧が位相30度の整合関係にある場合に限る。
        入力の位相規約が異なると、複素値（特に力率）は一致しない。

    `ItmImModelDto`のインピーダンス・アドミタンスに対応する電力構造で保持します。

    Attributes:
        input_power (ArrayComplexPowerDto): IM入力電力[VA]。
        primary_loss_power (ArrayComplexPowerDto): IM一次側損失電力[VA]。
            `ItmImModelDto`の`primary_impedance`に対応する。
        excitation_loss_power (ArrayComplexPowerDto): IM励磁回路損失電力[VA]（鉄損）。
            `ItmImModelDto`の`excitation_impedance`に対応する。
        cage_multiplicity (ImCageMultiplicityType): かごの重数（単一／二重）。
        secondary_base_loss_power (dict[ImSecondaryCageBranchType, ArrayComplexPowerDto]):
            IM二次側基本損失電力[VA]（枝ごと）。
        secondary_load_power (dict[ImSecondaryCageBranchType, ArrayComplexPowerDto]):
            IM二次側負荷電力[VA]（枝ごと。軸出力控除を引く前の内部機械出力）。
        secondary_branch_total_power (dict[ImSecondaryCageBranchType, ArrayComplexPowerDto]):
            IM二次側（base+load の直列枝）合計電力[VA]（枝ごと）。
        secondary_total_power (ArrayComplexPowerDto):
            二次側合計電力[VA]（枝電流合計と二次電圧で計算した合計）。
        friction_windage_loss_power (ArrayComplexPowerDto): 摩擦・風損[VA]。
            虚部は常に 0（有効電力のみ）。`ImFrictionWindageModelDto` が
            `NONE` のときはゼロ配列。`ImSeriesDto.nameplate_power`
            （3相合計）基準で計算するため、この量だけ「1相で計算して3相へ
            変換」の経路を通らない。
        stray_load_loss_power (ArrayComplexPowerDto): 漂遊負荷損[VA]。
            虚部は常に 0（有効電力のみ）。`ImStrayLoadModelDto` が `NONE`
            のときはゼロ配列。基準の扱いは `friction_windage_loss_power`
            と同じ。
        output_power (ArrayComplexPowerDto): 特性値計算で参照するIM正規出力電力[VA]。
            目的: 単かご/多重かご等のモデル差を **電力計算段で吸収**し、特性値計算では
            `output_power` のみを参照して一律にトルク・効率を計算できるようにする。
            定義: `sum(secondary_load_power.values()) − friction_windage_loss_power
            − stray_load_loss_power`（軸出力。実部のみ減算）。両損失が `NONE`
            のときは従来どおり `sum(secondary_load_power.values())` と一致する。
        total_loss_power (ArrayComplexPowerDto): IM全体損失電力[VA]。
            一次銅損・二次銅損・鉄損に加え、`friction_windage_loss_power` と
            `stray_load_loss_power` を含む。
        copper_loss_power (ArrayComplexPowerDto): IM銅損電力[VA]。
        iron_loss_power (ArrayComplexPowerDto): IM鉄損電力[VA]。
    """

    input_power: ArrayComplexPowerDto
    primary_loss_power: ArrayComplexPowerDto
    excitation_loss_power: ArrayComplexPowerDto

    cage_multiplicity: ImCageMultiplicityType
    secondary_base_loss_power: dict[
        ImSecondaryCageBranchType, ArrayComplexPowerDto
    ]
    secondary_load_power: dict[ImSecondaryCageBranchType, ArrayComplexPowerDto]
    secondary_branch_total_power: dict[
        ImSecondaryCageBranchType, ArrayComplexPowerDto
    ]
    secondary_total_power: ArrayComplexPowerDto

    friction_windage_loss_power: ArrayComplexPowerDto
    stray_load_loss_power: ArrayComplexPowerDto

    output_power: ArrayComplexPowerDto
    total_loss_power: ArrayComplexPowerDto
    copper_loss_power: ArrayComplexPowerDto
    iron_loss_power: ArrayComplexPowerDto

    def __post_init__(self) -> None:
        """二次辞書のキーが cage_multiplicity と一致することを検証する。

        Raises:
            ValueError: 期待する枝キー集合と一致しない場合。
        """
        expected = expected_branch_keys_for_cage_multiplicity(
            self.cage_multiplicity
        )
        for label, branch_map in (
            ("secondary_base_loss_power", self.secondary_base_loss_power),
            ("secondary_load_power", self.secondary_load_power),
            ("secondary_branch_total_power", self.secondary_branch_total_power),
        ):
            keys = frozenset(branch_map.keys())
            if keys != expected:
                raise ValueError(
                    f"{label} のキーが cage_multiplicity={self.cage_multiplicity!s} "
                    "に対し不正です。"
                    f" 期待: {sorted(b.value for b in expected)}, "
                    f"実際: {sorted(b.value for b in keys)}"
                )


@dataclass(frozen=True)
class ItmCablePowerDto:
    """ケーブル各電力の種類とその値のDTO。

    シミュレーション計算で得られたケーブルの各電力の種類とその値を保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。
    電力は`ArrayComplexPowerDto`として**3相合計の複素電力**（$S_{total}$）を保持します。
    相量（スター等価）ベースでも線量ベースでも計算でき、以下が等価です：
    - $S_{total} = 3 \\, V_{\\phi} \\, I_{\\phi}^{*}$
    - $S_{total} = \\sqrt{3} \\, V_{LL} \\, I_{L}^{*}$

    NOTE: 上記2式（相量ベースと線量ベース）が複素数として一致するのは、
        平衡三相かつ線間電圧と相電圧が位相30度の整合関係にある場合に限る。
        入力の位相規約が異なると、複素値（特に力率）は一致しない。

    `ItmCableImmittanceDto`と同じデータ構造（dict形式）で保持します。
    ケーブルは常に π 型等価回路を想定する。

    Attributes:
        system_total_input_power (ArrayComplexPowerDto): システム全体入力電力[VA]。
            入力線間電圧・線電流（線側の量）から計算した3相合計複素電力。
            スター結線の規約（線間電圧フェーザが相電圧フェーザより +30° 進む）
            による位相回転を打ち消す補正（e^{-jπ/6}）を施してあり、相量
            （スター等価）基準の `input_phase_power` と複素値が一致する。
            これにより有効電力・無効電力（力率）の分解が相量ベースと整合する。
        input_phase_power (ArrayComplexPowerDto): 入力点（相量/スター等価）で計算した3相合計電力[VA]。
        conductor_loss_power (dict[PieCableConductorKey, ArrayComplexPowerDto]):
            導線の損失電力の辞書。π型回路の場合、以下のキーを持つ:
                - PieCableConductorKey.SINGLE: 導線の損失電力 [VA]。
                    `ItmCableImmittanceDto`の`conductor_impedance`に対応する。
        ground_loss_power (dict[PieCableGroundKey, ArrayComplexPowerDto]):
            アース接続の損失電力の辞書。π型回路の場合、以下のキーを持つ:
                - PieCableGroundKey.UPSTREAM: 上流側アース損失電力 [VA]。
                    `ItmCableImmittanceDto`の`ground_admittance[PieCableGroundKey.UPSTREAM]`に対応する。
                - PieCableGroundKey.DOWNSTREAM: 下流側アース損失電力 [VA]。
                    `ItmCableImmittanceDto`の`ground_admittance[PieCableGroundKey.DOWNSTREAM]`に対応する。
        end_point_phase_power (ArrayComplexPowerDto): 終点（相量/スター等価）で計算した3相合計電力[VA]。
            IMの入力電力計算にも使用される。
        total_loss_power (ArrayComplexPowerDto): ケーブル全体損失電力[VA]。
    """

    system_total_input_power: ArrayComplexPowerDto
    input_phase_power: ArrayComplexPowerDto
    conductor_loss_power: dict[PieCableConductorKey, ArrayComplexPowerDto]
    ground_loss_power: dict[PieCableGroundKey, ArrayComplexPowerDto]
    end_point_phase_power: ArrayComplexPowerDto
    total_loss_power: ArrayComplexPowerDto

    def __post_init__(self) -> None:
        """π型ケーブルとして損失電力辞書のキー整合性をバリデーションする。

        以下のキー構成を前提とする:

        - conductor_loss_power: keys == {PieCableConductorKey.SINGLE}
        - ground_loss_power: keys == {PieCableGroundKey.UPSTREAM, PieCableGroundKey.DOWNSTREAM}
        """
        expected_conductor_keys = frozenset({PieCableConductorKey.SINGLE})
        expected_ground_keys = frozenset(
            {PieCableGroundKey.UPSTREAM, PieCableGroundKey.DOWNSTREAM}
        )

        conductor_keys = frozenset(self.conductor_loss_power.keys())
        ground_keys = frozenset(self.ground_loss_power.keys())

        if conductor_keys != expected_conductor_keys:
            raise ValueError(
                "ケーブル（π型）の conductor_loss_power のキーが不正です: "
                f"{conductor_keys}. 期待値: {expected_conductor_keys}"
            )
        if ground_keys != expected_ground_keys:
            raise ValueError(
                "ケーブル（π型）の ground_loss_power のキーが不正です: "
                f"{ground_keys}. 期待値: {expected_ground_keys}"
            )


@dataclass(frozen=True)
class ItmPowerDto:
    """電力シミュレーション結果DTO。

    シミュレーション計算で得られた電力（IM電力、ケーブル電力）を保持します。
    ここで保持する電力は、いずれも**3相合計の複素電力**（$S_{total}$）です。

    Attributes:
        im_power (ItmImPowerDto): IM各電力のDTO。
        cable_power (ItmCablePowerDto): ケーブル各電力のDTO。
            ケーブルが存在しない場合でも、擬似ケーブルモデルが作成されるため、常に存在する。
    """

    im_power: ItmImPowerDto
    cable_power: ItmCablePowerDto
