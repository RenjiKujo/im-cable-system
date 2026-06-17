"""Forward 系（CartesianGrid / OperatingPoints 共通）ジョブ spec。

設計方針:
    - シンプルな frozen データクラスのみとする。
    - カタログ YAML のパスは JobSpec には持たせず、Runner 側で
      :meth:`IConfig.create` のキーワード引数、または ``config.yaml`` の
      デフォルトとして Config に注入する。
    - JobSpec はユーザーがジョブごとに選ぶ TSV パスのみを保持する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ForwardJobSpec:
    """1 ジョブ分の Forward 系入力ファイル束.

    CartesianGrid モードと OperatingPoints モードは同じファイル構成
    （シリーズ選択 TSV / 軸 TSV / optional 性能曲線 TSV）を共有する。
    軸 TSV の意味（直積か co-indexed か）は ``orchestrate`` 層が
    ``assemble_input_dto`` 段で ``reference_axes`` の指定として与える。
    ``load_data`` / ``assemble_input_dto`` / ``validate_job_spec`` は
    モードに依存しない。

    Attributes:
        series_selection_path: シリーズ選択 TSV のパス。
        axes_path: 評価点軸 TSV のパス（slip / frequency /
            input_line_voltage の列を持つ）。
        performance_curve_path: IM 性能曲線 TSV のパス（``None`` 可）。
    """

    series_selection_path: Path
    axes_path: Path
    performance_curve_path: Path | None = None


@dataclass(frozen=True)
class ForwardJobSpecs:
    """Forward 系ジョブの束.

    Attributes:
        specs: 1 ジョブ分のパス束のタプル。
    """

    specs: tuple[ForwardJobSpec, ...]
