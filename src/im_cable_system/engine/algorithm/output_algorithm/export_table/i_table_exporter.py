"""表 export ステップ（表 artifact のファイル保存）のインターフェース。

build と分離した I/O 専用ステップ。エクスポート可否（ON/OFF）の判定は
呼び出し側（orchestrator）が config フラグで行い、本ステップは渡された
表 DataFrame の保存のみを担う（表の生成・加工はしない）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pandas import DataFrame

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class ITableExporter(ABC):
    """表 DataFrame をファイルへ保存する契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ITableExporter:
        """config / logger からエクスポーターを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ITableExporter: 生成されたエクスポーター。
        """
        pass

    @abstractmethod
    def export(self, table: DataFrame, output_dto: OutputDto) -> None:
        """渡された表 DataFrame をそのままファイルへ保存する。

        本ステップは DataFrame を変更・再構築しない（生成・加工は make_table
        の責務）。保存先・ファイル名は ``config.dump_data_config.tables``
        （sub_dir / filename_pattern）に従う。

        ``output_dto`` の用途（意図）:
            現状の filename_pattern（``tbl_{kind}_{timestamp}.csv``）では
            未使用だが、将来ファイル名・サブディレクトリに系統名
            （``output_dto.name``）や ``{kind}`` 等の文脈を反映できるよう
            受け取っておく。表の中身には用いない。

        Args:
            table: 保存対象の DataFrame（完成済み）。
            output_dto: 出力データ DTO（ファイル名文脈。現状未使用）。
        """
        pass
