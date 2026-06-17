"""IM ケーブルシステムの実行時設定とロガーの公開窓口。

層外（algorithm / processor / pipeline / tests）からは、本パッケージ
``im_cable_system.engine.shared.config`` ルートから ``Config`` / ``IConfig``
/ ``Logger`` / ``ILogger`` / ``load_config`` / ``load_yaml_root_dict``、横断デコレータ ``timer``、
および各セクションの検証済み
**dataclass / Enum / `ConfigSnapshot`** をまとめて import する。
``schema/`` や ``decorators/`` 配下への直接 import は不要で、本
``__init__.py`` の ``__all__`` に載っているシンボルだけを使う。

``schema/`` 配下の **Factory（``*ConfigFactory`` / ``ConfigSnapshotFactory``）**
と内部 utility（``_parsers``）は窓口に載せない。設定インスタンスの生成は
``Config.create`` 経由に一本化されており、層外から個別 factory を呼ぶ
必要は無い（必要が生じたら都度 ``__all__`` に追加する）。

使い方とパス解決ルールの詳細は、``docs/shared/config_and_logger.md`` を参照する。
"""

from im_cable_system.engine.shared.config.app_config import Config
from im_cable_system.engine.shared.config.app_logger import Logger
from im_cable_system.engine.shared.config.config_reader import (
    load_config,
    load_yaml_root_dict,
)
from im_cable_system.engine.shared.config.decorators.timer import timer
from im_cable_system.engine.shared.config.i_app_config import IConfig
from im_cable_system.engine.shared.config.i_app_logger import ILogger
from im_cable_system.engine.shared.config.schema.config_snapshot import (
    ConfigSnapshot,
)
from im_cable_system.engine.shared.config.schema.current_estimation import (
    ConvergenceCriterion,
    CurrentEstimationConfig,
    CurrentEstimationIterationConfig,
)
from im_cable_system.engine.shared.config.schema.data_processing import (
    DataProcessingConfig,
    DataProcessingMethod,
)
from im_cable_system.engine.shared.config.schema.dump import (
    DumpBlockConfig,
    DumpDataConfig,
    DumpDtosConfig,
    DumpReportsConfig,
)
from im_cable_system.engine.shared.config.schema.estimate_params import (
    EstimateParamsConfig,
    LeastSquaresOptimizerConfig,
    OptimizerAlgorithm,
    OptimizerConfig,
    ResidualConfig,
    ResidualNormalizationConfig,
    ResidualNormalizationMethod,
    ResidualNormalizationStatistic,
    ResidualWeightsConfig,
)
from im_cable_system.engine.shared.config.schema.input_validation import (
    InputValidationConfig,
)
from im_cable_system.engine.shared.config.schema.logging import (
    LoggingConfig,
    LogLevel,
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
from im_cable_system.engine.shared.config.schema.severity import Severity
from im_cable_system.engine.shared.config.schema.validation import (
    CurrentVoltageRangeValidationConfig,
    EnergyConservationValidationConfig,
    ValidationConfig,
)

__all__ = [
    # 設定本体・I/F
    "Config",
    "load_config",
    "load_yaml_root_dict",
    "ConfigSnapshot",
    "IConfig",
    "ILogger",
    "Logger",
    # 横断デコレータ
    "timer",
    # ロギング
    "LogLevel",
    "LoggingConfig",
    # 共通
    "Severity",
    # project_info / input.validation
    "InputValidationConfig",
    "ProjectInfoConfig",
    # execute.numerical_guard / execute.data_processing
    "DataProcessingConfig",
    "DataProcessingMethod",
    "NumericalGuardConfig",
    # execute.validation
    "CurrentVoltageRangeValidationConfig",
    "EnergyConservationValidationConfig",
    "ValidationConfig",
    # execute.current_estimation
    "ConvergenceCriterion",
    "CurrentEstimationConfig",
    "CurrentEstimationIterationConfig",
    # execute.estimate_params
    "EstimateParamsConfig",
    "LeastSquaresOptimizerConfig",
    "OptimizerAlgorithm",
    "OptimizerConfig",
    "ResidualConfig",
    "ResidualNormalizationConfig",
    "ResidualNormalizationMethod",
    "ResidualNormalizationStatistic",
    "ResidualWeightsConfig",
    # output.figures / dump
    "DumpBlockConfig",
    "DumpDataConfig",
    "DumpDtosConfig",
    "DumpReportsConfig",
    "OutputFiguresConfig",
]
