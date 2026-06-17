"""``dump`` セクションのスキーマと factory。

``base_dir`` は外部から ``Config.create(dump_base_dir=...)`` で渡し得るため
``DumpDataConfig`` には含めず、別経路（``IConfig.get_dump_base_dir()``）で
解決する。本 dataclass は各サブブロック（figures / tables / dtos.*）の
``enabled`` / ``sub_dir`` / ``filename_pattern`` のみを保持する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_bool,
    parse_dict,
    parse_required_str,
)


@dataclass(frozen=True)
class DumpBlockConfig:
    """単一の dump ブロック（figures / tables / 個別 DTO）。"""

    enabled: bool
    sub_dir: str
    filename_pattern: str


@dataclass(frozen=True)
class DumpDtosConfig:
    """DTO 系 dump（input / itm / output）。"""

    input_dtos: DumpBlockConfig
    itm_dtos: DumpBlockConfig
    output_dtos: DumpBlockConfig


@dataclass(frozen=True)
class DumpReportsConfig:
    """report 系 dump（estimate_params 専用の構造化レポート）。

    figures / tables と異なり report は異種複数ファイルを出力するため、
    セクションごとに ``filename_pattern`` を持つ。

    Attributes:
        enabled: report 出力の有効・無効（全セクション共通）。
        sub_dir: 出力サブディレクトリ。
        fit_summary_pattern: 1 件分のフィット要約 CSV のファイル名パターン。
        fitted_catalog_pattern: 推定モデル（catalog 形式）YAML のパターン。
        numerical_stability_pattern: 1 件分の数値安定化イベント CSV の
            ファイル名パターン。
    """

    enabled: bool
    sub_dir: str
    fit_summary_pattern: str
    fitted_catalog_pattern: str
    numerical_stability_pattern: str


@dataclass(frozen=True)
class DumpDataConfig:
    """dump セクション全体（``base_dir`` を除く正規化済み構造）。"""

    figures: DumpBlockConfig
    tables: DumpBlockConfig
    reports: DumpReportsConfig
    dtos: DumpDtosConfig


def _create_dump_block(
    raw: Any,
    *,
    key_path: str,
    default_sub_dir: str,
    default_filename_pattern: str,
) -> DumpBlockConfig:
    """個別 dump ブロック（enabled / sub_dir / filename_pattern）を作る。"""
    block = parse_dict(raw, key_path=key_path)
    return DumpBlockConfig(
        enabled=parse_bool(
            block.get("enabled"),
            key_path=f"{key_path}.enabled",
            default=False,
        ),
        sub_dir=parse_required_str(
            block.get("sub_dir"),
            key_path=f"{key_path}.sub_dir",
            default=default_sub_dir,
        ),
        filename_pattern=parse_required_str(
            block.get("filename_pattern"),
            key_path=f"{key_path}.filename_pattern",
            default=default_filename_pattern,
        ),
    )


def _create_dump_reports_block(
    raw: Any,
    *,
    key_path: str,
) -> DumpReportsConfig:
    """report dump ブロック（enabled / sub_dir / 各 pattern）を作る。"""
    block = parse_dict(raw, key_path=key_path)
    return DumpReportsConfig(
        enabled=parse_bool(
            block.get("enabled"),
            key_path=f"{key_path}.enabled",
            default=False,
        ),
        sub_dir=parse_required_str(
            block.get("sub_dir"),
            key_path=f"{key_path}.sub_dir",
            default="reports",
        ),
        fit_summary_pattern=parse_required_str(
            block.get("fit_summary_pattern"),
            key_path=f"{key_path}.fit_summary_pattern",
            default="report_fit_summary_{im_cable_system_name}_{timestamp}.csv",
        ),
        fitted_catalog_pattern=parse_required_str(
            block.get("fitted_catalog_pattern"),
            key_path=f"{key_path}.fitted_catalog_pattern",
            default="report_model_{im_cable_system_name}_{timestamp}.yaml",
        ),
        numerical_stability_pattern=parse_required_str(
            block.get("numerical_stability_pattern"),
            key_path=f"{key_path}.numerical_stability_pattern",
            default=(
                "report_numerical_stability_"
                "{im_cable_system_name}_{timestamp}.csv"
            ),
        ),
    )


class DumpDataConfigFactory:
    """``dump`` セクションを dataclass に変換する。

    YAML 構造（``dump.input.dtos`` / ``dump.execute.dtos`` / ``dump.output.*``）
    を、利用側にとって読みやすい平坦な構造（figures / tables / dtos.*）に
    詰め替えて返す。
    """

    @staticmethod
    def create(raw: Any) -> DumpDataConfig:
        """YAML 由来の dict から :class:`DumpDataConfig` を組み立てる。

        Args:
            raw: ``dump`` の生 dict（``None`` 可。``base_dir`` キーは無視）。

        Returns:
            DumpDataConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または各値の制約違反。
        """
        block = parse_dict(raw, key_path="dump")
        input_block = parse_dict(
            block.get("input"),
            key_path="dump.input",
        )
        execute_block = parse_dict(
            block.get("execute"),
            key_path="dump.execute",
        )
        output_block = parse_dict(
            block.get("output"),
            key_path="dump.output",
        )
        return DumpDataConfig(
            figures=_create_dump_block(
                output_block.get("figures"),
                key_path="dump.output.figures",
                default_sub_dir="figures",
                default_filename_pattern=(
                    "fig_{kind}_{im_cable_system_name}_{timestamp}.png"
                ),
            ),
            tables=_create_dump_block(
                output_block.get("tables"),
                key_path="dump.output.tables",
                default_sub_dir="tables",
                default_filename_pattern="tbl_{kind}_{timestamp}.csv",
            ),
            reports=_create_dump_reports_block(
                output_block.get("reports"),
                key_path="dump.output.reports",
            ),
            dtos=DumpDtosConfig(
                input_dtos=_create_dump_block(
                    input_block.get("dtos"),
                    key_path="dump.input.dtos",
                    default_sub_dir="dtos/input",
                    default_filename_pattern="input_{timestamp}.pkl",
                ),
                itm_dtos=_create_dump_block(
                    execute_block.get("dtos"),
                    key_path="dump.execute.dtos",
                    default_sub_dir="dtos/itm",
                    default_filename_pattern="itm_{timestamp}.pkl",
                ),
                output_dtos=_create_dump_block(
                    output_block.get("dtos"),
                    key_path="dump.output.dtos",
                    default_sub_dir="dtos/output",
                    default_filename_pattern="output_{timestamp}.pkl",
                ),
            ),
        )
