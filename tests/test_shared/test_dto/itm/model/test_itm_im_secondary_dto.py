"""``ItmImSecondaryDto`` の dict キー検証テスト。

このクラスは「枝単位の計算結果として 1 キーのみの辞書」も許容する点が
他の cage-aware DTO と異なる（部分集合として許容）。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatInductanceDto,
    FloatResistanceDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImSecondaryDto
from tests.test_shared.test_dto.itm._itm_builders import (
    make_complex_admittance,
    make_complex_impedance,
)


def _basic_secondary_model() -> ImSecondaryModelDto:
    return ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)


def _make_rl_for_branches(
    branches: list[ImSecondaryCageBranchType],
) -> tuple[
    dict[ImSecondaryCageBranchType, FloatResistanceDto],
    dict[ImSecondaryCageBranchType, FloatInductanceDto],
]:
    """枝ごとのダミー R/L 辞書を作る（キー検証テストでは値を参照しない）。"""
    return (
        {b: FloatResistanceDto(value=1.0, unit="Ω") for b in branches},
        {b: FloatInductanceDto(value=1.0, unit="H") for b in branches},
    )


def _make_dict_for_branches(
    branches: list[ImSecondaryCageBranchType],
) -> tuple[
    dict[ImSecondaryCageBranchType, ImSecondaryModelDto],
    dict,
    dict,
    dict,
    dict,
    dict,
    dict,
]:
    return (
        {b: _basic_secondary_model() for b in branches},
        {b: make_complex_impedance() for b in branches},
        {b: make_complex_admittance() for b in branches},
        {b: make_complex_impedance() for b in branches},
        {b: make_complex_admittance() for b in branches},
        {b: make_complex_impedance() for b in branches},
        {b: make_complex_admittance() for b in branches},
    )


class TestItmImSecondaryDtoSingleCage:
    def test_single_branch_ok(self) -> None:
        models, imps, adms, b_imps, b_adms, l_imps, l_adms = (
            _make_dict_for_branches([ImSecondaryCageBranchType.SINGLE])
        )
        res, ind = _make_rl_for_branches([ImSecondaryCageBranchType.SINGLE])
        ItmImSecondaryDto(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            resistances=res,
            inductances=ind,
            models=models,
            impedances=imps,
            admittances=adms,
            base_impedances=b_imps,
            base_admittances=b_adms,
            load_impedances=l_imps,
            load_admittances=l_adms,
        )

    def test_double_branch_in_single_cage_rejected(self) -> None:
        # SINGLE_CAGE で INNER/OUTER は許容されない
        models, imps, adms, b_imps, b_adms, l_imps, l_adms = (
            _make_dict_for_branches(
                [
                    ImSecondaryCageBranchType.INNER,
                    ImSecondaryCageBranchType.OUTER,
                ]
            )
        )
        res, ind = _make_rl_for_branches(
            [
                ImSecondaryCageBranchType.INNER,
                ImSecondaryCageBranchType.OUTER,
            ]
        )
        with pytest.raises(ValueError, match="cage_multiplicity"):
            ItmImSecondaryDto(
                cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
                resistances=res,
                inductances=ind,
                models=models,
                impedances=imps,
                admittances=adms,
                base_impedances=b_imps,
                base_admittances=b_adms,
                load_impedances=l_imps,
                load_admittances=l_adms,
            )

    def test_empty_dict_rejected(self) -> None:
        # 空辞書は単独で raise する
        with pytest.raises(ValueError, match="空であってはなりません"):
            ItmImSecondaryDto(
                cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
                resistances={
                    ImSecondaryCageBranchType.SINGLE: FloatResistanceDto(
                        value=1.0, unit="Ω"
                    )
                },
                inductances={
                    ImSecondaryCageBranchType.SINGLE: FloatInductanceDto(
                        value=1.0, unit="H"
                    )
                },
                models={},
                impedances={
                    ImSecondaryCageBranchType.SINGLE: make_complex_impedance()
                },
                admittances={
                    ImSecondaryCageBranchType.SINGLE: make_complex_admittance()
                },
                base_impedances={
                    ImSecondaryCageBranchType.SINGLE: make_complex_impedance()
                },
                base_admittances={
                    ImSecondaryCageBranchType.SINGLE: make_complex_admittance()
                },
                load_impedances={
                    ImSecondaryCageBranchType.SINGLE: make_complex_impedance()
                },
                load_admittances={
                    ImSecondaryCageBranchType.SINGLE: make_complex_admittance()
                },
            )


class TestItmImSecondaryDtoDoubleCage:
    def test_full_branches_ok(self) -> None:
        models, imps, adms, b_imps, b_adms, l_imps, l_adms = (
            _make_dict_for_branches(
                [
                    ImSecondaryCageBranchType.INNER,
                    ImSecondaryCageBranchType.OUTER,
                ]
            )
        )
        res, ind = _make_rl_for_branches(
            [
                ImSecondaryCageBranchType.INNER,
                ImSecondaryCageBranchType.OUTER,
            ]
        )
        ItmImSecondaryDto(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            resistances=res,
            inductances=ind,
            models=models,
            impedances=imps,
            admittances=adms,
            base_impedances=b_imps,
            base_admittances=b_adms,
            load_impedances=l_imps,
            load_admittances=l_adms,
        )

    def test_partial_inner_only_allowed(self) -> None:
        """二重かごでも、枝単位の計算結果は INNER のみを許容する。"""
        models, imps, adms, b_imps, b_adms, l_imps, l_adms = (
            _make_dict_for_branches([ImSecondaryCageBranchType.INNER])
        )
        res, ind = _make_rl_for_branches([ImSecondaryCageBranchType.INNER])
        ItmImSecondaryDto(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            resistances=res,
            inductances=ind,
            models=models,
            impedances=imps,
            admittances=adms,
            base_impedances=b_imps,
            base_admittances=b_adms,
            load_impedances=l_imps,
            load_admittances=l_adms,
        )

    def test_single_branch_not_allowed_in_double_cage(self) -> None:
        # DOUBLE_CAGE で SINGLE は許容されない（部分集合の対象外）
        models, imps, adms, b_imps, b_adms, l_imps, l_adms = (
            _make_dict_for_branches([ImSecondaryCageBranchType.SINGLE])
        )
        res, ind = _make_rl_for_branches([ImSecondaryCageBranchType.SINGLE])
        with pytest.raises(ValueError, match="cage_multiplicity"):
            ItmImSecondaryDto(
                cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
                resistances=res,
                inductances=ind,
                models=models,
                impedances=imps,
                admittances=adms,
                base_impedances=b_imps,
                base_admittances=b_adms,
                load_impedances=l_imps,
                load_admittances=l_adms,
            )
