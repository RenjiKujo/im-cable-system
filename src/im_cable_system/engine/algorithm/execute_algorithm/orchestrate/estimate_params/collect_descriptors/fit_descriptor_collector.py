"""フィット記述子コレクタの実装。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.cable import (  # noqa: E501
    collect_cable_fittable_descriptors,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.fit_descriptor_set import (  # noqa: E501
    FitDescriptorSet,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.i_fit_descriptor_collector import (  # noqa: E501
    IFitDescriptorCollector,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.im import (  # noqa: E501
    ImParameterFitStrategyFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.config import (
    IConfig,
    ILogger,
    load_yaml_root_dict,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    ImDto,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
    ImParameterFitDescriptorBounds,
)


class FitDescriptorCollector(IFitDescriptorCollector):
    """かご重数ストラテジ（IM）とケーブル記述子を束ねる実装。

    探索上下限（bounds）の読み込みも本コレクタが担う。Config は bounds YAML の
    「パス解決」だけを担い、本コレクタが YAML 読み込みと bounds DTO 構築を行う。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFitDescriptorCollector:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def collect(
        self,
        im_dto: ImDto,
        cable_dto: CableDto | None,
    ) -> FitDescriptorSet:
        """IM とケーブルの記述子を収集する。

        探索上下限は Config の path getter から bounds YAML を読み込んで構築する。
        ケーブル bounds はケーブル入力があるときのみ読み込む（IM のみの推定が
        ケーブル設定に依存しないようにするため）。
        """
        im_bounds = self._load_im_bounds()

        im_series = im_dto.im_series
        strategy = ImParameterFitStrategyFactory.create(im_series)
        im_descriptors = strategy.collect_im_descriptors(im_series, im_bounds)
        im_count = len(im_descriptors)

        descriptors: list[FittableParamDescriptor] = list(im_descriptors)
        if cable_dto is not None:
            cable_bounds = self._load_cable_bounds()
            descriptors.extend(
                collect_cable_fittable_descriptors(cable_dto, cable_bounds)
            )
        if not descriptors:
            raise ValueError(
                "パフォーマンスカーブに対してフィット可能なパラメータが存在しません。"
            )
        return FitDescriptorSet(descriptors=descriptors, im_count=im_count)

    def _load_im_bounds(self) -> ImParameterFitDescriptorBounds:
        """IM bounds YAML を読み込む。"""
        path = self._config.get_im_bounds_and_init_file_path()
        document = load_yaml_root_dict(path)
        return ImParameterFitDescriptorBounds.from_estimation_document(document)

    def _load_cable_bounds(self) -> CableParameterFitDescriptorBounds:
        """ケーブル bounds YAML を読み込む。"""
        path = self._config.get_cable_bounds_and_init_file_path()
        document = load_yaml_root_dict(path)
        return CableParameterFitDescriptorBounds.from_estimation_document(
            document
        )
