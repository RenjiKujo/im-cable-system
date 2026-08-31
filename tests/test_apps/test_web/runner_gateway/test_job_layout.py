"""job_layout: config マテリアライズ・dump.base_dir の除去・ファイル名サニタイズ。

内部実装の単体テスト: ``sanitize_filename`` は層外非公開（窓口の ``__all__`` に
無い）ため、リーフから直接 import する。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from apps.web.runner_gateway import (
    JobLayout,
    delete_job_dir,
    materialize_config,
    read_config_timezone,
    save_input_file,
    write_cmd_json,
)
from apps.web.runner_gateway.job_layout import sanitize_filename


class TestJobLayoutCreate:
    """ジョブディレクトリの作成。"""

    def test_create_makes_inputs_and_outputs_dirs(self, tmp_path: Path) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")

        assert layout.job_dir == tmp_path / "jobs" / "job-1"
        assert layout.inputs_dir.is_dir()
        assert layout.output_dir.is_dir()
        assert layout.config_path == layout.job_dir / "config.yaml"
        assert layout.cmd_json_path == layout.job_dir / "cmd.json"
        assert layout.run_log_path == layout.job_dir / "run.log"


class TestSanitizeFilename:
    """アップロードファイル名のサニタイズ。"""

    def test_strips_directory_components(self) -> None:
        assert sanitize_filename("../../etc/passwd") == "passwd"

    def test_replaces_unsafe_characters(self) -> None:
        assert sanitize_filename("input file (1).csv") == "input_file_1_.csv"

    def test_empty_result_falls_back_to_default_name(self) -> None:
        assert sanitize_filename("...") == "file"


class TestSaveInputFile:
    """入力アップロードの保存。"""

    def test_saves_under_inputs_dir_with_field_prefix(
        self, tmp_path: Path
    ) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")

        saved = save_input_file(
            layout, "series_selection", "series.csv", b"a,b\n1,2\n"
        )

        assert saved.parent == layout.inputs_dir
        assert saved.name == "series_selection__series.csv"
        assert saved.read_bytes() == b"a,b\n1,2\n"

    def test_same_original_name_from_different_fields_does_not_collide(
        self, tmp_path: Path
    ) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")

        first = save_input_file(layout, "axes", "shared.csv", b"axes")
        second = save_input_file(
            layout, "series_selection", "shared.csv", b"series"
        )

        assert first != second
        assert first.read_bytes() == b"axes"
        assert second.read_bytes() == b"series"


class TestMaterializeConfig:
    """config.yaml のマテリアライズ。"""

    def test_removes_dump_base_dir_and_reports_it(self, tmp_path: Path) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")
        base_yaml_text = yaml.safe_dump(
            {"dump": {"base_dir": "/somewhere/else", "output": {}}}
        )

        result = materialize_config(layout, base_yaml_text=base_yaml_text)

        assert result.removed_dump_base_dir is True
        written = yaml.safe_load(layout.config_path.read_text())
        assert "base_dir" not in written["dump"]
        assert "output" in written["dump"]

    def test_no_dump_base_dir_reports_false(self, tmp_path: Path) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")
        base_yaml_text = yaml.safe_dump({"project_info": {"version": "1.0.0"}})

        result = materialize_config(layout, base_yaml_text=base_yaml_text)

        assert result.removed_dump_base_dir is False

    def test_overrides_deep_merge_into_base(self, tmp_path: Path) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")
        base_yaml_text = yaml.safe_dump(
            {
                "calculation": {
                    "execute": {"data_processing": {"method": "sequential"}}
                }
            }
        )

        materialize_config(
            layout,
            base_yaml_text=base_yaml_text,
            overrides={
                "calculation": {
                    "execute": {"data_processing": {"max_workers": 4}}
                }
            },
        )

        written = yaml.safe_load(layout.config_path.read_text())
        data_processing = written["calculation"]["execute"]["data_processing"]
        assert data_processing["method"] == "sequential"
        assert data_processing["max_workers"] == 4


class TestReadConfigTimezone:
    """``config.yaml`` の ``project_info.timezone``。読めなければ UTC。"""

    def test_reads_asia_tokyo(self, tmp_path: Path) -> None:
        read_config_timezone.cache_clear()
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        (job_dir / "config.yaml").write_text(
            "project_info:\n  timezone: Asia/Tokyo\n", encoding="utf-8"
        )

        assert read_config_timezone(job_dir) == "Asia/Tokyo"

    def test_missing_project_info_falls_back_to_utc(
        self, tmp_path: Path
    ) -> None:
        read_config_timezone.cache_clear()
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        (job_dir / "config.yaml").write_text("dump: {}\n", encoding="utf-8")

        assert read_config_timezone(job_dir) == "UTC"

    def test_missing_config_file_falls_back_to_utc(
        self, tmp_path: Path
    ) -> None:
        read_config_timezone.cache_clear()
        job_dir = tmp_path / "job"
        job_dir.mkdir()

        assert read_config_timezone(job_dir) == "UTC"

    def test_unknown_zone_name_falls_back_to_utc(self, tmp_path: Path) -> None:
        read_config_timezone.cache_clear()
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        (job_dir / "config.yaml").write_text(
            "project_info:\n  timezone: Not/AZone\n", encoding="utf-8"
        )

        assert read_config_timezone(job_dir) == "UTC"

    def test_rewrite_requires_cache_clear(self, tmp_path: Path) -> None:
        read_config_timezone.cache_clear()
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        (job_dir / "config.yaml").write_text(
            "project_info:\n  timezone: Asia/Tokyo\n", encoding="utf-8"
        )
        assert read_config_timezone(job_dir) == "Asia/Tokyo"

        (job_dir / "config.yaml").write_text(
            "project_info:\n  timezone: UTC\n", encoding="utf-8"
        )
        read_config_timezone.cache_clear()
        assert read_config_timezone(job_dir) == "UTC"


class TestWriteCmdJson:
    """cmd.json への来歴記録。"""

    def test_writes_argv_and_env(self, tmp_path: Path) -> None:
        layout = JobLayout.create(tmp_path / "jobs", "job-1")

        write_cmd_json(layout, ["python", "run.py"], {"MPLBACKEND": "Agg"})

        assert layout.cmd_json_path.is_file()
        content = layout.cmd_json_path.read_text()
        assert "MPLBACKEND" in content
        assert "run.py" in content


class TestDeleteJobDir:
    """ジョブディレクトリ削除の封じ込め。"""

    def test_removes_directory_under_jobs_root(self, tmp_path: Path) -> None:
        jobs_root = tmp_path / "jobs"
        layout = JobLayout.create(jobs_root, "job-1")
        (layout.job_dir / "marker.txt").write_text("x", encoding="utf-8")

        delete_job_dir(jobs_root, layout.job_dir)

        assert not layout.job_dir.exists()

    def test_rejects_path_outside_jobs_root(self, tmp_path: Path) -> None:
        jobs_root = tmp_path / "jobs"
        jobs_root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        with pytest.raises(ValueError, match="jobs_root"):
            delete_job_dir(jobs_root, outside)

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        jobs_root = tmp_path / "jobs"
        layout = JobLayout.create(jobs_root, "job-1")
        sneaky = layout.job_dir / ".." / ".." / "outside"
        sneaky.mkdir(parents=True, exist_ok=True)

        with pytest.raises(ValueError, match="jobs_root"):
            delete_job_dir(jobs_root, sneaky)

    def test_missing_directory_is_noop(self, tmp_path: Path) -> None:
        jobs_root = tmp_path / "jobs"
        jobs_root.mkdir()
        missing = jobs_root / "gone"

        delete_job_dir(jobs_root, missing)
