"""``outputs/`` 配下の実行時走査とパストラバーサル検証。DB にもマニフェストにも持たない。

``filename_pattern`` や ``sub_dir`` を config でどう変えても追従不要にするため、
成果物メタは一切保持せず毎回 ``rglob`` する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactInfo:
    """1 成果物ファイルの走査結果。"""

    kind: str
    rel_path: str
    size_bytes: int
    modified_at: (
        float  # epoch 秒。ISO8601 化は呼び出し側（api/schemas.py）の責務
    )


def list_artifacts(output_dir: Path) -> list[ArtifactInfo]:
    """``output_dir`` 配下のファイルを走査し、kind 別に一覧する。

    ``kind`` は ``output_dir`` からの相対パスの第 1 セグメント
    （``figures`` / ``tables`` / ``reports`` / ``dtos``）。
    """
    if not output_dir.is_dir():
        return []
    infos: list[ArtifactInfo] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir)
        stat = path.stat()
        infos.append(
            ArtifactInfo(
                kind=rel.parts[0] if rel.parts else "",
                rel_path=rel.as_posix(),
                size_bytes=stat.st_size,
                modified_at=stat.st_mtime,
            )
        )
    return infos


def resolve_artifact_path(output_dir: Path, rel_path: str) -> Path:
    """``rel_path`` を ``output_dir`` 配下に限定して解決する（パストラバーサル対策）。

    解決後のパスが ``output_dir`` の配下であることを ``is_relative_to`` で
    検証してから返す。

    Raises:
        ValueError: 配下から外れる、または対象ファイルが存在しない場合。
    """
    resolved_output_dir = output_dir.resolve()
    candidate = (resolved_output_dir / rel_path).resolve()
    if not candidate.is_relative_to(resolved_output_dir):
        raise ValueError(
            f"rel_path が output_dir の配下ではありません: {rel_path}"
        )
    if not candidate.is_file():
        raise ValueError(f"アーティファクトが見つかりません: {rel_path}")
    return candidate
