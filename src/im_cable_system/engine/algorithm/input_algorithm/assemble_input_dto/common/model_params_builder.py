"""モデルパラメータ辞書と FloatParamDtos の変換（Forward / EstimateParams 共通）。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
)


def float_param_dtos_from_dict(
    params: dict[str, float] | None,
) -> FloatParamDtos | None:
    """``{name: value}`` 辞書を :class:`FloatParamDtos` に変換する。

    Args:
        params: パラメータ辞書。空または None のときは None。

    Returns:
        FloatParamDtos | None: 変換結果。
    """
    if params is None or len(params) == 0:
        return None
    objects = [
        FloatParamDto(name=name, value=value) for name, value in params.items()
    ]
    return FloatParamDtos(objects=objects)
