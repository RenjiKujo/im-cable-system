"""出力アルゴリズムパッケージ。

ItmDto から OutputDto（generic 合成）を組み立て、図・表・レポートを side effect
として出力する。ステップ構成は convert → make_figure → make_table →
make_report → export。具象オーケストレーターは実行モードで分かれる
（ForwardByCartesianGrid / ForwardByOperatingPoints は supply_grid /
operating_points 形状の図表のみ、EstimateParams は加えて 1 件分のレポートを
出力する）。

層外（processor / pipeline）から見える契約は本パッケージ直下の
:class:`IOutputOrchestrator` のみとする。具象オーケストレーター
（:class:`ForwardByCartesianGridOutputOrchestrator` /
:class:`ForwardByOperatingPointsOutputOrchestrator` /
:class:`EstimateParamsOutputOrchestrator`）はインスタンス生成のための窓口
``...output_algorithm.orchestrate`` から import する。run summary を含むレポート
出力は EstimateParams オーケストレーターの per-itm の run() に閉じるため、
processor 層は export ステップを直接利用しない。
"""

from im_cable_system.engine.algorithm.output_algorithm.i_output_orchestrator import (  # noqa: E501
    IOutputOrchestrator,
)

__all__ = [
    "IOutputOrchestrator",
]
