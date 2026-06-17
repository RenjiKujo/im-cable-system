"""新出力アルゴリズムのオーケストレーター・インターフェース。

1本の ItmDto に対し convert → make_figure → make_table → (config 次第で)
export を実行し、1本の OutputDto を返す契約。図・表はファイルへの side effect
として出力し、戻り値の OutputDto には載せない。

本 IF を ``output_algorithm`` 直下に置くことで、層外（processor /
pipeline）から見える出力アルゴリズムの契約は本 IF のみであることを明示する。
具象（supply_grid / operating_points）は orchestrate サブパッケージに置く。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import ItmDto
from im_cable_system.engine.shared.dto.output import OutputDto


class IOutputOrchestrator(ABC):
    """新出力アルゴリズムの共通オーケストレーター契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IOutputOrchestrator:
        """config / logger から各ステップを束ねて生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IOutputOrchestrator: 生成されたオーケストレーター。
        """
        pass

    @abstractmethod
    def run(self, itm_dto: ItmDto) -> OutputDto:
        """convert → make_figure → make_table → (任意)export を実行する。

        図・表のエクスポート可否は config の ``figures.enabled`` /
        ``tables.enabled`` で **個別** に判定する。

        Args:
            itm_dto: 単一の中間 DTO。

        Returns:
            OutputDto: 出力データ DTO（図・表はファイル side effect）。
        """
        pass
