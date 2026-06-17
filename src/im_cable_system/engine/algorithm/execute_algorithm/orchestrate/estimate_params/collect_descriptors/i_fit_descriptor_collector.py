"""フィット記述子コレクタのインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.fit_descriptor_set import (  # noqa: E501
    FitDescriptorSet,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    ImDto,
)


class IFitDescriptorCollector(ABC):
    """IM とケーブルのフィット対象記述子を収集する。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFitDescriptorCollector:
        """config と logger を受け取り、自身のインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IFitDescriptorCollector: 生成された記述子コレクタ。
        """
        pass

    @abstractmethod
    def collect(
        self,
        im_dto: ImDto,
        cable_dto: CableDto | None,
    ) -> FitDescriptorSet:
        """IM（かご重数で分岐）とケーブルの記述子を収集する。

        探索上下限（bounds）は Config の path getter から bounds YAML を
        読み込んで内部で構築する。

        Args:
            im_dto: 対象の IM DTO。
            cable_dto: ケーブル DTO（1 セクション前提）。無い場合は None。

        Returns:
            FitDescriptorSet: 記述子列（先頭が IM）と IM 部の個数。

        Raises:
            ValueError: フィット可能な記述子が 1 つも無いとき、または
                bounds YAML のパス解決・形式が不正なとき。
        """
        pass
