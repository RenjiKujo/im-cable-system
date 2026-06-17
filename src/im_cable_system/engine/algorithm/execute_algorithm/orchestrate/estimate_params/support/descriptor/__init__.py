"""フィット記述子 DTO（軸2: ステップ間共有の公開窓口）。

``FittableParamDescriptor`` は estimate_params の collect → fit → apply →
summary パイプラインを横断して生成・消費される 1 スカラパラメータの記述子。
特定ステップに属さない共有データ契約のため、本 ``support`` 配下に置く。
層外・層横断・別ステップからは本窓口経由で import する。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor.fittable_param_descriptor import (  # noqa: E501
    FittableParamDescriptor,
)

__all__: list[str] = [
    "FittableParamDescriptor",
]
