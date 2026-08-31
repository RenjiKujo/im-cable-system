"""``report_model_*.yaml`` の読み取り。

公開窓口 ``apps.web.engine_contract`` から import する。
"""

from __future__ import annotations

from pathlib import Path

from apps.web.engine_contract import list_fitted_catalogs

_DATA_DIR = Path(__file__).resolve().parent / "data"
_SAMPLE = _DATA_DIR / "report_model_sample.yaml"


class TestListFittedCatalogs:
    """全件読み取りと name 昇順。"""

    def test_reads_sample_report(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        destination = reports_dir / "report_model_sample.yaml"
        destination.write_text(
            _SAMPLE.read_text(encoding="utf-8"), encoding="utf-8"
        )

        views = list_fitted_catalogs(reports_dir)

        assert len(views) == 1
        view = views[0]
        assert view.name == "SYS01"
        assert view.source_filename == "report_model_sample.yaml"
        assert view.model_labels["im_friction_windage"] == "NONE"
        assert view.model_labels["im_stray_load"] == "NONE"
        assert view.fit_metrics.optimizer_success is True
        paths = [param.path for param in view.fitted_parameters]
        assert "im.friction_windage_model.params.k_friction_windage" in paths

    def test_returns_empty_when_directory_is_empty(
        self, tmp_path: Path
    ) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        assert list_fitted_catalogs(reports_dir) == ()

    def test_returns_empty_when_directory_is_missing(
        self, tmp_path: Path
    ) -> None:
        assert list_fitted_catalogs(tmp_path / "reports") == ()

    def test_returns_all_sorted_by_name(self, tmp_path: Path) -> None:
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        sample = _SAMPLE.read_text(encoding="utf-8")
        (reports_dir / "report_model_b.yaml").write_text(
            sample.replace("SYS01", "B_SYS"), encoding="utf-8"
        )
        (reports_dir / "report_model_a.yaml").write_text(
            sample.replace("SYS01", "A_SYS"), encoding="utf-8"
        )

        views = list_fitted_catalogs(reports_dir)

        assert [view.name for view in views] == ["A_SYS", "B_SYS"]
        assert [view.source_filename for view in views] == [
            "report_model_a.yaml",
            "report_model_b.yaml",
        ]
