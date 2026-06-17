"""load_data 横断のテキスト読込ユーティリティの公開窓口。

本サブパッケージは、Forward 系（CartesianGrid / OperatingPoints。
``load_data.forward/`` 配下に統合）と ``estimate_params/`` が共有する
**最小・安定** なテキストファイル読込基盤のみを置く。責務は次に限定する。

- 拡張子に応じた CSV/TSV 区切り文字の判定
- 行リストへの素読み（``read_csv_rows``）
- 単位セル文字列の正規化（``normalize_unit_cell``）
- YAML ファイルのルート dict 読込（``load_yaml_root_map``）

YAML スキーマ解釈（必須キー取り出し、``{value, unit}`` の解釈、
``model: {name, params}`` の解釈など）は各サブパッケージ配下の parser /
assembler に委ねる。本窓口は上記の薄い層にとどめる。
"""

from im_cable_system.engine.algorithm.input_algorithm.load_data.util.csv_utils import (  # noqa: E501
    csv_delimiter_for_path,
    normalize_unit_cell,
    read_csv_rows,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.util.yaml_utils import (  # noqa: E501
    load_yaml_root_map,
)

__all__ = [
    "csv_delimiter_for_path",
    "load_yaml_root_map",
    "normalize_unit_cell",
    "read_csv_rows",
]
