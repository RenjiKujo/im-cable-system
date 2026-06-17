"""誘導電動機状態判定ロジック（ドメイン層）。

このモジュールは、誘導電動機 DTO に対する **bool 述語** を提供する。

提供する述語:
    - ``is_delta`` / ``is_star``: 結線方式（DELTA / STAR）判定。
    - ``has_current_dependent_immittance_model``:
      一次・励磁・二次モデルに電流依存型が含まれるかの判定。

特徴:
    - 入力にはドメイン共通の DTO（``ImDto``）を用いる。
    - ``im_dto.im_series`` が埋め込まれている前提（既存述語と同じ方針）。
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImConnectionType,
    ImDto,
    ImExcitationModelType,
    ImPrimaryModelType,
    ImSecondaryModelType,
)

# 電流値によってイミタンスが変化する IM 回路モデルタイプ。
# 一次・励磁・二次のどれか一つでも該当すれば「電流依存あり」と判定する。
_CURRENT_DEPENDENT_IM_IMMITTANCE_MODEL_TYPES: frozenset[
    ImSecondaryModelType | ImPrimaryModelType | ImExcitationModelType
] = frozenset(
    {
        ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
        ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1,
        ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1,
        ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1,
        ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1,
    }
)


def is_delta(
    im_dto: ImDto,
) -> bool:
    """デルタ結線かどうかを判定する。

    Args:
        im_dto: 誘導電動機DTO。

    Returns:
        bool: デルタ結線の場合True、スター結線の場合False。
    """
    return im_dto.im_series.connection_type == ImConnectionType.DELTA


def is_star(
    im_dto: ImDto,
) -> bool:
    """スター結線かどうかを判定する。

    Args:
        im_dto: 誘導電動機DTO。

    Returns:
        bool: スター結線の場合True、デルタ結線の場合False。
    """
    return im_dto.im_series.connection_type == ImConnectionType.STAR


def has_current_dependent_immittance_model(
    im_dto: ImDto,
) -> bool:
    """誘導電動機のイミタンスモデルに電流依存型が含まれるか判定する。

    一次・励磁・二次（複数ブランチ含む）のいずれかのイミタンスモデルが
    電流依存型であれば True を返す。
    どの実行パス（Direct / Iteration 等）を選ぶかは判定しない。
    実行パス選択はアルゴリズム層の責務とする。

    Args:
        im_dto: 誘導電動機DTO。``im_series`` が埋め込まれている前提。

    Returns:
        bool: 一次・励磁・二次のいずれかが電流依存型の場合True。
    """
    im_series = im_dto.im_series
    if (
        im_series.primary_model.name
        in _CURRENT_DEPENDENT_IM_IMMITTANCE_MODEL_TYPES
    ):
        return True
    if (
        im_series.excitation_model.name
        in _CURRENT_DEPENDENT_IM_IMMITTANCE_MODEL_TYPES
    ):
        return True
    for secondary_model in im_series.secondary_models.values():
        if secondary_model.name in _CURRENT_DEPENDENT_IM_IMMITTANCE_MODEL_TYPES:
            return True
    return False
