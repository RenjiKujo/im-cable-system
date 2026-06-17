"""execute_stage テスト共通フィクスチャ。

ExecuteStage の責務は「InputDtos を分割し、各 InputDto に Execute
オーケストレーターの ``execute`` を逐次／並列戦略で適用して ItmDtos に
まとめる」ことに限定される。重い数値計算（algorithm 層）は
``tests/test_algorithm`` および ``tests/test_processor/test_all_stage`` で
カバーするため、本テスト群ではステージ固有の責務を fake で隔離して検証する。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from im_cable_system.engine.algorithm.execute_algorithm import (
    IExecuteAlgorithmsOrchestrator,
)
from im_cable_system.engine.processor.execute_stage.strategy import (
    IDataProcessingStrategy,
)
from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from im_cable_system.engine.shared.dto.input import InputDto
from im_cable_system.engine.shared.dto.itm import ItmDto


class StubItm:
    """fake オーケストレーターが返す ItmDto 代用オブジェクト。

    ``source`` に生成元の InputDto を保持し、写像・順序の検証に用いる。
    """

    def __init__(self, source: object) -> None:
        """生成元を保持する。"""
        self.source: object = source
        self.name: object = source


class FakeExecuteOrchestrator(IExecuteAlgorithmsOrchestrator[InputDto, ItmDto]):
    """各 InputDto を :class:`StubItm` に写像する fake オーケストレーター。"""

    def __init__(self) -> None:
        """呼び出し履歴を初期化する。"""
        self.executed: list[object] = []

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IExecuteAlgorithmsOrchestrator[InputDto, ItmDto]:
        """fake を生成する。"""
        _ = (config, logger)
        return cls()

    def execute(self, input_dto: InputDto) -> ItmDto:
        """生成元を保持した StubItm を返す（履歴も記録）。"""
        self.executed.append(input_dto)
        return StubItm(input_dto)  # type: ignore[return-value]

    def _build_model(self, input_dto: InputDto) -> ItmDto:
        """fake では使用しない。"""
        raise NotImplementedError

    def _simulate(self, itm_dto: ItmDto) -> ItmDto:
        """fake では使用しない。"""
        raise NotImplementedError

    def _validate_itm_dto(self, itm_dto: ItmDto) -> None:
        """fake では検証しない。"""
        _ = itm_dto


class RecordingStrategy(IDataProcessingStrategy):
    """受け取った items / process_func を記録する逐次 fake 戦略。"""

    def __init__(self) -> None:
        """記録領域を初期化する。"""
        self.received_items: list[InputDto] | None = None
        self.received_func: Callable[[InputDto], ItmDto] | None = None

    def process(
        self,
        items: list[InputDto],
        process_func: Callable[[InputDto], ItmDto],
    ) -> list[ItmDto]:
        """items を順番に process_func へ通し、結果リストを返す。"""
        self.received_items = list(items)
        self.received_func = process_func
        return [process_func(item) for item in items]


class FakeDumpConfig:
    """dump_itm_dtos_if_enabled が参照する属性のみ持つ fake config。"""

    def __init__(self, base_dir: Path, *, enabled: bool) -> None:
        """ダンプ設定とタイムゾーンを保持する。"""
        self._base_dir: Path = base_dir
        self.dump_data_config = SimpleNamespace(
            dtos=SimpleNamespace(
                itm_dtos=SimpleNamespace(
                    enabled=enabled,
                    sub_dir="itm",
                    filename_pattern="itm_dtos_{timestamp}.pkl",
                ),
            ),
        )
        self.project_info = SimpleNamespace(timezone="UTC")

    def get_dump_base_dir(self) -> Path:
        """ダンプ基準ディレクトリを返す。"""
        return self._base_dir


def _noop(*args: object, **kwargs: object) -> None:
    """何もしないロガーメソッドの代用。"""
    _ = (args, kwargs)


def _repo_root() -> Path:
    """リポジトリルート（``tests/`` の親）。"""
    return Path(__file__).resolve().parents[3]


def _test_base_config_path() -> Path:
    """テスト用ベース設定 YAML のパス。"""
    return (
        _repo_root()
        / "tests"
        / "input_files"
        / "config"
        / "test_base_config.yaml"
    )


@pytest.fixture
def config() -> IConfig:
    """テスト用ベース設定から生成した :class:`IConfig`（実 wiring 検証用）。"""
    return Config.create(config_file_path=_test_base_config_path())


@pytest.fixture
def logger(config: IConfig) -> ILogger:
    """テスト用ベース設定から生成した :class:`ILogger`。"""
    return Logger.create(config)


@pytest.fixture
def fake_orchestrator() -> FakeExecuteOrchestrator:
    """各入力を StubItm に写像する fake オーケストレーター。"""
    return FakeExecuteOrchestrator()


@pytest.fixture
def recording_strategy() -> RecordingStrategy:
    """items / process_func を記録する逐次 fake 戦略。"""
    return RecordingStrategy()


@pytest.fixture
def dump_disabled_config() -> IConfig:
    """ダンプ無効の最小 fake config（process の純粋部分のみ検証する用）。"""
    return FakeDumpConfig(_repo_root(), enabled=False)  # type: ignore[return-value]


@pytest.fixture
def noop_logger() -> ILogger:
    """info/warning が no-op の fake ロガー。"""
    return SimpleNamespace(  # type: ignore[return-value]
        info=_noop,
        warning=_noop,
        debug=_noop,
        error=_noop,
    )
