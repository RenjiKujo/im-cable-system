"""executor: 偽の runner スクリプトで 0/1/2・タイムアウト・キャンセルの各経路を検証する。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from apps.web.runner_gateway import (
    ErrorKind,
    JobStatus,
    start_process,
    terminate,
    wait_for_completion,
)

_FAKE_RUNNER = Path(__file__).parent / "data" / "fake_runner.py"


def _argv(**kwargs: object) -> list[str]:
    argv = [sys.executable, str(_FAKE_RUNNER)]
    for key, value in kwargs.items():
        argv += [f"--{key.replace('_', '-')}", str(value)]
    return argv


class TestWaitForCompletion:
    """終了コード → status/error_kind の写像。"""

    def test_exit_zero_is_succeeded(self, tmp_path: Path) -> None:
        async def run() -> None:
            job = await start_process(
                _argv(exit_code=0),
                cwd=tmp_path,
                run_log_path=tmp_path / "run.log",
            )
            result = await wait_for_completion(job, timeout_seconds=10)
            assert result.status == JobStatus.SUCCEEDED
            assert result.exit_code == 0
            assert result.error_kind is None

        asyncio.run(run())

    def test_exit_two_is_validation_failure(self, tmp_path: Path) -> None:
        async def run() -> None:
            job = await start_process(
                _argv(exit_code=2),
                cwd=tmp_path,
                run_log_path=tmp_path / "run.log",
            )
            result = await wait_for_completion(job, timeout_seconds=10)
            assert result.status == JobStatus.FAILED
            assert result.exit_code == 2
            assert result.error_kind == ErrorKind.VALIDATION

        asyncio.run(run())

    def test_exit_one_is_unexpected_failure(self, tmp_path: Path) -> None:
        async def run() -> None:
            job = await start_process(
                _argv(exit_code=1),
                cwd=tmp_path,
                run_log_path=tmp_path / "run.log",
            )
            result = await wait_for_completion(job, timeout_seconds=10)
            assert result.status == JobStatus.FAILED
            assert result.exit_code == 1
            assert result.error_kind == ErrorKind.UNEXPECTED

        asyncio.run(run())

    def test_timeout_terminates_process_and_reports_timeout(
        self, tmp_path: Path
    ) -> None:
        async def run() -> None:
            job = await start_process(
                _argv(sleep_seconds=5),
                cwd=tmp_path,
                run_log_path=tmp_path / "run.log",
            )
            result = await wait_for_completion(job, timeout_seconds=0.2)
            assert result.status == JobStatus.FAILED
            assert result.exit_code is None
            assert result.error_kind == ErrorKind.TIMEOUT
            assert job.process.returncode is not None

        asyncio.run(run())

    def test_run_log_merges_stdout_and_stderr(self, tmp_path: Path) -> None:
        run_log_path = tmp_path / "run.log"

        async def run() -> None:
            job = await start_process(
                _argv(stdout_message="out-line", stderr_message="err-line"),
                cwd=tmp_path,
                run_log_path=run_log_path,
            )
            await wait_for_completion(job, timeout_seconds=10)

        asyncio.run(run())

        content = run_log_path.read_text()
        assert "out-line" in content
        assert "err-line" in content

    def test_preamble_lines_are_written_first(self, tmp_path: Path) -> None:
        run_log_path = tmp_path / "run.log"

        async def run() -> None:
            job = await start_process(
                _argv(exit_code=0),
                cwd=tmp_path,
                run_log_path=run_log_path,
                preamble_lines=["removed dump.base_dir from uploaded config"],
            )
            await wait_for_completion(job, timeout_seconds=10)

        asyncio.run(run())

        first_line = run_log_path.read_text().splitlines()[0]
        assert first_line == "removed dump.base_dir from uploaded config"


class TestTerminate:
    """キャンセル経路（terminate → 猶予後 kill）。"""

    def test_terminate_stops_running_process(self, tmp_path: Path) -> None:
        async def run() -> None:
            job = await start_process(
                _argv(sleep_seconds=30),
                cwd=tmp_path,
                run_log_path=tmp_path / "run.log",
            )
            await terminate(job, grace_seconds=2)
            job.close_log()
            assert job.process.returncode is not None

        asyncio.run(run())

    def test_terminate_on_already_finished_process_is_noop(
        self, tmp_path: Path
    ) -> None:
        async def run() -> None:
            job = await start_process(
                _argv(exit_code=0),
                cwd=tmp_path,
                run_log_path=tmp_path / "run.log",
            )
            await job.process.wait()
            await terminate(job, grace_seconds=2)
            job.close_log()

        asyncio.run(run())
