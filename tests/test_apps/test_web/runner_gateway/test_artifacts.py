"""artifacts: 走査結果の kind 分類と、パストラバーサル拒否。"""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.web.runner_gateway import list_artifacts, resolve_artifact_path


def _make_output_dir(tmp_path: Path) -> Path:
    output_dir = tmp_path / "outputs"
    (output_dir / "figures").mkdir(parents=True)
    (output_dir / "tables").mkdir(parents=True)
    (output_dir / "figures" / "fig_a.png").write_bytes(b"png-bytes")
    (output_dir / "tables" / "tbl_a.csv").write_text("a,b\n1,2\n")
    return output_dir


class TestListArtifacts:
    """outputs/ 配下の走査。"""

    def test_classifies_kind_by_first_path_segment(
        self, tmp_path: Path
    ) -> None:
        output_dir = _make_output_dir(tmp_path)

        infos = list_artifacts(output_dir)

        kinds = {info.kind for info in infos}
        assert kinds == {"figures", "tables"}
        rel_paths = {info.rel_path for info in infos}
        assert rel_paths == {"figures/fig_a.png", "tables/tbl_a.csv"}

    def test_missing_output_dir_returns_empty_list(
        self, tmp_path: Path
    ) -> None:
        assert list_artifacts(tmp_path / "does_not_exist") == []

    def test_size_and_modified_at_are_reported(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)

        infos = list_artifacts(output_dir)

        fig_info = next(i for i in infos if i.rel_path == "figures/fig_a.png")
        assert fig_info.size_bytes == len(b"png-bytes")
        assert fig_info.modified_at > 0


class TestResolveArtifactPath:
    """パストラバーサル対策。"""

    def test_resolves_existing_file_under_output_dir(
        self, tmp_path: Path
    ) -> None:
        output_dir = _make_output_dir(tmp_path)

        resolved = resolve_artifact_path(output_dir, "figures/fig_a.png")

        assert resolved == (output_dir / "figures" / "fig_a.png").resolve()

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)
        (tmp_path / "secret.txt").write_text("secret")

        with pytest.raises(ValueError, match="配下ではありません"):
            resolve_artifact_path(output_dir, "../secret.txt")

    def test_rejects_missing_file(self, tmp_path: Path) -> None:
        output_dir = _make_output_dir(tmp_path)

        with pytest.raises(ValueError, match="見つかりません"):
            resolve_artifact_path(output_dir, "figures/does_not_exist.png")
