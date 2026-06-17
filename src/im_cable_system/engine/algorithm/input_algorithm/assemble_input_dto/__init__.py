"""IM ケーブルシステム Input 用の InputDto 組み立て公開窓口。

4 段フロー（``_validate_job_spec`` → ``_load_data`` →
``_assemble_input_dto`` → ``_validate_input_dto``）の 3 段目を担う。
各パイプラインの ``Orchestrator.create`` から ``*Assembler.create`` を
呼んで使用する。

サブパッケージ構成:
    - ``forward/``: ``ForwardInputDtoAssembler``（CartesianGrid /
      OperatingPoints 共通）。
    - ``estimate_params/``: ``EstimateParamsAssembler``。
    - ``common/``: 経路非依存の組み立てヘルパ群（``unit_normalizer`` /
      ``si_normalizer`` / 各種 ``*_builder``）。``forward/`` /
      ``estimate_params/`` の各 ``Assembler`` から共通利用する層内専用窓口。

経路別 Assembler の関係:
    Forward / EstimateParams の具象 Assembler 同士は委譲しない。
    共有する DTO ビルダー・SI 正規化は ``common/`` 配下に集約し、
    両経路の Assembler が必要なものを直接呼び出す。
    EstimateParams Assembler はその前段に「性能曲線の比率列 →
    絶対単位変換」を挟む。

層外 import 経路:
    - 具象アセンブラ（``ForwardInputDtoAssembler`` /
      ``EstimateParamsAssembler``）は経路別サブ窓口
      （``assemble_input_dto.forward`` / ``assemble_input_dto.estimate_params``）
      から import するのを正規とする。
    - 経路非依存の抽象（``IInputDtoAssembler``）は本ルート窓口から
      import する。
    - 本ルート窓口でも具象アセンブラを再エクスポートしているが、これは
      横断スクリプト等から「両モードの具象を 1 つの窓口から取得できる」
      便宜上のもので、orchestrate 層からは経路別窓口を優先する。

責務分担:
    TSV/YAML 構造・スキーマ違反は ``load_data`` 層、
    DTO ``__post_init__`` による局所契約は各 DTO に分離している。
    本パッケージでは LoadedData → ``InputDto`` 構成要素 DTO への純粋な
    変換と、最終段での ``InputDto`` 全体の SI 基本単位化を扱う。
    組み立て後でないと判定できない契約（SI 単位整合・cross-field 制約・
    参照軸直積点数など）は :mod:`...validate_input_dto` 段に委ねる。
"""

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.estimate_params import (  # noqa: E501
    EstimateParamsAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.forward import (  # noqa: E501
    ForwardInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.i_input_dto_assembler import (  # noqa: E501
    IInputDtoAssembler,
)

__all__ = [
    "EstimateParamsAssembler",
    "ForwardInputDtoAssembler",
    "IInputDtoAssembler",
]
