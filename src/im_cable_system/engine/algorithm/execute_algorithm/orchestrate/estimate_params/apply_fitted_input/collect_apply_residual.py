"""試行ベクトルから DTO への反映（:func:`apply_fitted_params`）。

IM 記述子の列挙とケーブル記述子の連結は
``estimate_params_execution_orchestrator.execute`` 内で行う（読みやすさのため）。

IM 記述子本体の組み立ては ``collect_descriptors.im``（ストラテジ＋組み立て）、
ケーブルは :class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.CableDto` 単位（π 型＋導体モデル）。
記述子の組み立ては :mod:`collect_descriptors.im.descriptor_build` /
:mod:`collect_descriptors.cable.descriptor_build`、DTO への適用は
:mod:`descriptor_apply`。カーブ対 Itm の残差は
:mod:`support.curve_eval.curve_residual_vector`。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    ImSeriesDto,
)

from .descriptor_apply import (
    apply_cable_dto_from_descriptors,
    apply_im_from_descriptors,
)


def apply_fitted_params(
    im_series_dto: ImSeriesDto,
    cable_dto: CableDto | None,
    descriptors: list[FittableParamDescriptor],
    x: np.ndarray,
    im_descriptor_count: int,
) -> tuple[ImSeriesDto, CableDto | None]:
    """記述子とベクトル x から更新した ImSeriesDto と CableDto を返す。

    Args:
        im_series_dto: 元の IM シリーズ DTO。
        cable_dto: 元のケーブル DTO（1 セクション前提）。None の場合は None を返す。
        descriptors: ``execute`` で構築したリスト（先頭が IM、続けてケーブル。順序一致）。
        x: フィット変数ベクトル。``len(x) == len(descriptors)``。
        im_descriptor_count: IM 部記述子の個数（先頭 ``im_descriptor_count`` 個）。

    Returns:
        (更新後の ImSeriesDto, 更新後の CableDto または None)。

    Raises:
        ValueError: 長さ不整合、またはケーブル無しなのにケーブル記述子がある場合。
    """
    n = len(descriptors)
    if len(x) != n:
        raise ValueError(
            f"x の長さ {len(x)} が descriptors の長さ {n} と一致しません。"
        )
    if im_descriptor_count < 0 or im_descriptor_count > n:
        raise ValueError(
            f"im_descriptor_count={im_descriptor_count} が "
            f"descriptors 長 {n} の範囲外です。"
        )
    cable_desc = descriptors[im_descriptor_count:]
    if cable_dto is None and cable_desc:
        raise ValueError(
            "ケーブルが無いのにケーブル用の記述子が descriptors に含まれています。"
        )

    im_desc = descriptors[:im_descriptor_count]
    x_im = x[:im_descriptor_count]
    new_im = apply_im_from_descriptors(im_series_dto, im_desc, x_im)

    if cable_dto is None:
        return new_im, None

    x_cable = x[im_descriptor_count:]
    new_cable = apply_cable_dto_from_descriptors(
        cable_dto,
        cable_desc,
        x_cable,
    )
    return new_im, new_cable
