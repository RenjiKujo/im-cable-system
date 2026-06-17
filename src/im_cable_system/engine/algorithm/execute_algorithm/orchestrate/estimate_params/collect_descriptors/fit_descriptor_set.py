"""フィット記述子の収集結果 DTO。

IM 部とケーブル部を連結した記述子列と、先頭から数えた IM 部の個数を保持する。
``apply_fitted_params`` が IM / ケーブルの区切りに ``im_count`` を用いる。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)


@dataclass(frozen=True)
class FitDescriptorSet:
    """フィット対象記述子の集合。

    Attributes:
        descriptors: フィット記述子（先頭が IM、続けてケーブルの順）。
        im_count: 先頭から数えた IM 部記述子の個数。
    """

    descriptors: list[FittableParamDescriptor]
    im_count: int
