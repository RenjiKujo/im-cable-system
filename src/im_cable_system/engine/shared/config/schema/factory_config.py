"""YAML 由来 dict から :class:`ConfigSnapshot` を組み立てる集約 factory。

各セクション factory を順に呼び、検証・補完済みの dataclass を束ねた
``ConfigSnapshot`` を返す。Config（``app_config.py``）の ``__init__`` から
呼び出されることで、Config 取得時点での YAML スキーマ検証
（fail-fast）が成立する。

本 factory は ``calculation.input`` / ``calculation.execute`` /
``calculation.output`` のネスト構造を意識し、各セクションを適切な
深さの dict として下位 factory に渡す責務を負う。
"""

from __future__ import annotations

from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
)
from im_cable_system.engine.shared.config.schema.config_snapshot import (
    ConfigSnapshot,
)
from im_cable_system.engine.shared.config.schema.current_estimation import (
    CurrentEstimationConfigFactory,
)
from im_cable_system.engine.shared.config.schema.data_processing import (
    DataProcessingConfigFactory,
)
from im_cable_system.engine.shared.config.schema.dump import (
    DumpDataConfigFactory,
)
from im_cable_system.engine.shared.config.schema.estimate_params import (
    EstimateParamsConfigFactory,
)
from im_cable_system.engine.shared.config.schema.input_validation import (
    InputValidationConfigFactory,
)
from im_cable_system.engine.shared.config.schema.logging import (
    LoggingConfigFactory,
)
from im_cable_system.engine.shared.config.schema.numerical_guard import (
    NumericalGuardConfigFactory,
)
from im_cable_system.engine.shared.config.schema.output_figures import (
    OutputFiguresConfigFactory,
)
from im_cable_system.engine.shared.config.schema.project_info import (
    ProjectInfoConfigFactory,
)
from im_cable_system.engine.shared.config.schema.validation import (
    ValidationConfigFactory,
)


class ConfigSnapshotFactory:
    """``config.yaml`` 由来 dict から :class:`ConfigSnapshot` を組み立てる。"""

    @staticmethod
    def create(raw: dict[str, Any]) -> ConfigSnapshot:
        """YAML ルート dict から :class:`ConfigSnapshot` を構築する。

        各セクション factory を呼ぶことで、欠損キーは既定値で補完され、
        値ありで不正なものは ``ValueError`` で弾かれる。

        Args:
            raw: ``load_config`` の戻り値（ルート dict）。

        Returns:
            ConfigSnapshot: 検証・正規化済みのイミュータブル dataclass。

        Raises:
            ValueError: いずれかのセクションで検証に失敗した場合。
        """
        calculation = parse_dict(raw.get("calculation"), key_path="calculation")
        input_block = parse_dict(
            calculation.get("input"),
            key_path="calculation.input",
        )
        execute_block = parse_dict(
            calculation.get("execute"),
            key_path="calculation.execute",
        )
        output_block = parse_dict(
            calculation.get("output"),
            key_path="calculation.output",
        )

        return ConfigSnapshot(
            project_info=ProjectInfoConfigFactory.create(
                raw.get("project_info"),
            ),
            logging=LoggingConfigFactory.create(raw.get("logging")),
            input_validation=InputValidationConfigFactory.create(
                input_block.get("validation"),
            ),
            data_processing=DataProcessingConfigFactory.create(
                execute_block.get("data_processing"),
            ),
            numerical_guard=NumericalGuardConfigFactory.create(
                execute_block.get("numerical_guard"),
            ),
            validation=ValidationConfigFactory.create(
                execute_block.get("validation"),
            ),
            current_estimation=CurrentEstimationConfigFactory.create(
                execute_block.get("current_estimation"),
            ),
            estimate_params=EstimateParamsConfigFactory.create(
                execute_block.get("estimate_params"),
            ),
            output_figures=OutputFiguresConfigFactory.create(
                output_block.get("figures"),
            ),
            dump_data=DumpDataConfigFactory.create(raw.get("dump")),
        )
