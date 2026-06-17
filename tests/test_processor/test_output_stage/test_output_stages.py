"""3 モード OutputStage の軽量テスト。

pickle や外部ダンプに依存しない。create と空入力時の process のみ検証する。
図表・レポートのファイル出力や Execute との結合は次に集約::

    tests/test_processor/test_all_stage/forward_by_cartesian_grid/
    tests/test_processor/test_all_stage/estimate_params/
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("matplotlib")

import im_cable_system.engine.shared.config.app_config as app_config_module
from im_cable_system.engine.processor.output_stage import (
    EstimateParamsOutputStage,
    ForwardByCartesianGridOutputStage,
    ForwardByOperatingPointsOutputStage,
)
from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDtos,
)

_STAGE_CLASSES: list[Any] = [
    ForwardByCartesianGridOutputStage,
    ForwardByOperatingPointsOutputStage,
    EstimateParamsOutputStage,
]


def _shared_config_yaml_path() -> Path:
    """Simulation 共有 config.yaml のパス。"""
    return Path(app_config_module.__file__).resolve().parent / "config.yaml"


def _test_config() -> IConfig:
    """共有 config.yaml を読んだ Config。"""
    return Config.create(config_file_path=_shared_config_yaml_path())


def _test_logger() -> ILogger:
    """テスト用 Logger。"""
    return Logger.create(_test_config())


@pytest.mark.parametrize("stage_cls", _STAGE_CLASSES)
class TestOutputStages:
    """各 OutputStage の create / 空 process を検証する。"""

    def test_create_returns_stage(self, stage_cls: Any) -> None:
        """create が IStage 実装を返す。"""
        stage = stage_cls.create(
            config=_test_config(),
            logger=_test_logger(),
        )
        assert stage is not None
        assert hasattr(stage, "process")

    def test_process_empty_returns_empty_collection(
        self,
        stage_cls: Any,
    ) -> None:
        """空の Itm コレクションは空の Output コレクションを返す。"""
        stage = stage_cls.create(
            config=_test_config(),
            logger=_test_logger(),
        )
        result = stage.process(ItmDtos(objects=[]))
        assert len(result.get_all()) == 0
