"""estimate_params 向け job_spec の公開窓口。

1 ジョブ = 1 統合 TSV 入力の仕様（``EstimateParamsJobSpec``）のみを
公開する。複数 TSV の束ね・展開はパイプライン呼び出し側で行う。

NOTE:
    bounds/init YAML のスキーマ解釈（``ParameterFitSpec`` 等）は
    ``shared.estimate_params_fit_spec`` を公開窓口とする。本パッケージは
    ジョブ入力ファイル指定（``EstimateParamsJobSpec``）のみを担う。
"""

from im_cable_system.engine.shared.job_spec.estimate_params.estimate_params_job_spec import (  # noqa: E501
    EstimateParamsJobSpec,
)

__all__ = [
    "EstimateParamsJobSpec",
]
