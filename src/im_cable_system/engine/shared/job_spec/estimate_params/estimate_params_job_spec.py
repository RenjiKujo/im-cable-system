"""estimate_params 向け job_spec。

EstimateParams は 1 つの統合 TSV を読み込み、内部の候補軸を直積展開して
複数の :class:`InputDto` を生成する。1 ジョブ = 1 統合 TSV。

設計方針:
    - シンプルな frozen データクラスのみとする。
    - 境界 YAML のパスは JobSpec には持たせず、Runner 側で
      :meth:`IConfig.create` のキーワード引数
      （``im_bounds_and_init_file_path`` / ``cable_bounds_and_init_file_path``）
      に渡す。これにより PIP 利用時に、クライアントは自プロジェクト内の
      ``bounds`` YAML を Config に注入できる。
    - ジョブ識別用の命名 prefix は持たない。出力用ラベルは TSV の
      ``im_performance_curve_name`` を流用する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EstimateParamsJobSpec:
    """estimate_params 1 ジョブ分の入力定義。

    Attributes:
        input_tsv_path: 統合入力 TSV（名板・固定モデル・候補軸・性能曲線）。
    """

    input_tsv_path: Path
