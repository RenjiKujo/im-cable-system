"""IM パラメータフィットストラテジのファクトリー。

二次かご枝の重数（:class:`ImCageMultiplicityType`）のみを分岐軸とする。
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSeriesDto,
    expected_branch_keys_for_cage_multiplicity,
)

from .strategy_im_parameter_fit import (
    DoubleCageImParameterFitStrategy,
    IImParameterFitStrategy,
    SingleCageImParameterFitStrategy,
)


class ImParameterFitStrategyFactory:
    """:class:`IImParameterFitStrategy` の生成。"""

    @staticmethod
    def create(im_series: ImSeriesDto) -> IImParameterFitStrategy:
        """``im_series.cage_multiplicity`` と二次辞書キーに応じてストラテジを返す。

        Args:
            im_series: IM シリーズ DTO。

        Returns:
            IImParameterFitStrategy: 単一かごまたは二重かご用実装。

        Raises:
            ValueError: 重数と ``secondary_models`` のキーが整合しない場合。
        """
        expected = expected_branch_keys_for_cage_multiplicity(
            im_series.cage_multiplicity
        )
        actual = frozenset(im_series.secondary_models.keys())
        if actual != expected:
            raise ValueError(
                "cage_multiplicity と secondary_models のキーが一致しません: "
                f"multiplicity={im_series.cage_multiplicity}, "
                f"expected_keys={sorted(b.value for b in expected)}, "
                f"actual_keys={sorted(b.value for b in actual)}"
            )
        if im_series.cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
            return SingleCageImParameterFitStrategy.create()
        if im_series.cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE:
            return DoubleCageImParameterFitStrategy.create()
        raise ValueError(
            f"未対応の cage_multiplicity: {im_series.cage_multiplicity}"
        )
