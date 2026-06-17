"""特性値シミュレーション結果DTOクラス。

このモジュールは、IM＋ケーブル系シミュレーションにおける各特性値の種類と
その値を保持するDTOを定義します。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayEfficiencyDto,
    ArrayRotationalSpeedDto,
    ArrayTorqueDto,
)


@dataclass(frozen=True)
class ItmRotationalSpeedDto:
    """回転速度特性値DTO。

    シミュレーション計算で得られた回転速度を保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。

    Attributes:
        rotational_speed (ArrayRotationalSpeedDto): 回転速度配列[rad/s]。
    """

    rotational_speed: ArrayRotationalSpeedDto


@dataclass(frozen=True)
class ItmTorqueDto:
    """トルク特性値DTO。

    シミュレーション計算で得られたトルクを保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。

    Attributes:
        torque (ArrayTorqueDto): トルク配列[N·m]。
    """

    torque: ArrayTorqueDto


@dataclass(frozen=True)
class ItmEfficiencyDto:
    """効率特性値DTO。

    シミュレーション計算で得られた効率を保持します。
    配列形状は`model.array_layout`で定義された多次元配列です。

    Attributes:
        system_efficiency (ArrayEfficiencyDto): IMシステム効率[無次元]。
            地上電源入力(ケーブル入力)→IM出力。
        im_efficiency (ArrayEfficiencyDto): IM内部効率[無次元]。
            IM入力→IM出力。
        cable_efficiency (ArrayEfficiencyDto): ケーブル効率[無次元]。
            地上電源入力(ケーブル入力)→ケーブル出力。
    """

    system_efficiency: ArrayEfficiencyDto
    im_efficiency: ArrayEfficiencyDto
    cable_efficiency: ArrayEfficiencyDto


@dataclass(frozen=True)
class ItmCharacteristicDto:
    """特性値シミュレーション結果DTO。

    シミュレーション計算で得られた特性値（回転速度、トルク、効率）を保持します。

    Attributes:
        rotational_speed (ItmRotationalSpeedDto): 回転速度特性値DTO。
        torque (ItmTorqueDto): トルク特性値DTO。
        efficiency (ItmEfficiencyDto): 効率特性値DTO。
    """

    rotational_speed: ItmRotationalSpeedDto
    torque: ItmTorqueDto
    efficiency: ItmEfficiencyDto
