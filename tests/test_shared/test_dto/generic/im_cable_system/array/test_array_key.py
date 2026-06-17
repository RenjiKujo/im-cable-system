"""``ArrayKey`` Enum と分類メソッドのテスト。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey


class TestArrayKeyValues:
    def test_member_str_subclass(self) -> None:
        assert ArrayKey.SLIP == "slip"
        assert ArrayKey.FREQUENCY == "frequency"
        assert isinstance(ArrayKey.SLIP, str)

    def test_double_cage_keys(self) -> None:
        assert (
            ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT.value
            == "double_cage_im_secondary_inner_current"
        )
        assert (
            ArrayKey.DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT.value
            == "double_cage_im_secondary_outer_current"
        )

    def test_pie_cable_keys_dot_namespaced(self) -> None:
        # CONDUCTOR_CURRENT_PIE_SINGLE は dot 区切りで PieCableConductorKey と
        # 整合した値を持つ
        assert (
            ArrayKey.CONDUCTOR_CURRENT_PIE_SINGLE.value
            == "conductor_current.pie_single"
        )
        assert (
            ArrayKey.GROUND_CURRENT_PIE_UPSTREAM.value
            == "ground_current.pie_upstream"
        )
        assert (
            ArrayKey.GROUND_CURRENT_PIE_DOWNSTREAM.value
            == "ground_current.pie_downstream"
        )


class TestArrayKeyClassifiers:
    def test_reference_axes_members(self) -> None:
        members = ArrayKey.reference_axes_members()
        assert ArrayKey.SLIP in members
        assert ArrayKey.FREQUENCY in members
        assert ArrayKey.INPUT_LINE_VOLTAGE in members
        # 電流系（ケーブル入力線電流・IM 内部電流など）は reference_axes には含まれない
        assert ArrayKey.INPUT_LINE_CURRENT not in members
        assert ArrayKey.IM_INPUT_CURRENT not in members
        assert ArrayKey.IM_PRIMARY_CURRENT not in members

    def test_reference_axis_values(self) -> None:
        values = ArrayKey.reference_axis_values()
        assert isinstance(values, frozenset)
        assert "slip" in values
        assert "frequency" in values
        # 非候補は含まれない
        assert "im_input_current" not in values

    def test_all_array_key_values_contains_all_members(self) -> None:
        values = ArrayKey.all_array_key_values()
        assert isinstance(values, frozenset)
        for member in ArrayKey:
            assert member.value in values
