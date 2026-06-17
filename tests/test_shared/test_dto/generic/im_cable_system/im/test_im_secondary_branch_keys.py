"""``ImSecondaryCageBranchType`` / ``ImCageMultiplicityType`` テスト。

カバー対象:
    - 2 つの Enum の値整合
    - ``expected_branch_keys_for_cage_multiplicity`` の対応関係
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    expected_branch_keys_for_cage_multiplicity,
)


class TestImCageMultiplicityType:
    def test_single_cage_value(self) -> None:
        assert ImCageMultiplicityType.SINGLE_CAGE.value == "SINGLE_CAGE"

    def test_double_cage_value(self) -> None:
        assert ImCageMultiplicityType.DOUBLE_CAGE.value == "DOUBLE_CAGE"


class TestImSecondaryCageBranchType:
    def test_branch_values(self) -> None:
        assert ImSecondaryCageBranchType.SINGLE.value == "SINGLE"
        assert ImSecondaryCageBranchType.INNER.value == "INNER"
        assert ImSecondaryCageBranchType.OUTER.value == "OUTER"


class TestExpectedBranchKeys:
    def test_single_cage_returns_single_only(self) -> None:
        keys = expected_branch_keys_for_cage_multiplicity(
            ImCageMultiplicityType.SINGLE_CAGE
        )
        assert keys == frozenset({ImSecondaryCageBranchType.SINGLE})

    def test_double_cage_returns_inner_outer(self) -> None:
        keys = expected_branch_keys_for_cage_multiplicity(
            ImCageMultiplicityType.DOUBLE_CAGE
        )
        assert keys == frozenset(
            {
                ImSecondaryCageBranchType.INNER,
                ImSecondaryCageBranchType.OUTER,
            }
        )

    def test_returns_frozenset(self) -> None:
        keys = expected_branch_keys_for_cage_multiplicity(
            ImCageMultiplicityType.SINGLE_CAGE
        )
        assert isinstance(keys, frozenset)
