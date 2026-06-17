"""export_report 共通のファイル名・出力先パス整形ヘルパー。

report ブロックの ``*_pattern`` を ``{timestamp}`` / ``{im_cable_system_name}``
で整形し（pattern が一部しか含まなくても整形でき、未使用の値は無視する）、
系統名をファイル名向けに無害化する。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from im_cable_system.engine.shared.config import IConfig


def safe_system_name(name: str) -> str:
    """系統名をファイル名向けに無害化した文字列で返す。"""
    return name.strip().replace("/", "_").replace("\\", "_")[:200]


def format_report_filename(
    pattern: str,
    *,
    timestamp: str,
    im_cable_system_name: str,
) -> str:
    """pattern を ``{timestamp}`` / ``{im_cable_system_name}`` で整形する。

    pattern がこれらの一部しか含まなくても整形できる（未使用の値は無視する）。
    ただし、これら以外のプレースホルダを含む pattern は ``KeyError`` となる。
    """
    kwargs = {
        "timestamp": timestamp,
        "im_cable_system_name": im_cable_system_name,
    }
    try:
        return pattern.format(**kwargs)
    except KeyError:
        subset = {k: v for k, v in kwargs.items() if f"{{{k}}}" in pattern}
        return pattern.format(**subset)


def current_timestamp(config: IConfig) -> str:
    """config のタイムゾーンで現在時刻のタイムスタンプ文字列を返す。"""
    tz_name = config.project_info.timezone
    return datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%dT%H%M%S")


def resolve_report_path(
    config: IConfig,
    *,
    sub_dir: str,
    filename: str,
) -> Path:
    """report 出力先の絶対パスを返し、親ディレクトリを作成する。"""
    base_dir = config.get_dump_base_dir()
    sub = sub_dir.strip()
    out_dir = base_dir / sub if sub else base_dir
    out_path = (out_dir / filename).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path
