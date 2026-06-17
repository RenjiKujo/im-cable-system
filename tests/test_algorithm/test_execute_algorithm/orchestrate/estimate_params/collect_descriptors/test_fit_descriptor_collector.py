"""FitDescriptorCollector の単体テスト。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors import (  # noqa: E501
    FitDescriptorCollector,
    IFitDescriptorCollector,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestFitDescriptorCollector:
    """記述子コレクタの生成を確認する。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェース型を返す。"""
        collector = FitDescriptorCollector.create(
            config=config,
            logger=logger,
        )
        assert isinstance(collector, IFitDescriptorCollector)
