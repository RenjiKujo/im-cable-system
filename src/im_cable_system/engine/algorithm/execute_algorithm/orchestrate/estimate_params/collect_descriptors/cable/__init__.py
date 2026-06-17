"""ケーブルフィット記述子の組み立て。

ケーブル（1 セクション）の π 型 4 パラメータ＋導体モデル係数の記述子組み立て
関数を公開する。記述子集合の収集本体（:class:`FitDescriptorCollector`）から
利用する公開窓口。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.cable.descriptor_build import (  # noqa: E501
    collect_cable_fittable_descriptors,
)

__all__: list[str] = [
    "collect_cable_fittable_descriptors",
]
