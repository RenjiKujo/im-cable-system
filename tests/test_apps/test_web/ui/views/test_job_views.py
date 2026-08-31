"""job_views の Streamlit 非依存な純関数（時刻表示・一覧行・成果物 URL・状態解決）。

描画そのものは Streamlit ランタイムが要るので対象外。ここで固定するのは
「表示の手前で値をどう変換するか」だけで、とくに TZ 変換と URL の quote は
壊れても画面が黙って間違った値を出すため、テストで押さえる。

内部実装の単体テスト: ``_artifact_url`` はリーフ直 import。
"""

from __future__ import annotations

import httpx

from apps.web.ui.views.job_views import (
    _artifact_url,  # noqa: PLC2701
    format_time,
    has_non_terminal_job,
    job_rows,
    jobs_signature,
    resolve_selected_job_id,
    resolve_status_for_polling,
)


class TestFormatTime:
    """UTC ISO 文字列 → ジョブの config TZ 表示。"""

    def test_converts_utc_to_the_given_timezone(self) -> None:
        formatted = format_time("2026-08-21T00:30:00+00:00", "Asia/Tokyo")

        assert formatted.startswith("2026-08-21 09:30:00")

    def test_treats_naive_input_as_utc(self) -> None:
        """API が tz 指定なしで返しても UTC とみなす（ずれを黙って作らない）。"""
        naive = format_time("2026-08-21T00:30:00", "Asia/Tokyo")
        aware = format_time("2026-08-21T00:30:00+00:00", "Asia/Tokyo")

        assert naive == aware

    def test_empty_input_returns_empty_string(self) -> None:
        assert format_time(None, "UTC") == ""
        assert format_time("", "UTC") == ""

    def test_utc_roundtrip_keeps_the_wall_clock(self) -> None:
        formatted = format_time("2026-08-21T00:30:00+00:00", "UTC")

        assert formatted.startswith("2026-08-21 00:30:00")


class TestJobRows:
    """一覧 dataframe の行。"""

    def _job(self, **overrides: object) -> dict[str, object]:
        job: dict[str, object] = {
            "id": "job-1",
            "mode": "estimate_params",
            "status": "succeeded",
            "created_at": "2026-08-21T00:30:00+00:00",
            "timezone": "Asia/Tokyo",
            "exit_code": 0,
            "error_kind": None,
        }
        job.update(overrides)
        return job

    def test_maps_fields_and_formats_created_at(self) -> None:
        rows = job_rows([self._job()])

        assert len(rows) == 1
        assert rows[0]["job_id"] == "job-1"
        assert rows[0]["mode"] == "estimate_params"
        assert rows[0]["status"] == "succeeded"
        assert rows[0]["exit"] == "0"
        assert str(rows[0]["created_at"]).startswith("2026-08-21 09:30:00")

    def test_none_exit_and_error_become_empty_strings(self) -> None:
        """未終了ジョブで "None" という文字が画面に出ないこと。"""
        rows = job_rows([self._job(exit_code=None, error_kind=None)])

        assert rows[0]["exit"] == ""
        assert rows[0]["error"] == ""

    def test_error_kind_is_passed_through(self) -> None:
        rows = job_rows([self._job(exit_code=2, error_kind="validation")])

        assert rows[0]["exit"] == "2"
        assert rows[0]["error"] == "validation"

    def test_empty_list_returns_empty_rows(self) -> None:
        assert job_rows([]) == []


class TestArtifactUrl:
    """成果物ダウンロード URL の組み立て。"""

    def test_keeps_slashes_but_escapes_other_characters(self) -> None:
        url = _artifact_url(
            "job-1", "figures/curve 01.png", disposition="inline"
        )

        assert "/api/jobs/job-1/artifacts/figures/curve%2001.png" in url
        assert url.endswith("?disposition=inline")

    def test_escapes_characters_that_would_change_the_path(self) -> None:
        url = _artifact_url("job-1", "tables/a?b#c.csv", disposition="inline")

        assert "a%3Fb%23c.csv" in url

    def test_disposition_is_reflected(self) -> None:
        url = _artifact_url("job-1", "t.csv", disposition="attachment")

        assert url.endswith("?disposition=attachment")


class _StubClient:
    """``ApiClient`` のうち ``get_job`` だけを差し替えるスタブ。"""

    def __init__(self, result: object) -> None:
        self._result = result
        self.calls = 0

    def get_job(self, job_id: str) -> dict[str, object]:  # noqa: ARG002
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        assert isinstance(self._result, dict)
        return self._result


class TestResolveStatusForPolling:
    """一覧に無いジョブだけ詳細を 1 回引く。"""

    def _jobs(self) -> list[dict[str, object]]:
        return [{"id": "job-1", "status": "running"}]

    def test_uses_the_listed_status_without_calling_the_api(self) -> None:
        client = _StubClient({"status": "succeeded"})

        status = resolve_status_for_polling(client, self._jobs(), "job-1")  # type: ignore[arg-type]

        assert status == "running"
        assert client.calls == 0

    def test_falls_back_to_the_detail_endpoint(self) -> None:
        client = _StubClient({"status": "succeeded"})

        status = resolve_status_for_polling(client, self._jobs(), "job-2")  # type: ignore[arg-type]

        assert status == "succeeded"
        assert client.calls == 1

    def test_returns_none_when_the_detail_call_fails(self) -> None:
        """ポーリング中の一時的な失敗で画面を落とさない。"""
        client = _StubClient(httpx.ConnectError("boom"))

        status = resolve_status_for_polling(client, self._jobs(), "job-2")  # type: ignore[arg-type]

        assert status is None


class TestResolveSelectedJobId:
    """行選択 > 引き継ぎ > 現在値 > 空。"""

    def _jobs(self) -> list[dict[str, object]]:
        return [
            {"id": "job-a", "status": "running"},
            {"id": "job-b", "status": "succeeded"},
        ]

    def test_row_selection_wins(self) -> None:
        resolved = resolve_selected_job_id(
            jobs=self._jobs(),
            selected_rows=[1],
            pending_select_job_id="job-a",
            current_selected_job_id="job-a",
        )

        assert resolved == "job-b"

    def test_pending_handoff_is_used_when_no_row_is_selected(self) -> None:
        """欠陥 A の回帰: キーが残っていても引き継ぎを読む。"""
        resolved = resolve_selected_job_id(
            jobs=self._jobs(),
            selected_rows=[],
            pending_select_job_id="job-a",
            current_selected_job_id="",
        )

        assert resolved == "job-a"

    def test_keeps_current_when_no_row_and_no_pending(self) -> None:
        resolved = resolve_selected_job_id(
            jobs=self._jobs(),
            selected_rows=[],
            pending_select_job_id="",
            current_selected_job_id="job-b",
        )

        assert resolved == "job-b"

    def test_empty_when_nothing_is_available(self) -> None:
        resolved = resolve_selected_job_id(
            jobs=self._jobs(),
            selected_rows=[],
            pending_select_job_id="",
            current_selected_job_id="",
        )

        assert resolved == ""

    def test_ignores_out_of_range_row_selection(self) -> None:
        resolved = resolve_selected_job_id(
            jobs=self._jobs(),
            selected_rows=[99],
            pending_select_job_id="job-a",
            current_selected_job_id="job-b",
        )

        assert resolved == "job-a"


class TestJobsSignature:
    """一覧監視用の指紋。"""

    def test_status_change_changes_the_signature(self) -> None:
        before = jobs_signature([{"id": "job-1", "status": "running"}])
        after = jobs_signature([{"id": "job-1", "status": "succeeded"}])

        assert before != after

    def test_add_or_remove_changes_the_signature(self) -> None:
        one = jobs_signature([{"id": "job-1", "status": "running"}])
        two = jobs_signature(
            [
                {"id": "job-1", "status": "running"},
                {"id": "job-2", "status": "queued"},
            ]
        )

        assert one != two
        assert jobs_signature([]) != one

    def test_same_list_keeps_the_same_signature(self) -> None:
        jobs: list[dict[str, object]] = [
            {"id": "job-1", "status": "running"},
            {"id": "job-2", "status": "succeeded"},
        ]

        assert jobs_signature(jobs) == jobs_signature(list(jobs))


class TestHasNonTerminalJob:
    """監視フラグメントを起動する条件。"""

    def test_true_when_queued_or_running_is_present(self) -> None:
        assert has_non_terminal_job([{"id": "a", "status": "queued"}])
        assert has_non_terminal_job([{"id": "a", "status": "running"}])

    def test_false_when_all_terminal_or_empty(self) -> None:
        assert not has_non_terminal_job(
            [
                {"id": "a", "status": "succeeded"},
                {"id": "b", "status": "failed"},
                {"id": "c", "status": "cancelled"},
            ]
        )
        assert not has_non_terminal_job([])
