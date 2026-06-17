"""表 export ステップの実装。

渡された表 ``DataFrame`` を ``config.dump_data_config.tables``（sub_dir /
filename_pattern）に従い CSV として保存する。表の生成・加工はしない
（make_table の責務）。
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pandas import DataFrame

from im_cable_system.engine.algorithm.output_algorithm.export_table.i_table_exporter import (  # noqa: E501
    ITableExporter,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


def _format_artifact_filename(
    pattern: str,
    *,
    kind: str,
    timestamp: str,
    im_cable_system_name: str,
) -> str:
    """filename_pattern を ``{kind}`` / ``{timestamp}`` / ``{im_cable_system_name}`` で整形する。

    pattern がこれらの一部しか含まなくても整形できる（未使用の値は無視する）。
    ただし、これら以外のプレースホルダを含む pattern は ``KeyError`` となる。
    """
    kwargs = {
        "kind": kind,
        "timestamp": timestamp,
        "im_cable_system_name": im_cable_system_name,
    }
    try:
        return pattern.format(**kwargs)
    except KeyError:
        subset = {k: v for k, v in kwargs.items() if f"{{{k}}}" in pattern}
        return pattern.format(**subset)


def _safe_name(output_dto: OutputDto) -> str:
    """OutputDto 名をファイル名向けに無害化した文字列で返す。"""
    name = output_dto.name
    raw = str(name.get_value()) if hasattr(name, "get_value") else str(name)
    return raw.strip().replace("/", "_").replace("\\", "_")[:200]


class TableExporter(ITableExporter):
    """表 DataFrame を CSV ファイルへ保存するエクスポーター。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ITableExporter:
        """エクスポーターのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def export(self, table: DataFrame, output_dto: OutputDto) -> None:
        """渡された表 DataFrame を ``dump_data_config.tables`` に従い保存する。

        空の DataFrame（必須軸欠如時の make_table 戻り値）は保存しない。
        ``output_dto`` はファイル名（系統名）文脈に用いる。
        """
        if table.empty:
            return
        tbl_block = self._config.dump_data_config.tables
        base_dir = self._config.get_dump_base_dir()
        tz_name = self._config.project_info.timezone
        timestamp = datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%dT%H%M%S")
        im_cable_system_name = _safe_name(output_dto)
        filename = _format_artifact_filename(
            tbl_block.filename_pattern,
            kind=im_cable_system_name,
            timestamp=timestamp,
            im_cable_system_name=im_cable_system_name,
        )
        sub_dir = tbl_block.sub_dir.strip()
        out_dir = base_dir / sub_dir if sub_dir else base_dir
        out_path = (out_dir / filename).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        table.to_csv(out_path, index=False, encoding="utf-8")
        self._logger.info("Table saved to %s", out_path)
