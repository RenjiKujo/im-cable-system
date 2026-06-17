"""Figure export ステップの実装。

渡された Figure を ``config.dump_data_config.figures``（sub_dir /
filename_pattern）に従いファイルへ保存するだけの軽量ステップ。Figure の
生成・加工・サイズ・解像度（A4 印刷前提の figsize / dpi）はすべて
make_figure 側の責務。表示（show）は display_figure の責務のため行わない。
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from matplotlib.figure import Figure

from im_cable_system.engine.algorithm.output_algorithm.export_figure.i_figure_exporter import (  # noqa: E501
    IFigureExporter,
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


class FigureExporter(IFigureExporter):
    """Figure をファイルへ保存するエクスポーター。"""

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
    ) -> IFigureExporter:
        """エクスポーターのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def export(
        self,
        figure: Figure,
        output_dto: OutputDto,
        *,
        kind: str = "figure",
    ) -> None:
        """渡された Figure を ``dump_data_config.figures`` に従い保存する。

        ``kind`` は slip 軸・出力比軸などの Figure 種別、``output_dto`` は
        系統名文脈に用いる。Figure の生成・加工・サイズ・解像度は make_figure の
        責務のため、本ステップは保存先を決めて ``savefig`` するだけ
        （figure 固有の figsize / dpi をそのまま使う）。
        """
        fig_block = self._config.dump_data_config.figures
        base_dir = self._config.get_dump_base_dir()
        tz_name = self._config.project_info.timezone
        timestamp = datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%dT%H%M%S")
        im_cable_system_name = _safe_name(output_dto)
        filename = _format_artifact_filename(
            fig_block.filename_pattern,
            kind=kind,
            timestamp=timestamp,
            im_cable_system_name=im_cable_system_name,
        )
        sub_dir = fig_block.sub_dir.strip()
        out_dir = base_dir / sub_dir if sub_dir else base_dir
        out_path = (out_dir / filename).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        figure.savefig(str(out_path))
        self._logger.info("Figure saved to %s", out_path)
