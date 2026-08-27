"""subprocess の起動・タイムアウト・kill・run.log 書き出し・終了コード→status の写像。

HTTP も DB も import しない。並行数制御・タスク登録簿・キャンセル要求と
終了コードの競合解決は ``apps/web/api/supervisor.py`` の責務
（このモジュールは 1 ジョブ分の subprocess ライフサイクルだけを見る）。
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import IO

_logger = logging.getLogger(__name__)

_EXIT_OK = 0
_EXIT_UNEXPECTED_ERROR = 1
_EXIT_VALIDATION_ERROR = 2

_DEFAULT_KILL_GRACE_SECONDS = 5.0


class JobStatus(str, Enum):
    """ジョブの実行状態（store の ``jobs.status`` と同じ語彙）。"""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorKind(str, Enum):
    """失敗理由の分類（store の ``jobs.error_kind`` と同じ語彙）。"""

    VALIDATION = "validation"
    UNEXPECTED = "unexpected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class ExecutionResult:
    """subprocess 終了後（または壁時計タイムアウト後）の結果。"""

    status: JobStatus
    exit_code: int | None
    error_kind: ErrorKind | None


class RunningJob:
    """起動済み subprocess と、書き込み中の run.log ファイルハンドルの束。"""

    def __init__(
        self, process: asyncio.subprocess.Process, log_file: IO[bytes]
    ) -> None:
        self.process = process
        self._log_file = log_file

    def close_log(self) -> None:
        if not self._log_file.closed:
            self._log_file.close()


async def start_process(
    argv: list[str],
    *,
    cwd: Path,
    run_log_path: Path,
    preamble_lines: list[str] | None = None,
) -> RunningJob:
    """subprocess を起動し、stdout/stderr を ``run_log_path`` へマージして書く。

    起動はシェル文字列ではなく ``create_subprocess_exec(*argv)``（exec）。
    ``argv[0]`` が実行ファイル、以降が引数。ターミナル手打ちと同等の起動を
    プログラムから行う。

    そのほかの起動パラメータ:
        cwd: 子プロセスのカレントディレクトリ（呼び出し側はリポジトリルート）。
            入出力は argv 側が絶対パスだが、相対パス参照の逃げ道を塞ぐ。
        stdout / stderr: 両方を同じ ``run.log`` へ合流（``STDOUT`` は stderr を
            stdout と同じ先へ向ける指定）。UI からログを辿れるようにする。
        env: 親の環境を引き継ぎつつ ``MPLBACKEND=Agg`` を必須上書き
            （matplotlib のヘッドレス実行。未設定だと figure 出力が落ちる）。
    """
    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = run_log_path.open("wb")
    if preamble_lines:
        for line in preamble_lines:
            log_file.write(f"{line}\n".encode())
        log_file.flush()
    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    # argv だけで「何を起動するか」は足りる。cwd / ログ合流 / env は実行条件。
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(cwd),
        stdout=log_file,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
    )
    _logger.info("started job process (pid=%s argv=%s)", process.pid, argv)
    return RunningJob(process=process, log_file=log_file)


def _map_exit_code(exit_code: int) -> ExecutionResult:
    if exit_code == _EXIT_OK:
        return ExecutionResult(JobStatus.SUCCEEDED, exit_code, None)
    if exit_code == _EXIT_VALIDATION_ERROR:
        return ExecutionResult(
            JobStatus.FAILED, exit_code, ErrorKind.VALIDATION
        )
    return ExecutionResult(JobStatus.FAILED, exit_code, ErrorKind.UNEXPECTED)


async def wait_for_completion(
    job: RunningJob, timeout_seconds: float
) -> ExecutionResult:
    """終了か壁時計タイムアウトまで待ち、終了コードを status/error_kind へ写す。

    タイムアウト時は ``terminate`` してから ``ExecutionResult`` を返す
    （呼び出し側で追加の後始末は不要）。ここでの壁時計タイムアウトは
    ``config.calculation.execute.data_processing.timeout_seconds`` とは無関係
    （それは ``as_completed`` の待ち上限でジョブ全体の上限ではない）。
    """
    try:
        exit_code = await asyncio.wait_for(
            job.process.wait(), timeout=timeout_seconds
        )
    except TimeoutError:
        _logger.warning(
            "job process timed out after %.1fs (pid=%s)",
            timeout_seconds,
            job.process.pid,
        )
        await terminate(job, grace_seconds=_DEFAULT_KILL_GRACE_SECONDS)
        return ExecutionResult(JobStatus.FAILED, None, ErrorKind.TIMEOUT)
    finally:
        job.close_log()
    return _map_exit_code(exit_code)


async def terminate(
    job: RunningJob, *, grace_seconds: float = _DEFAULT_KILL_GRACE_SECONDS
) -> None:
    """SIGTERM を送り、猶予後もまだ生きていれば SIGKILL する。

    すでに終了しているプロセスに対しては何もしない（べき等）。
    """
    if job.process.returncode is not None:
        return
    job.process.send_signal(signal.SIGTERM)
    try:
        await asyncio.wait_for(job.process.wait(), timeout=grace_seconds)
    except TimeoutError:
        _logger.warning(
            "job process ignored SIGTERM, sending SIGKILL (pid=%s)",
            job.process.pid,
        )
        job.process.kill()
        await job.process.wait()
