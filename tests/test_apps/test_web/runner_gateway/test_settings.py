"""RunnerGatewaySettings.from_env: jobs_root の既定と環境変数上書き。

内部実装の単体テスト。
"""

from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from apps.web.runner_gateway import RunnerGatewaySettings


class TestJobsRootFromEnv:
    """``IM_CABLE_SYSTEM_JOBS_ROOT`` 未設定時は ``<repo>/local_jobs/``。"""

    def test_default_is_repo_local_jobs(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.delenv("IM_CABLE_SYSTEM_JOBS_ROOT", raising=False)

        settings = RunnerGatewaySettings.from_env()

        assert settings.jobs_root == settings.repo_root / "local_jobs"
        assert ".im-cable-system" not in settings.jobs_root.parts

    def test_env_override_is_used(
        self, monkeypatch: MonkeyPatch, tmp_path: Path
    ) -> None:
        override = tmp_path / "jobs-override"
        monkeypatch.setenv("IM_CABLE_SYSTEM_JOBS_ROOT", str(override))

        settings = RunnerGatewaySettings.from_env()

        assert settings.jobs_root == override

    def test_from_env_does_not_create_directory(
        self, monkeypatch: MonkeyPatch, tmp_path: Path
    ) -> None:
        jobs_root = tmp_path / "does-not-exist-yet"
        monkeypatch.setenv("IM_CABLE_SYSTEM_JOBS_ROOT", str(jobs_root))

        RunnerGatewaySettings.from_env()

        assert not jobs_root.exists()
