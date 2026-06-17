"""make_report ステップ（構造化レポートの組み立て）のインターフェース。

OutputDto から :class:`ReportDto` を組み立てる契約。I/O は行わず（export_report
の責務）、純粋にデータを構築する。対象外（フィット要約を持たない出力）の
場合は ``None`` を返す。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.algorithm.output_algorithm.make_report.report_dto import (  # noqa: E501
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class IReportBuilder(ABC):
    """OutputDto から構造化レポート DTO を組み立てる契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IReportBuilder:
        """config / logger からビルダーを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IReportBuilder: 生成されたビルダー。
        """
        pass

    @abstractmethod
    def build(self, output_dto: OutputDto) -> ReportDto | None:
        """OutputDto から :class:`ReportDto` を組み立てる。

        Args:
            output_dto: 単一の出力トップ DTO。

        Returns:
            ReportDto: 構造化レポート。対象外（フィット要約無し）は None。
        """
        pass
