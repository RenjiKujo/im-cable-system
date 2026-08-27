"""``<job_dir>`` のレイアウト決定・作成・入力保存・config.yaml のマテリアライズ。

FastAPI も SQLAlchemy も import しない（``docs/apps/web/0_overview.md`` の
``runner_gateway`` の境界）。

``sanitize_filename`` は窓口 ``__init__.py`` に載せない（層外非公開）。
保存経路は ``save_input_file`` 1 本に限る設計で、api 層がファイル名を先に
加工してから渡す使い方を認めないため。サニタイズ規則自体は実装詳細であり、
公開 API として固定しない。
"""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

_FALLBACK_TIMEZONE = "UTC"

_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
_DEFAULT_SANITIZED_NAME = "file"


@dataclass(frozen=True)
class JobLayout:
    """1 ジョブ分のディレクトリ構成。

    ``<jobs_root>/<job_id>/`` 配下に ``inputs/`` / ``config.yaml`` /
    ``cmd.json`` / ``run.log`` / ``outputs/`` を持つ。
    """

    job_id: str
    job_dir: Path
    inputs_dir: Path
    config_path: Path
    cmd_json_path: Path
    run_log_path: Path
    output_dir: Path

    @classmethod
    def create(cls, jobs_root: Path, job_id: str) -> JobLayout:
        """ジョブディレクトリと ``inputs/`` / ``outputs/`` を作成する。"""
        job_dir = jobs_root / job_id
        inputs_dir = job_dir / "inputs"
        output_dir = job_dir / "outputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            job_id=job_id,
            job_dir=job_dir,
            inputs_dir=inputs_dir,
            config_path=job_dir / "config.yaml",
            cmd_json_path=job_dir / "cmd.json",
            run_log_path=job_dir / "run.log",
            output_dir=output_dir,
        )


def sanitize_filename(filename: str) -> str:
    """アップロードファイル名からディレクトリ成分を除いた安全な basename を作る。"""
    basename = Path(filename).name
    sanitized = _SANITIZE_PATTERN.sub("_", basename).strip("._")
    return sanitized or _DEFAULT_SANITIZED_NAME


def save_input_file(
    layout: JobLayout, field_name: str, filename: str, content: bytes
) -> Path:
    """アップロードされた入力を ``inputs/`` へサニタイズして保存する。

    同一ジョブ内で複数フィールドが同名ファイルを持ってもぶつからないよう、
    ``<field_name>__<sanitized_name>`` で保存する。

    Returns:
        保存先の絶対パス（``resolve()`` 済み）。
    """
    sanitized = sanitize_filename(filename)
    destination = layout.inputs_dir / f"{field_name}__{sanitized}"
    destination.write_bytes(content)
    return destination.resolve()


@dataclass(frozen=True)
class ConfigMaterializeResult:
    """config.yaml マテリアライズの結果。"""

    config_path: Path
    removed_dump_base_dir: bool


def _deep_merge(
    base: dict[str, Any], overrides: Mapping[str, Any]
) -> dict[str, Any]:
    """辞書を再帰的にマージする（``overrides`` を優先）。"""
    merged = deepcopy(base)
    for key, value in overrides.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def materialize_config(
    layout: JobLayout,
    *,
    base_yaml_text: str,
    overrides: Mapping[str, Any] | None = None,
) -> ConfigMaterializeResult:
    """config.yaml をジョブディレクトリへマテリアライズする。

    ``base_yaml_text`` はプリセット YAML、またはアップロードされた config.yaml
    全文のいずれか（どちらを渡すかは呼び出し側が選ぶ）。``overrides`` はそこへ
    深いマージで上書きする。``dump.base_dir`` キーは常に削除する
    （CLI 引数 ``--dump-base-dir`` を優先させ、混在させないため）。

    Raises:
        ValueError: ``base_yaml_text`` のトップレベルが辞書でない場合。
    """
    raw = yaml.safe_load(base_yaml_text) or {}
    if not isinstance(raw, dict):
        raise ValueError(
            "config.yaml のトップレベルは辞書である必要があります。"
        )
    merged = _deep_merge(raw, overrides or {})
    removed = False
    dump_section = merged.get("dump")
    if isinstance(dump_section, dict) and "base_dir" in dump_section:
        del dump_section["base_dir"]
        removed = True
    layout.config_path.write_text(
        yaml.safe_dump(merged, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return ConfigMaterializeResult(
        config_path=layout.config_path, removed_dump_base_dir=removed
    )


@lru_cache(maxsize=512)
def read_config_timezone(job_dir: Path) -> str:
    """``<job_dir>/config.yaml`` の ``project_info.timezone`` を返す。

    ファイル無し・形が不正・IANA 名として無効な場合は ``UTC``。
    一覧 API がジョブごとに読むため、読めない 1 件で応答全体を落とさない。
    ``config.yaml`` は投入時に 1 度書かれて以後変わらないのでキャッシュする。
    """
    config_path = job_dir / "config.yaml"
    name: str | None = None
    if config_path.is_file():
        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            raw = None
        if isinstance(raw, dict):
            project_info = raw.get("project_info")
            if isinstance(project_info, dict):
                candidate = project_info.get("timezone")
                if isinstance(candidate, str) and candidate.strip() != "":
                    name = candidate
    if name is None:
        return _FALLBACK_TIMEZONE
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return _FALLBACK_TIMEZONE
    return name


def write_cmd_json(
    layout: JobLayout, argv: list[str], env: Mapping[str, str]
) -> None:
    """実行した argv と環境変数を ``cmd.json`` に記録する（来歴。成果物メタではない）。"""
    layout.cmd_json_path.write_text(
        json.dumps(
            {"argv": argv, "env": dict(env)}, indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )


def delete_job_dir(jobs_root: Path, job_dir: Path) -> None:
    """``job_dir`` を ``jobs_root`` 配下に限定してから削除する。

    存在しなければ何もしない。

    Raises:
        ValueError: 解決後の ``job_dir`` が ``jobs_root`` の配下でない場合。
    """
    resolved_root = jobs_root.resolve()
    resolved_job_dir = job_dir.resolve()
    if not resolved_job_dir.is_relative_to(resolved_root):
        raise ValueError(
            f"job_dir が jobs_root の配下ではありません: {job_dir}"
        )
    if not resolved_job_dir.exists():
        return
    shutil.rmtree(resolved_job_dir)
