"""組み立て後 InputDto バリデーションの公開窓口。

4 段フロー（``_validate_job_spec`` → ``_load_data`` →
``_assemble_input_dto`` → ``_validate_input_dto``）の 4 段目を担う。
各パイプラインの ``Orchestrator.create`` から ``*InputDtoValidator.create``
を呼んで使用する。

サブパッケージ構成:
    - ``forward/``: ``ForwardInputDtoValidator``（CartesianGrid /
      OperatingPoints 共通）。
    - ``estimate_params/``: ``EstimateParamsInputDtoValidator``。
    - ``common/``: 経路非依存の検査関数群（``array_layout_checks`` /
      ``cable_checks`` / ``grid_size_checks`` / ``im_checks`` /
      ``si_execute_input_contract``）。``forward/`` / ``estimate_params/``
      の各 ``Validator`` から共通利用する層内専用窓口。

経路別 Validator の関係:
    Forward / EstimateParams の具象 Validator 同士は委譲しない。
    SI 単位 / cross-field / grid size などの経路非依存チェックは
    ``common/`` 配下に集約し、両経路の Validator が同じ順序で呼び出す。
    EstimateParams Validator はその末尾に「PC カタログ非空」の
    固有チェックを 1 つ追加する。

責務分担:
    パス存在等の事前検査は :mod:`...validate_job_spec`、
    LoadedData が作れないケースの raise は ``load_data`` 層、
    InputDto が作れないケースの raise は ``assemble_input_dto`` 層
    （DTO ``__post_init__`` を含む）に分離している。
    本パッケージでは、組み立て後の :class:`InputDto` でないと判定
    できない事柄のみを扱う。具体的には、現在の単位が SI 基本単位に
    揃っていること、線間電圧が実数入力であること、名板値やケーブル長が
    正値であること、参照軸直積点数が設定上限以下であること、
    EstimateParams では参照性能曲線が存在することを検査する。

検査対象外:
    ExecuteStage のモデルビルダー互換性や、計算モデルごとのサポート可否は
    本パッケージでは扱わない。それらは execute_algorithm 側のモデル構築
    契約として扱う。
"""

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.estimate_params import (  # noqa: E501
    EstimateParamsInputDtoValidator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.forward import (  # noqa: E501
    ForwardInputDtoValidator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.i_input_dto_validator import (  # noqa: E501
    IInputDtoValidator,
)

__all__ = [
    "EstimateParamsInputDtoValidator",
    "ForwardInputDtoValidator",
    "IInputDtoValidator",
]
