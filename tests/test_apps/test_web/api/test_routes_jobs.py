"""routes_jobs: 投入が 202 を返し計算を待たないこと・状態遷移・パストラバーサル拒否。"""

from __future__ import annotations

import io
import time
from pathlib import Path

from fastapi.testclient import TestClient

from tests.test_apps.test_web.api.conftest import poll_until_terminal

_REPO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLE_CSV = _REPO_ROOT / "examples/input/estimate_params_input.csv"
_REPORT_SAMPLE = (
    Path(__file__).resolve().parent.parent
    / "engine_contract"
    / "data"
    / "report_model_sample.yaml"
)
_REQUIRED_AXES_PREFIX = (
    "model_candidate_axis,candidate_1\n"
    "im_friction_windage,NONE\n"
    "im_stray_load,NONE\n"
)


def _estimate_params_files(
    content: str = "slip,current\n0.1,1.0\n",
    *,
    include_required_axes: bool = True,
) -> dict:
    if include_required_axes and "im_friction_windage" not in content:
        content = _REQUIRED_AXES_PREFIX + content
    return {"input": ("input.csv", io.BytesIO(content.encode()), "text/csv")}


def _forward_files(content: str = "slip,freq,voltage\n0.1,60,400\n") -> dict:
    return {
        "series_selection": (
            "series.csv",
            io.BytesIO(content.encode()),
            "text/csv",
        ),
        "axes": ("axes.csv", io.BytesIO(b"slip\n0.1\n"), "text/csv"),
    }


class TestSubmitJob:
    """投入 202・入力不備・未知の mode。"""

    def test_submit_returns_202_without_waiting_for_completion(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "queued"
        assert body["job_id"]

    def test_submit_unknown_mode_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/jobs/not_a_real_mode",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )

        assert response.status_code == 400

    def test_submit_missing_required_file_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
        )

        assert response.status_code == 400

    def test_submit_without_config_source_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/jobs/estimate_params", files=_estimate_params_files()
        )

        assert response.status_code == 400

    def test_submit_forward_mode_returns_202(self, client: TestClient) -> None:
        response = client.post(
            "/api/jobs/forward_by_cartesian_grid",
            data={"base_config": "forward_by_cartesian_grid_default"},
            files=_forward_files(),
        )

        assert response.status_code == 202


class TestJobLifecycle:
    """状態遷移（succeeded / failed(validation) / failed(unexpected)）。"""

    def test_reaches_succeeded_and_lists_artifacts(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]

        detail = poll_until_terminal(client, job_id)

        assert detail["status"] == "succeeded"
        assert detail["exit_code"] == 0
        assert detail["error_kind"] is None

        artifacts = client.get(f"/api/jobs/{job_id}/artifacts").json()
        rel_paths = [a["rel_path"] for a in artifacts["artifacts"]]
        assert "figures/fig_fake.png" in rel_paths

    def test_reaches_failed_with_validation_error_kind(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files("TRIGGER_EXIT_2\n"),
        )
        job_id = submit.json()["job_id"]

        detail = poll_until_terminal(client, job_id)

        assert detail["status"] == "failed"
        assert detail["exit_code"] == 2
        assert detail["error_kind"] == "validation"

    def test_reaches_failed_with_unexpected_error_kind(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files("TRIGGER_EXIT_1\n"),
        )
        job_id = submit.json()["job_id"]

        detail = poll_until_terminal(client, job_id)

        assert detail["status"] == "failed"
        assert detail["exit_code"] == 1
        assert detail["error_kind"] == "unexpected"

    def test_log_endpoint_returns_run_log_tail(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files("TRIGGER_EXIT_1\n"),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        log_response = client.get(f"/api/jobs/{job_id}/log?tail_lines=10")

        assert log_response.status_code == 200


class TestJobListAndDetail:
    """一覧・詳細・404。"""

    def test_get_unknown_job_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/jobs/does-not-exist")
        assert response.status_code == 404

    def test_list_filters_by_mode(self, client: TestClient) -> None:
        client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        client.post(
            "/api/jobs/forward_by_cartesian_grid",
            data={"base_config": "forward_by_cartesian_grid_default"},
            files=_forward_files(),
        )

        response = client.get("/api/jobs", params={"mode": "estimate_params"})

        jobs = response.json()["jobs"]
        assert jobs
        assert all(job["mode"] == "estimate_params" for job in jobs)

    def test_detail_includes_config_timezone_and_utc_offset(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]

        detail = client.get(f"/api/jobs/{job_id}").json()

        assert detail["timezone"] == "Asia/Tokyo"
        assert detail["created_at"].endswith("+00:00")


class TestArtifactDownload:
    """成果物ダウンロードとパストラバーサル拒否。"""

    def test_downloads_artifact_content(self, client: TestClient) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        response = client.get(
            f"/api/jobs/{job_id}/artifacts/figures/fig_fake.png"
        )

        assert response.status_code == 200
        assert response.content == b"fake-png-bytes"
        content_disposition = response.headers["content-disposition"]
        assert content_disposition.startswith("inline;")
        assert "fig_fake.png" in content_disposition

    def test_disposition_inline_sets_content_disposition(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        response = client.get(
            f"/api/jobs/{job_id}/artifacts/figures/fig_fake.png"
            "?disposition=inline"
        )

        assert response.status_code == 200
        content_disposition = response.headers["content-disposition"]
        assert content_disposition.startswith("inline;")
        assert "fig_fake.png" in content_disposition

    def test_disposition_attachment_sets_content_disposition(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        response = client.get(
            f"/api/jobs/{job_id}/artifacts/figures/fig_fake.png"
            "?disposition=attachment"
        )

        assert response.status_code == 200
        content_disposition = response.headers["content-disposition"]
        assert content_disposition.startswith("attachment;")
        assert "fig_fake.png" in content_disposition

    def test_rejects_path_traversal(self, client: TestClient) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        response = client.get(
            f"/api/jobs/{job_id}/artifacts/../../../../../../etc/passwd"
        )

        assert response.status_code in (400, 404)

    def test_missing_artifact_returns_404(self, client: TestClient) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        response = client.get(
            f"/api/jobs/{job_id}/artifacts/figures/does_not_exist.png"
        )

        assert response.status_code == 404


class TestCancelJob:
    """キャンセル経路。"""

    def test_cancel_running_job_marks_cancelled(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files("TRIGGER_SLEEP_5\n"),
        )
        job_id = submit.json()["job_id"]

        # running へ遷移するまで少し待ってからキャンセルする。
        for _ in range(50):
            detail = client.get(f"/api/jobs/{job_id}").json()
            if detail["status"] == "running":
                break
            time.sleep(0.05)

        cancel_response = client.post(f"/api/jobs/{job_id}/cancel")
        assert cancel_response.status_code == 200

        detail = poll_until_terminal(client, job_id)
        assert detail["status"] == "cancelled"
        assert detail["error_kind"] == "cancelled"

    def test_cancel_unknown_job_returns_404(self, client: TestClient) -> None:
        response = client.post("/api/jobs/does-not-exist/cancel")
        assert response.status_code == 404


def _old_format_example_csv() -> str:
    lines = _EXAMPLE_CSV.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(
        line
        for line in lines
        if "im_friction_windage" not in line and "im_stray_load" not in line
    )


def _jobs_root(client: TestClient) -> Path:
    return client.app.state.settings.jobs_root


class TestShaftDeductionPreflight:
    """旧形式入力は 422。ジョブは作られない。"""

    def test_old_format_csv_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(
                _old_format_example_csv(), include_required_axes=False
            ),
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "NONE" in detail
        assert "examples/input/estimate_params_input.csv" in detail
        assert client.get("/api/jobs").json()["jobs"] == []

    def test_old_format_bounds_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files={
                **_estimate_params_files(),
                "im_bounds": (
                    "im_bounds.yaml",
                    io.BytesIO(b"version: 1\nprimary: {}\n"),
                    "application/x-yaml",
                ),
            },
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "friction_windage" in detail
        assert "NONE" in detail

    def test_old_format_catalog_returns_422(self, client: TestClient) -> None:
        catalog = (
            b"version: 1\nim_series:\n"
            b'  - name: "Broken01"\n'
            b"    primary:\n"
            b'      model: { name: "BASIC", params: [] }\n'
        )
        response = client.post(
            "/api/jobs/forward_by_cartesian_grid",
            data={"base_config": "forward_by_cartesian_grid_default"},
            files={
                **_forward_files(),
                "im_catalog": (
                    "im_catalog.yaml",
                    io.BytesIO(catalog),
                    "application/x-yaml",
                ),
            },
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "Broken01" in detail
        assert "NONE" in detail


class TestUnknownModelKindPreflight:
    """候補軸の種別名のタイポは 422。ジョブは作られない。

    engine 側では bounds YAML 引きの ``KeyError`` になり、runner の exit 1 ＝
    ``error_kind="unexpected"`` へ落ちる（利用者の入力ミスなのに「想定外
    エラー」と出る）。投入時に弾いて ``validation`` 側へ寄せる。
    """

    def test_typo_in_candidate_kind_returns_422(
        self, client: TestClient
    ) -> None:
        content = (
            "model_candidate_axis,candidate_1\n"
            "im_primary,SLIP_DEPENDNET_LEAKAGE_SATURATION_V1\n"
            "im_friction_windage,NONE\n"
            "im_stray_load,NONE\n"
            "\n"
            "slip,current\n"
            "0.1,1.0\n"
        )
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(content),
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "im_primary" in detail
        assert "SLIP_DEPENDNET_LEAKAGE_SATURATION_V1" in detail
        assert client.get("/api/jobs").json()["jobs"] == []

    def test_known_kinds_are_accepted(self, client: TestClient) -> None:
        """正しい種別名なら通ること（プリフライトが過剰に弾かない）。"""
        content = (
            "model_candidate_axis,candidate_1\n"
            "im_primary,SLIP_DEPENDENT_LEAKAGE_SATURATION_V1\n"
            "im_friction_windage,NONE\n"
            "im_stray_load,NONE\n"
            "\n"
            "slip,current\n"
            "0.1,1.0\n"
        )
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(content),
        )

        assert response.status_code == 202


class TestRejectedSubmissionLeavesNothingBehind:
    """弾いた投入はディレクトリも残さない。

    台帳行は作られないので、ディレクトリだけ残ると台帳から辿れず、UI からも
    API からも消せないゴミが ``jobs_root`` に溜まり続ける。
    """

    def _job_dirs(self, tmp_path: Path) -> list[Path]:
        jobs_root = tmp_path / "jobs"
        if not jobs_root.is_dir():
            return []
        return [p for p in jobs_root.iterdir() if p.is_dir()]

    def test_422_removes_the_job_dir(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(
                _old_format_example_csv(), include_required_axes=False
            ),
        )

        assert response.status_code == 422
        assert client.get("/api/jobs").json()["jobs"] == []
        assert self._job_dirs(tmp_path) == []

    def test_400_removes_the_job_dir(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """必須入力の欠落（400）も同じく残さない。"""
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files={},
        )

        assert response.status_code == 400
        assert client.get("/api/jobs").json()["jobs"] == []
        assert self._job_dirs(tmp_path) == []

    def test_successful_submission_keeps_the_job_dir(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """後始末が成功経路を巻き込んでいないこと。"""
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )

        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert [p.name for p in self._job_dirs(tmp_path)] == [job_id]


class TestFitSummaries:
    """GET /api/jobs/{id}/fit-summaries。"""

    def test_fit_summaries_returns_all_sorted_by_name(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        reports_dir = _jobs_root(client) / job_id / "outputs" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        sample = _REPORT_SAMPLE.read_text(encoding="utf-8")
        (reports_dir / "report_model_b.yaml").write_text(
            sample.replace("SYS01", "B_SYS"), encoding="utf-8"
        )
        (reports_dir / "report_model_a.yaml").write_text(
            sample.replace("SYS01", "A_SYS"), encoding="utf-8"
        )

        response = client.get(f"/api/jobs/{job_id}/fit-summaries")

        assert response.status_code == 200
        summaries = response.json()["summaries"]
        assert [item["name"] for item in summaries] == ["A_SYS", "B_SYS"]
        assert summaries[0]["report_rel_path"] == "reports/report_model_a.yaml"
        assert summaries[1]["report_rel_path"] == "reports/report_model_b.yaml"
        assert summaries[0]["model_labels"]["im_friction_windage"] == "NONE"
        assert summaries[0]["fit_metrics"]["optimizer_success"] is True

    def test_fit_summaries_empty_returns_200(self, client: TestClient) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)

        response = client.get(f"/api/jobs/{job_id}/fit-summaries")
        assert response.status_code == 200
        assert response.json()["summaries"] == []

    def test_near_zero_slip_warning_when_non_none_present(
        self, client: TestClient
    ) -> None:
        example = _EXAMPLE_CSV.read_text(encoding="utf-8").replace(
            "im_friction_windage,NONE", "im_friction_windage,CONSTANT_V1"
        )
        response = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(example, include_required_axes=False),
        )

        assert response.status_code == 202
        warnings = response.json()["warnings"]
        assert warnings
        assert any("s≈0" in item or "s ≈ 0" in item for item in warnings)


class TestDeleteJob:
    """DELETE /api/jobs/{id}。"""

    def test_delete_terminal_job_removes_row_and_dir(
        self, client: TestClient
    ) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files(),
        )
        job_id = submit.json()["job_id"]
        poll_until_terminal(client, job_id)
        job_dir = _jobs_root(client) / job_id
        assert job_dir.is_dir()

        response = client.delete(f"/api/jobs/{job_id}")

        assert response.status_code == 204
        assert client.get(f"/api/jobs/{job_id}").status_code == 404
        assert job_id not in {
            job["id"] for job in client.get("/api/jobs").json()["jobs"]
        }
        assert not job_dir.exists()

    def test_delete_unknown_job_returns_404(self, client: TestClient) -> None:
        response = client.delete("/api/jobs/does-not-exist")
        assert response.status_code == 404

    def test_delete_running_job_returns_409(self, client: TestClient) -> None:
        submit = client.post(
            "/api/jobs/estimate_params",
            data={"base_config": "estimate_params_default"},
            files=_estimate_params_files("TRIGGER_SLEEP_5\n"),
        )
        job_id = submit.json()["job_id"]
        job_dir = _jobs_root(client) / job_id

        for _ in range(50):
            detail = client.get(f"/api/jobs/{job_id}").json()
            if detail["status"] == "running":
                break
            time.sleep(0.05)

        response = client.delete(f"/api/jobs/{job_id}")

        assert response.status_code == 409
        assert "キャンセル" in response.json()["detail"]
        assert client.get(f"/api/jobs/{job_id}").status_code == 200
        assert job_dir.is_dir()
