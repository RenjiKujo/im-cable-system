"""Tests for config YAML loading utilities.

YAML 読み込みの境界条件（不存在・空ファイル・非辞書ルート・パース失敗）と
返却値の型契約を担保する。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from im_cable_system.engine.shared.config import (
    load_config,
    load_yaml_root_dict,
)


class TestLoadConfig:
    """load_config の契約テスト。"""

    def test_returns_dict_for_simple_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("a: 1\nb: foo\n", encoding="utf-8")
        loaded = load_config(path)
        assert loaded == {"a": 1, "b": "foo"}

    def test_returns_nested_dict_for_nested_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text(
            "outer:\n  inner:\n    value: 42\n",
            encoding="utf-8",
        )
        loaded = load_config(path)
        assert loaded == {"outer": {"inner": {"value": 42}}}

    def test_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        # YAML 的に空文書は ``None`` だが、API としては ``dict`` を返す契約。
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        loaded = load_config(path)
        assert loaded == {}

    def test_missing_file_raises_file_not_found(self, tmp_path: Path) -> None:
        path = tmp_path / "missing.yaml"
        with pytest.raises(FileNotFoundError):
            load_config(path)

    def test_invalid_yaml_raises_yaml_error(self, tmp_path: Path) -> None:
        path = tmp_path / "broken.yaml"
        # クォート閉じ忘れ等のパース不能 YAML。
        path.write_text("a: [1, 2\n", encoding="utf-8")
        with pytest.raises(yaml.YAMLError):
            load_config(path)

    def test_relative_path_is_resolved(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # 相対パス入力時に cwd 基準で解決され、読み込みできる。
        path = tmp_path / "config.yaml"
        path.write_text("key: value\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        loaded = load_config(Path("config.yaml"))
        assert loaded == {"key": "value"}


class TestLoadYamlRootDict:
    """load_yaml_root_dict の契約テスト。"""

    def test_returns_dict_for_mapping_root(self, tmp_path: Path) -> None:
        path = tmp_path / "mapping.yaml"
        path.write_text("a: 1\nb: foo\n", encoding="utf-8")
        loaded = load_yaml_root_dict(path)
        assert loaded == {"a": 1, "b": "foo"}

    def test_empty_file_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        with pytest.raises(ValueError):
            load_yaml_root_dict(path)

    def test_sequence_root_raises_value_error(self, tmp_path: Path) -> None:
        path = tmp_path / "sequence.yaml"
        path.write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(ValueError):
            load_yaml_root_dict(path)
