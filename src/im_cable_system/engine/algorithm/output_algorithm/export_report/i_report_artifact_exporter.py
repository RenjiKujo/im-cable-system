"""1 件分レポート artifact の export ステップ共通インターフェース。

フィット要約 CSV / 推定モデル catalog YAML / 数値安定化イベント CSV を、
いずれも make_report が組み立てた :class:`ReportDto` を入力に保存する。
保存可否（ON/OFF）の判定は呼び出し側（orchestrator）が config フラグで行い、
本ステップは保存のみを担う。

NOTE: 入力を ReportDto に統一したため、``report`` が None（フィット要約を
    持たない出力等）のときは数値安定化イベントも含め何も出力しない。
    estimate_params では fit_summary が必須のため実害はない。集計が空の
    場合も従来どおり何も出力しない（実装側の ``is_empty()`` ガード）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class IReportArtifactExporter(ABC):
    """1 件分の :class:`ReportDto` を 1 つの artifact へ保存する契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IReportArtifactExporter:
        """config / logger からエクスポーターを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IReportArtifactExporter: 生成されたエクスポーター。
        """
        pass

    @abstractmethod
    def export(self, report: ReportDto) -> None:
        """1 件分の ReportDto を 1 つの artifact へ保存する。

        保存先・ファイル名は ``config.dump_data_config.reports`` に従う。

        Args:
            report: 保存対象の構造化レポート。
        """
        pass
