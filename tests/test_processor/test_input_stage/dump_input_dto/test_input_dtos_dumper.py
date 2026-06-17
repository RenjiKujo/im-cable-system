"""dump_input_dtos_if_enabled の単体テスト。

設定の有効／無効、ファイル出力と読み戻し、ダンプ失敗時の握りつぶしと
warning ログを検証する。実 Config に依存せず、必要属性のみ持つ fake で
隔離する。
"""

from __future__ import annotations

import pickle
from pathlib import Path
from types import SimpleNamespace

from im_cable_system.engine.processor.input_stage.dump_input_dto import (
    dump_input_dtos_if_enabled,
)
from im_cable_system.engine.shared.config import IConfig
from im_cable_system.engine.shared.dto.input import InputDtos


class RecordingLogger:
    """info / warning の呼び出しを記録する fake ロガー。"""

    def __init__(self) -> None:
        """記録領域を初期化する。"""
        self.infos: list[tuple[object, ...]] = []
        self.warnings: list[tuple[object, ...]] = []

    def info(self, *args: object, **kwargs: object) -> None:
        """info 呼び出しを記録する。"""
        _ = kwargs
        self.infos.append(args)

    def warning(self, *args: object, **kwargs: object) -> None:
        """warning 呼び出しを記録する。"""
        _ = kwargs
        self.warnings.append(args)

    def debug(self, *args: object, **kwargs: object) -> None:
        """未使用。"""
        _ = (args, kwargs)

    def error(self, *args: object, **kwargs: object) -> None:
        """未使用。"""
        _ = (args, kwargs)


class _FakeConfig:
    """dump_input_dtos_if_enabled が参照する属性のみ持つ fake config。"""

    def __init__(self, base_dir: Path, *, enabled: bool) -> None:
        self._base_dir = base_dir
        self.dump_data_config = SimpleNamespace(
            dtos=SimpleNamespace(
                input_dtos=SimpleNamespace(
                    enabled=enabled,
                    sub_dir="input",
                    filename_pattern="input_dtos_{timestamp}.pkl",
                ),
            ),
        )
        self.project_info = SimpleNamespace(timezone="UTC")

    def get_dump_base_dir(self) -> Path:
        return self._base_dir


def _make_config(base_dir: Path, *, enabled: bool) -> IConfig:
    """必要属性のみ持つ fake config を作る。"""
    return _FakeConfig(base_dir, enabled=enabled)  # type: ignore[return-value]


def test_disabled_writes_nothing(tmp_path: Path) -> None:
    """無効時はファイルを書かず warning も出さない。"""
    logger = RecordingLogger()
    config = _make_config(tmp_path, enabled=False)

    dump_input_dtos_if_enabled(
        config=config,
        logger=logger,  # type: ignore[arg-type]
        dtos=InputDtos(objects=[]),
    )

    assert list(tmp_path.rglob("*.pkl")) == []
    assert logger.warnings == []
    assert logger.infos == []


def test_enabled_writes_reloadable_pickle(tmp_path: Path) -> None:
    """有効時は sub_dir 配下に pickle を書き、読み戻すと InputDtos になる。"""
    logger = RecordingLogger()
    config = _make_config(tmp_path, enabled=True)

    dump_input_dtos_if_enabled(
        config=config,
        logger=logger,  # type: ignore[arg-type]
        dtos=InputDtos(objects=[]),
    )

    written = list((tmp_path / "input").glob("*.pkl"))
    assert len(written) == 1
    with written[0].open("rb") as handle:
        loaded = pickle.load(handle)
    assert isinstance(loaded, InputDtos)
    assert loaded.get_all() == []
    assert len(logger.infos) == 1
    assert logger.warnings == []


def test_dump_failure_is_swallowed_and_warned(tmp_path: Path) -> None:
    """pickle 不能な内容でも例外を送出せず warning を出す。"""
    logger = RecordingLogger()
    config = _make_config(tmp_path, enabled=True)

    # ラムダは pickle 不能 -> pickle.dump 内で例外になる。
    broken = InputDtos(objects=[lambda: None])  # type: ignore[list-item]

    dump_input_dtos_if_enabled(
        config=config,
        logger=logger,  # type: ignore[arg-type]
        dtos=broken,
    )

    assert len(logger.warnings) == 1
