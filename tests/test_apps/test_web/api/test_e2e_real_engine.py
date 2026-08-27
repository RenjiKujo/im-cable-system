"""実エンジンを回す E2E。fake runner を使わず本物の ``runner/run_*.py`` を呼ぶ。"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.web.api import create_app
from apps.web.runner_gateway import RunnerGatewaySettings

_REPO_ROOT = Path(__file__).resolve().parents[4]
_E2E_TIMEOUT_SECONDS = 600.0


@pytest.mark.slow
@pytest.mark.integration
class TestRealEngineEndToEnd:
    """投入 → job_id 即時返却 → ステータス遷移 → 成果物取得。"""

    def test_estimate_params_job_succeeds_via_real_runner(
        self, tmp_path: Path
    ) -> None:
        settings = RunnerGatewaySettings(
            repo_root=_REPO_ROOT,
            python_executable=Path(sys.executable),
            runner_dir=_REPO_ROOT / "runner",
            jobs_root=tmp_path / "jobs",
            max_concurrent_jobs=2,
            job_timeout_seconds=_E2E_TIMEOUT_SECONDS,
        )
        app = create_app(settings=settings)

        with TestClient(app) as client:
            input_path = _REPO_ROOT / "examples/input/estimate_params_input.csv"
            with input_path.open("rb") as input_file:
                submit = client.post(
                    "/api/jobs/estimate_params",
                    data={"base_config": "estimate_params_default"},
                    files={
                        "input": (
                            "estimate_params_input.csv",
                            input_file,
                            "text/csv",
                        )
                    },
                )
            assert submit.status_code == 202
            job_id = submit.json()["job_id"]
            assert submit.json()["status"] == "queued"

            deadline = time.monotonic() + _E2E_TIMEOUT_SECONDS
            detail: dict[str, object] = {}
            while time.monotonic() < deadline:
                detail = client.get(f"/api/jobs/{job_id}").json()
                if detail["status"] in ("succeeded", "failed"):
                    break
                time.sleep(2.0)

            assert detail["status"] == "succeeded", detail

            artifacts = client.get(f"/api/jobs/{job_id}/artifacts").json()[
                "artifacts"
            ]
            kinds = {a["kind"] for a in artifacts}
            assert "figures" in kinds
            assert "reports" in kinds

            response = client.get(f"/api/jobs/{job_id}/fit-summaries")
            assert response.status_code == 200
            summaries = response.json()["summaries"]
            assert len(summaries) == 2
            primaries = {
                item["model_labels"]["im_primary"] for item in summaries
            }
            assert primaries == {
                "BASIC",
                "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
            }
            for item in summaries:
                assert item["model_labels"]["im_friction_windage"] == "NONE"
                assert item["model_labels"]["im_stray_load"] == "NONE"

    def test_estimate_params_non_none_shaft_deduction_via_real_runner(
        self, tmp_path: Path
    ) -> None:
        settings = RunnerGatewaySettings(
            repo_root=_REPO_ROOT,
            python_executable=Path(sys.executable),
            runner_dir=_REPO_ROOT / "runner",
            jobs_root=tmp_path / "jobs",
            max_concurrent_jobs=2,
            job_timeout_seconds=_E2E_TIMEOUT_SECONDS,
        )
        app = create_app(settings=settings)
        input_path = (
            _REPO_ROOT
            / "tests/input_files/estimate_params"
            / "input_for_estimate_params_mechanical_loss.tsv"
        )

        with TestClient(app) as client, input_path.open("rb") as input_file:
            submit = client.post(
                "/api/jobs/estimate_params",
                data={"base_config": "estimate_params_default"},
                files={
                    "input": (
                        "input_for_estimate_params_mechanical_loss.tsv",
                        input_file,
                        "text/tab-separated-values",
                    )
                },
            )
            assert submit.status_code == 202
            job_id = submit.json()["job_id"]

            deadline = time.monotonic() + _E2E_TIMEOUT_SECONDS
            detail: dict[str, object] = {}
            while time.monotonic() < deadline:
                detail = client.get(f"/api/jobs/{job_id}").json()
                if detail["status"] in ("succeeded", "failed"):
                    break
                time.sleep(2.0)

            assert detail["status"] == "succeeded", detail
            response = client.get(f"/api/jobs/{job_id}/fit-summaries")
            assert response.status_code == 200
            summaries = response.json()["summaries"]
            assert any(
                item["model_labels"]["im_friction_windage"] == "CONSTANT_V1"
                and item["model_labels"]["im_stray_load"]
                == "CURRENT_DEPENDENT_QUADRATIC_V1"
                for item in summaries
            )
            matching = next(
                item
                for item in summaries
                if item["model_labels"]["im_friction_windage"] == "CONSTANT_V1"
                and item["model_labels"]["im_stray_load"]
                == "CURRENT_DEPENDENT_QUADRATIC_V1"
            )
            paths = [param["path"] for param in matching["fitted_parameters"]]
            assert any("k_friction_windage" in path for path in paths)
            assert any("k_stray_load" in path for path in paths)
