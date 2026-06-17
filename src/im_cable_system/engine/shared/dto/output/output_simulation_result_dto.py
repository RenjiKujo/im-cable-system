"""出力に必要なシミュレーション結果の生量 DTO（generic のみ依存）。

NOTE: 本 DTO は出力（図表・表）に必要な物理量だけを ``generic.physical_quantity``
    の値オブジェクトで保持する。``itm`` ステージの ``ItmSimulationDto`` を直接は
    抱えず、出力公開契約を itm 内部構造から切り離す。
    力率（PF）・電流の大きさ（|I|）・出力比などの **派生量は持たず**、
    図表／表ビルダーが本 DTO から計算する（図表専用属性は作らない方針）。
    値は SI 基本単位（Execute 層の規約）を前提とする。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayEfficiencyDto,
    ArrayRotationalSpeedDto,
    ArrayTorqueDto,
)


@dataclass(frozen=True)
class OutputSimulationResultDto:
    """出力用に抽出したシミュレーション結果の生量。

    配列形状は ``OutputDto.array_layout`` の参照軸ブロードキャスト形状に一致する。
    本 DTO は「完全に計算済み（電力・特性値あり）」の結果を表す。電流電圧のみ
    計算したケースでは本 DTO を生成しない（生成側がガードする）。

    Attributes:
        output_power: IM 出力電力（3相合計複素電力）[VA]。Pout は実部、
            出力比はこの実部を定格電力で割って算出する。
        cable_input_phase_power: ケーブル入力点の相電力（3相合計複素電力）[VA]。
            力率は :math:`\\mathrm{Re}(S)/|S|` で算出する。
        input_line_current: ケーブル入力線電流（複素）[A]。
            |I_line| は大きさ、電流比は定格電流で割って算出する。
        system_efficiency: システム効率 [-]（ケーブル入力→IM 出力）。
        torque: IM トルク [N·m]。
        rotational_speed: 回転速度 [rpm]。出力では rpm に統一する
            （他量は SI 基本単位）。convert ステップで rpm へ換算済み。
    """

    output_power: ArrayComplexPowerDto
    cable_input_phase_power: ArrayComplexPowerDto
    input_line_current: ArrayComplexCurrentDto
    system_efficiency: ArrayEfficiencyDto
    torque: ArrayTorqueDto
    rotational_speed: ArrayRotationalSpeedDto
