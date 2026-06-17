"""Config 全体の正規化済みスナップショット（``ConfigSnapshot``）。

YAML 全体を各セクションごとに検証・補完した結果を、イミュータブルな
dataclass として束ねる。各セクション dataclass はサブパッケージ内で
定義されており、本 dataclass はそれらの集約点である。

YAML 由来 dict から本 dataclass を作る責務は
:mod:`im_cable_system.engine.shared.config.schema.factory_config` に置く。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.config.schema.current_estimation import (
    CurrentEstimationConfig,
)
from im_cable_system.engine.shared.config.schema.data_processing import (
    DataProcessingConfig,
)
from im_cable_system.engine.shared.config.schema.dump import (
    DumpDataConfig,
)
from im_cable_system.engine.shared.config.schema.estimate_params import (
    EstimateParamsConfig,
)
from im_cable_system.engine.shared.config.schema.input_validation import (
    InputValidationConfig,
)
from im_cable_system.engine.shared.config.schema.logging import (
    LoggingConfig,
)
from im_cable_system.engine.shared.config.schema.numerical_guard import (
    NumericalGuardConfig,
)
from im_cable_system.engine.shared.config.schema.output_figures import (
    OutputFiguresConfig,
)
from im_cable_system.engine.shared.config.schema.project_info import (
    ProjectInfoConfig,
)
from im_cable_system.engine.shared.config.schema.validation import (
    ValidationConfig,
)


@dataclass(frozen=True)
class ConfigSnapshot:
    """検証・正規化済みの Config 全体スナップショット。"""

    project_info: ProjectInfoConfig
    logging: LoggingConfig
    input_validation: InputValidationConfig
    data_processing: DataProcessingConfig
    numerical_guard: NumericalGuardConfig
    validation: ValidationConfig
    current_estimation: CurrentEstimationConfig
    estimate_params: EstimateParamsConfig
    output_figures: OutputFiguresConfig
    dump_data: DumpDataConfig
