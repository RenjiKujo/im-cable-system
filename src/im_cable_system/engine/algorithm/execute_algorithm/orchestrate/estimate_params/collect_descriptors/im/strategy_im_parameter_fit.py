"""strategy: IM パラメータフィットのストラテジ（IF・単一かご・二重かご）。

二次かご枝の重数だけが記述子の並びを変える。一次・励磁・結線・回路形は推定対象外。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSecondaryCageBranchType,
    ImSeriesDto,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    ImParameterFitDescriptorBounds,
)

from .descriptor_build import (
    append_primary_and_excitation_fixed_rl_descriptors,
    append_primary_and_excitation_model_param_descriptors,
    append_secondary_branch_fixed_rl_descriptors,
    append_secondary_branch_model_param_descriptors,
)


class IImParameterFitStrategy(ABC):
    """IM シリーズに対するフィット記述子の収集ストラテジ。

    記述子の path は :func:`apply_im_from_descriptors` が解釈できる形式に統一する。
    ケーブル R/L/C は本 IF の外で付与する。
    """

    @abstractmethod
    def collect_im_descriptors(
        self,
        im_series: ImSeriesDto,
        bounds: ImParameterFitDescriptorBounds,
    ) -> list[FittableParamDescriptor]:
        """IM 部分のフィット対象記述子を構築する。

        Args:
            im_series: 対象の IM シリーズ DTO。
            bounds: 記述子の探索上下限（im_descriptor_bounds_and_init.yaml 由来）。

        Returns:
            記述子リスト（一次・励磁・二次枝ごとの R/L とモデル params）。
        """
        pass


class SingleCageImParameterFitStrategy(IImParameterFitStrategy):
    """単一かご（SINGLE 枝のみ）の記述子収集。"""

    @classmethod
    def create(cls) -> SingleCageImParameterFitStrategy:
        """インスタンスを生成する。"""
        return cls()

    def collect_im_descriptors(
        self,
        im_series: ImSeriesDto,
        bounds: ImParameterFitDescriptorBounds,
    ) -> list[FittableParamDescriptor]:
        """一次・励磁・SINGLE 二次の記述子を構築する。"""
        descriptors: list[FittableParamDescriptor] = []
        append_primary_and_excitation_fixed_rl_descriptors(
            im_series, bounds, descriptors
        )
        append_secondary_branch_fixed_rl_descriptors(
            im_series,
            ImSecondaryCageBranchType.SINGLE,
            bounds,
            descriptors,
        )
        append_primary_and_excitation_model_param_descriptors(
            im_series,
            bounds,
            descriptors,
        )
        append_secondary_branch_model_param_descriptors(
            im_series,
            ImSecondaryCageBranchType.SINGLE,
            bounds,
            descriptors,
        )
        return descriptors


class DoubleCageImParameterFitStrategy(IImParameterFitStrategy):
    """二重かご（INNER / OUTER）の記述子収集。

    順序: 一次・励磁固定 R/L → INNER/OUTER 二次 R/L → 一次・励磁モデル params
    → INNER 二次モデル params → OUTER 二次モデル params。
    """

    @classmethod
    def create(cls) -> DoubleCageImParameterFitStrategy:
        """インスタンスを生成する。"""
        return cls()

    def collect_im_descriptors(
        self,
        im_series: ImSeriesDto,
        bounds: ImParameterFitDescriptorBounds,
    ) -> list[FittableParamDescriptor]:
        """二重かご向け IM 記述子を構築する。"""
        descriptors: list[FittableParamDescriptor] = []
        append_primary_and_excitation_fixed_rl_descriptors(
            im_series,
            bounds,
            descriptors,
        )
        for branch in (
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        ):
            append_secondary_branch_fixed_rl_descriptors(
                im_series,
                branch,
                bounds,
                descriptors,
            )
        append_primary_and_excitation_model_param_descriptors(
            im_series,
            bounds,
            descriptors,
        )
        for branch in (
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        ):
            append_secondary_branch_model_param_descriptors(
                im_series,
                branch,
                bounds,
                descriptors,
            )
        return descriptors
