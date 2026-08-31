"""apps/web 全体で共有する実行時設定（python 実行パス・runner 配置・jobs_root・並行数）。

engine の ``Config``（fail-fast・YAML スキーマ検証）とは別の、Web 面専用の軽量設定。
値は環境変数から読み、未設定ならリポジトリ内の既定値にフォールバックする。
値の保持だけを担う DTO のため、他の設定クラスと違いインターフェース化はしない
（docs/conventions/2_design_principles.md の「抽象化しない例外」）。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_JOBS_ROOT = _REPO_ROOT / "local_jobs"
_DEFAULT_MAX_CONCURRENT_JOBS = 2
_DEFAULT_JOB_TIMEOUT_SECONDS = 1800.0


@dataclass(frozen=True)
class RunnerGatewaySettings:
    """subprocess 実行に必要な環境依存パラメータ一式。"""

    repo_root: Path
    python_executable: Path
    runner_dir: Path
    jobs_root: Path
    max_concurrent_jobs: int
    job_timeout_seconds: float

    @property
    def im_series_catalog_default(self) -> Path:
        """同梱 IM シリーズカタログの絶対パス（未アップロード時の既定値）。"""
        return (
            self.repo_root
            / "src/im_cable_system/catalog/im_series_catalog.yaml"
        )

    @property
    def cable_series_catalog_default(self) -> Path:
        """同梱ケーブルシリーズカタログの絶対パス（未アップロード時の既定値）。"""
        return (
            self.repo_root
            / "src/im_cable_system/catalog/cable_series_catalog.yaml"
        )

    @property
    def im_bounds_and_init_default(self) -> Path:
        """同梱 IM パラメータ境界・初期値 YAML の絶対パス（未アップロード時の既定値）。"""
        return (
            self.repo_root
            / "src/im_cable_system/bounds_and_init"
            / "im_descriptor_bounds_and_init.yaml"
        )

    @property
    def cable_bounds_and_init_default(self) -> Path:
        """同梱ケーブルパラメータ境界・初期値 YAML の絶対パス（未アップロード時の既定値）。"""
        return (
            self.repo_root
            / "src/im_cable_system/bounds_and_init"
            / "cable_descriptor_bounds_and_init.yaml"
        )

    @classmethod
    def from_env(cls) -> RunnerGatewaySettings:
        """環境変数から設定を生成するファクトリー。未設定はリポジトリ内既定値を使う。

        対応する環境変数:
            ``IM_CABLE_SYSTEM_PYTHON``: runner を起動する python の絶対パス。
            ``IM_CABLE_SYSTEM_JOBS_ROOT``: ジョブディレクトリの置き場所。
                未設定時は ``<repo_root>/local_jobs/``。相対値を渡しても
                ``resolve()`` して絶対パスで保持する。
            ``IM_CABLE_SYSTEM_MAX_CONCURRENT_JOBS``: 同時実行数の上限。
            ``IM_CABLE_SYSTEM_JOB_TIMEOUT_SECONDS``: 壁時計タイムアウト（秒）。
        """
        repo_root = _REPO_ROOT
        # 絶対化は必須。相対値のままだと ``--dump-base-dir`` に相対パスが載り、
        # engine が「絶対パスであること」を要求して弾く（全ジョブ exit 2）。
        # 台帳の ``job_dir`` / ``output_dir`` を絶対パスとする契約も破れる。
        jobs_root = Path(
            os.environ.get("IM_CABLE_SYSTEM_JOBS_ROOT", str(_DEFAULT_JOBS_ROOT))
        ).resolve()
        max_concurrent_jobs = int(
            os.environ.get(
                "IM_CABLE_SYSTEM_MAX_CONCURRENT_JOBS",
                str(_DEFAULT_MAX_CONCURRENT_JOBS),
            )
        )
        job_timeout_seconds = float(
            os.environ.get(
                "IM_CABLE_SYSTEM_JOB_TIMEOUT_SECONDS",
                str(_DEFAULT_JOB_TIMEOUT_SECONDS),
            )
        )
        return cls(
            repo_root=repo_root,
            python_executable=_resolve_python_executable(repo_root),
            runner_dir=repo_root / "runner",
            jobs_root=jobs_root,
            max_concurrent_jobs=max_concurrent_jobs,
            job_timeout_seconds=job_timeout_seconds,
        )


def _resolve_python_executable(repo_root: Path) -> Path:
    """runner を起動する python を決める。

    ``scripts/generate_estimate_params_readme_figure.py`` と同じ形
    （``[project.scripts]`` が無いためファイルパス直指定）。
    """
    override = os.environ.get("IM_CABLE_SYSTEM_PYTHON")
    if override:
        return Path(override)
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return venv_python
    return Path(sys.executable)
