"""フィット結果の InputDto 反映（apply_fitted_input）。

フィット済みの IM シリーズ・ケーブル DTO を ``InputDto`` に埋め込むアセンブラを
公開する。残差評価ループとフィット完了後の最終 forward で共通に用いる。

記述子→DTO の path 適用ヘルパ（:mod:`descriptor_apply` /
:mod:`collect_apply_residual`）は本ステップ専用のため同梱するが、公開窓口には
載せない（アセンブラ経由で利用する）。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input.fitted_input_assembler import (  # noqa: E501
    FittedInputAssembler,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input.i_fitted_input_assembler import (  # noqa: E501
    IFittedInputAssembler,
)

__all__: list[str] = [
    "FittedInputAssembler",
    "IFittedInputAssembler",
]
