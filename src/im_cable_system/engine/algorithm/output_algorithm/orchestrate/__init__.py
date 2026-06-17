"""出力系オーケストレーター実装の公開窓口。

実行モードごとの具象オーケストレーター（ForwardByCartesianGrid /
ForwardByOperatingPoints / EstimateParams）を、層外（processor）での
インスタンス生成向けに公開する。共通契約の IF は上位
（``output_algorithm.i_output_orchestrator.IOutputOrchestrator``）に置く
ため、本窓口には載せない（型として参照する processor からは IF のみが
見える、という構成を保つ）。

EstimateParams のレポート出力（1 件分の構造化レポート＋ run summary CSV）は
per-itm の ``run()`` 内に閉じるため、``export_report`` 窓口の各 exporter は
本オーケストレーターのみが利用し、processor 層からは参照しない。
"""

from im_cable_system.engine.algorithm.output_algorithm.orchestrate.estimate_params_output_orchestrator import (  # noqa: E501
    EstimateParamsOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.orchestrate.forward_by_cartesian_grid_output_orchestrator import (  # noqa: E501
    ForwardByCartesianGridOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.orchestrate.forward_by_operating_points_output_orchestrator import (  # noqa: E501
    ForwardByOperatingPointsOutputOrchestrator,
)

__all__ = [
    "EstimateParamsOutputOrchestrator",
    "ForwardByCartesianGridOutputOrchestrator",
    "ForwardByOperatingPointsOutputOrchestrator",
]
