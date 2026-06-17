"""ケーブル状態判定ロジック（ドメイン層）。

このモジュールは、ケーブル DTO に対する **bool 述語** を提供する。

提供する述語:
    - ``check_all_ground_insulated``: 全セクションが完全絶縁か。
    - ``check_any_ground_shorted``: いずれかのセクションが地絡しているか。
    - ``check_all_conductor_ideal``: 全セクションの導体が理想的か。
    - ``has_current_dependent_conductor_model``:
      ケーブル導体モデルが電流依存型か。

特徴:
    - 入力・出力にはDTO（特に`common`層のDTO）を用いる
    - アルゴリズム層から利用される純粋判定ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    ConductorModelType,
)

# 電流値によってイミタンスが変化するケーブル導体モデルタイプ。
_CURRENT_DEPENDENT_CABLE_CONDUCTOR_MODEL_TYPES: frozenset[
    ConductorModelType
] = frozenset(
    {
        ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
    }
)


def check_all_ground_insulated(
    cable_dto: CableDto,
    *,
    max_mag: float,
) -> bool:
    """全てのケーブルが完全絶縁されているか判定する。

    全てのセクションで ground_resistance_length = inf または max_mag以上 かつ
    ground_capacitance_per_length = 0 の場合にTrueを返す。

    Args:
        cable_dto: ケーブルDTO。
        max_mag: 極大ガードのしきい値（キーワード必須）。アルゴリズム層が
            Config の ``numerical_guard_config`` から ``1 / eps`` を注入する。
            Domain 側で既定値を持たない。

    Returns:
        bool: 全てのケーブルが完全絶縁されている場合True。
    """
    for section in cable_dto.sections.get_all():
        series_dto = section.series
        if series_dto is None:
            raise ValueError(
                "CableSeriesDto is not embedded in cable_dto.sections[]. "
                "Please set CableSectionDto.series."
            )

        # 抵抗長積を基本単位に変換
        resistance_length_base = (
            series_dto.ground_resistance_length.to_base_unit().value
        )

        # キャパシタンス線密度を基本単位に変換
        capacitance_per_length_base = (
            series_dto.ground_capacitance_per_length.to_base_unit().value
        )

        # 抵抗がinfでもmax_mag以上でもない、またはキャパシタンスが0でない場合はFalse
        if (
            not (
                np.isinf(resistance_length_base)
                or resistance_length_base >= max_mag
            )
            or capacitance_per_length_base != 0.0
        ):
            return False

    return True


def check_any_ground_shorted(
    cable_dto: CableDto,
    *,
    eps: float,
) -> bool:
    """1つ以上のケーブルが地絡しているか判定する。

    1つ以上のセクションで ground_resistance_length <= eps または
    ground_capacitance_per_length = inf の場合にTrueを返す。

    Args:
        cable_dto: ケーブルDTO。
        eps: 極小ガードのしきい値（キーワード必須）。アルゴリズム層が Config の
            ``numerical_guard_config.eps`` から注入する。Domain 側で既定値を
            持たない。``abs(x) <= eps`` を地絡とみなす。

    Returns:
        bool: 1つ以上のケーブルが地絡している場合True。
    """
    for section in cable_dto.sections.get_all():
        series_dto = section.series
        if series_dto is None:
            raise ValueError(
                "CableSeriesDto is not embedded in cable_dto.sections[]. "
                "Please set CableSectionDto.series."
            )

        # 抵抗長積を基本単位に変換
        resistance_length_base = (
            series_dto.ground_resistance_length.to_base_unit().value
        )

        # キャパシタンス線密度を基本単位に変換
        capacitance_per_length_base = (
            series_dto.ground_capacitance_per_length.to_base_unit().value
        )

        # 抵抗がeps以下、またはキャパシタンスが無限大の場合はTrue
        if resistance_length_base <= eps or np.isinf(
            capacitance_per_length_base
        ):
            return True

    return False


def check_all_conductor_ideal(
    cable_dto: CableDto,
    *,
    eps: float,
) -> bool:
    """全てのケーブルの導体が理想的か判定する。

    全てのセクションで conductor_inductance_per_length <= eps かつ
    conductor_resistance_per_length <= eps の場合にTrueを返す。

    Args:
        cable_dto: ケーブルDTO。
        eps: 極小ガードのしきい値（キーワード必須）。アルゴリズム層が Config の
            ``numerical_guard_config.eps`` から注入する。Domain 側で既定値を
            持たない。``abs(x) <= eps`` を理想（無視できる）とみなす。

    Returns:
        bool: 全てのケーブルの導体が理想的な場合True。
    """
    for section in cable_dto.sections.get_all():
        series_dto = section.series
        if series_dto is None:
            raise ValueError(
                "CableSeriesDto is not embedded in cable_dto.sections[]. "
                "Please set CableSectionDto.series."
            )

        # インダクタンス線密度を基本単位に変換
        inductance_per_length_base = (
            series_dto.conductor_inductance_per_length.to_base_unit().value
        )

        # 抵抗線密度を基本単位に変換
        resistance_per_length_base = (
            series_dto.conductor_resistance_per_length.to_base_unit().value
        )

        # インダクタンスがepsより大きい、または抵抗がepsより大きい場合はFalse
        if inductance_per_length_base > eps or resistance_per_length_base > eps:
            return False

    return True


def has_current_dependent_conductor_model(
    cable_dto: CableDto,
) -> bool:
    """ケーブル導体モデルが電流依存型か判定する。

    どの実行パス（Direct / Iteration 等）を選ぶかは判定しない。
    実行パス選択はアルゴリズム層の責務とする。

    Args:
        cable_dto: ケーブルDTO。

    Returns:
        bool: 導体モデルが電流依存型の場合True。
    """
    return (
        cable_dto.conductor_model.name
        in _CURRENT_DEPENDENT_CABLE_CONDUCTOR_MODEL_TYPES
    )
