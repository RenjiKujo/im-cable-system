"""estimate_params 用 InputDto バリデーションの公開窓口。

層外・オーケストレーターからは本パッケージの
``EstimateParamsInputDtoValidator`` を import する。EstimateParams 経路
固有の検査として「``im_pc_catalogs`` が空でないこと」を末尾に追加する
が、それ以外の SI 単位 / cross-field / grid size 等は ``common/``
配下の経路非依存チェック一式を Forward 経路と同じ順序で呼び出す。

責務分担:
    TSV/YAML 構造・スキーマ違反は ``load_data`` 層、
    DTO 化・単位正規化・enum 変換は ``assemble_input_dto`` 層、
    DTO ``__post_init__`` による局所契約は各 DTO に分離している。
    本パッケージでは InputDto 全体になって初めて判定できる契約
    （SI 基本単位、cross-field 数値、参照軸直積グリッド上限、
    EstimateParams 固有の必須データ有無）のみを扱う。
"""

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.estimate_params.validator import (  # noqa: E501
    EstimateParamsInputDtoValidator,
)

__all__ = [
    "EstimateParamsInputDtoValidator",
]
