"""estimate_params 用ロードの公開窓口。

1 つの統合 TSV を読み込み、候補軸の直積展開済みの
:class:`EstimateParamsInputLoadedData` タプルを返すローダーを公開する。
中間表現データクラス自体は :mod:`...load_data.data_class` の公開窓口で
集約しているため、ここでは再エクスポートしない。
"""

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.loader import (  # noqa: E501
    EstimateParamsLoader,
)

__all__ = [
    "EstimateParamsLoader",
]
