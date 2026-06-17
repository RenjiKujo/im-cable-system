"""フィット記述子の収集（collect_descriptors）。

かご重数ストラテジ（IM）とケーブル記述子を束ね、IM/ケーブルの区切り情報付き
記述子集合（:class:`FitDescriptorSet`）を返すコレクタを公開する。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.fit_descriptor_collector import (  # noqa: E501
    FitDescriptorCollector,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.fit_descriptor_set import (  # noqa: E501
    FitDescriptorSet,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.i_fit_descriptor_collector import (  # noqa: E501
    IFitDescriptorCollector,
)

__all__: list[str] = [
    "FitDescriptorCollector",
    "FitDescriptorSet",
    "IFitDescriptorCollector",
]
