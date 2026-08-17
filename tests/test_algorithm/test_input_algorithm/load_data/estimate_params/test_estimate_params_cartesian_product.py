"""``cartesian_product.iter_model_combos`` の単体テスト。

単一かご run と二重かご run が、`candidate_secondary_single` /
`candidate_secondary_double_*` の指定に応じて適切に分離・連結されて
yield されることを確認する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    iter_model_combos,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
)


def _make_parsed(
    *,
    candidate_primary: tuple[str, ...] = ("BASIC",),
    candidate_excitation: tuple[str, ...] = ("BASIC",),
    candidate_secondary_single: tuple[str, ...] = (),
    candidate_secondary_double_inner: tuple[str, ...] = (),
    candidate_secondary_double_outer: tuple[str, ...] = (),
    candidate_friction_windage: tuple[str, ...] = ("NONE",),
    candidate_stray_load: tuple[str, ...] = ("NONE",),
    candidate_cable_conductor: tuple[str, ...] = (),
) -> EstimateParamsParsedTables:
    """テスト用 ParsedTables。fw/sl は必須軸なので既定でも ``NONE`` を
    1 件持つ（``unified_input_parser`` が保証する契約を模す）。"""
    return EstimateParamsParsedTables(
        im_performance_curve_name="dummy",
        nameplate_block={},
        fixed={},
        candidate_primary=candidate_primary,
        candidate_excitation=candidate_excitation,
        candidate_secondary_single=candidate_secondary_single,
        candidate_secondary_double_inner=candidate_secondary_double_inner,
        candidate_secondary_double_outer=candidate_secondary_double_outer,
        candidate_friction_windage=candidate_friction_windage,
        candidate_stray_load=candidate_stray_load,
        candidate_cable_conductor=candidate_cable_conductor,
        supply_block={},
        curve_header_row=[],
        curve_unit_row=[],
        curve_data_rows=[],
    )


class TestIterModelCombosSingleOnly:
    """``single`` のみ指定。"""

    def test_yields_single_cage_combos_only(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_single=(
                "BASIC",
                "SLIP_DEPENDENT_SKIN_EFFECT_V1",
            ),
        )
        combos = list(iter_model_combos(parsed, include_cable=False))
        assert len(combos) == 2
        assert all(c.secondary_inner is None for c in combos)
        assert all(c.cable_conductor is None for c in combos)
        assert {c.secondary_outer.value for c in combos} == {
            "BASIC",
            "SLIP_DEPENDENT_SKIN_EFFECT_V1",
        }


class TestIterModelCombosDoubleOnly:
    """``double_inner`` と ``double_outer`` 同時指定（``single`` 無し）。"""

    def test_yields_double_cage_combos_only(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_double_inner=("BASIC",),
            candidate_secondary_double_outer=("BASIC",),
        )
        combos = list(iter_model_combos(parsed, include_cable=False))
        assert len(combos) == 1
        assert all(c.secondary_inner is not None for c in combos)
        assert combos[0].secondary_outer is not None
        assert combos[0].secondary_inner is not None
        assert combos[0].secondary_outer.value == "BASIC"
        assert combos[0].secondary_inner.value == "BASIC"


class TestIterModelCombosMixed:
    """``single`` と ``double_inner/outer`` を同時指定したケース。"""

    def test_yields_single_run_then_double_run(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_single=(
                "BASIC",
                "SLIP_DEPENDENT_SKIN_EFFECT_V1",
            ),
            candidate_secondary_double_inner=("BASIC",),
            candidate_secondary_double_outer=("BASIC",),
        )
        combos = list(iter_model_combos(parsed, include_cable=False))
        # 単一かご 2 + 二重かご 1 = 3
        assert len(combos) == 3
        # 順序: single 群が先
        assert combos[0].secondary_inner is None
        assert combos[1].secondary_inner is None
        assert combos[2].secondary_inner is not None


class TestIterModelCombosWithCableAxis:
    """ケーブル軸の有無による直積数の変化。"""

    def test_cable_axis_doubles_combos_when_used(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_single=("BASIC",),
            candidate_cable_conductor=(
                "BASIC",
                "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1",
            ),
        )
        combos = list(iter_model_combos(parsed, include_cable=True))
        assert len(combos) == 2
        assert {
            c.cable_conductor.value for c in combos if c.cable_conductor
        } == {
            "BASIC",
            "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1",
        }

    def test_cable_axis_skipped_when_include_cable_false(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_single=("BASIC",),
            candidate_cable_conductor=("BASIC",),
        )
        combos = list(iter_model_combos(parsed, include_cable=False))
        assert len(combos) == 1
        assert combos[0].cable_conductor is None

    def test_cable_axis_skipped_when_no_candidates(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_single=("BASIC",),
            candidate_cable_conductor=(),
        )
        combos = list(iter_model_combos(parsed, include_cable=True))
        assert len(combos) == 1
        assert combos[0].cable_conductor is None


class TestIterModelCombosFullProduct:
    """全軸非空のときの直積要素数チェック。"""

    def test_full_product_size_matches_expectation(self) -> None:
        parsed = _make_parsed(
            candidate_primary=("BASIC", "BASIC"),
            candidate_excitation=("BASIC", "BASIC"),
            candidate_secondary_single=("BASIC", "BASIC"),
            candidate_cable_conductor=("BASIC", "BASIC"),
        )
        combos = list(iter_model_combos(parsed, include_cable=True))
        # 2 × 2 × 2 × 2 = 16
        assert len(combos) == 16


class TestIterModelCombosCableNoneToken:
    """ケーブル軸に ``NONE`` 候補が含まれるケース。"""

    def test_none_token_maps_to_no_cable_combo(self) -> None:
        """``NONE`` 候補は ``cable_conductor is None`` の combo を yield する。"""
        parsed = _make_parsed(
            candidate_secondary_single=("BASIC",),
            candidate_cable_conductor=("NONE", "BASIC"),
        )
        combos = list(iter_model_combos(parsed, include_cable=True))
        assert len(combos) == 2
        none_combos = [c for c in combos if c.cable_conductor is None]
        cable_combos = [c for c in combos if c.cable_conductor is not None]
        assert len(none_combos) == 1
        assert len(cable_combos) == 1
        # ``NONE`` は 1-based 列番号 1、``BASIC`` は列番号 2 を保持する。
        assert none_combos[0].cable_conductor_index == 1
        assert cable_combos[0].cable_conductor_index == 2
        assert cable_combos[0].cable_conductor is not None
        assert cable_combos[0].cable_conductor.value == "BASIC"


class TestIterModelCombosFrictionWindageStrayLoadNoneOnly:
    """``NONE`` のみを指定した場合、組み合わせは 1 件のまま増えない。

    行を省略できた旧フォールバック挙動と数値的に同一であることを固定する
    回帰テスト（出力名・直積件数がこの変更で変わらないことの根拠）。
    """

    def test_none_only_axis_yields_single_combo_with_index_one(self) -> None:
        parsed = _make_parsed(candidate_secondary_single=("BASIC",))
        combos = list(iter_model_combos(parsed, include_cable=False))
        assert len(combos) == 1
        assert combos[0].friction_windage.value == "NONE"
        assert combos[0].stray_load.value == "NONE"
        # この軸は必ず採用されるため常に 1-based（0 は使わない）。
        assert combos[0].friction_windage_index == 1
        assert combos[0].stray_load_index == 1


class TestIterModelCombosFrictionWindageStrayLoadMultiplication:
    """両行に 2 候補を書くと組み合わせが最大 4 倍になる。"""

    def test_two_candidates_each_axis_quadruples_combos(self) -> None:
        parsed = _make_parsed(
            candidate_secondary_single=("BASIC",),
            candidate_friction_windage=("NONE", "CONSTANT_V1"),
            candidate_stray_load=("NONE", "CURRENT_DEPENDENT_QUADRATIC_V1"),
        )
        combos = list(iter_model_combos(parsed, include_cable=False))
        assert len(combos) == 4
        seen = {(c.friction_windage.value, c.stray_load.value) for c in combos}
        assert seen == {
            ("NONE", "NONE"),
            ("NONE", "CURRENT_DEPENDENT_QUADRATIC_V1"),
            ("CONSTANT_V1", "NONE"),
            ("CONSTANT_V1", "CURRENT_DEPENDENT_QUADRATIC_V1"),
        }
        # index は 1-based で候補列順と対応する。
        indices = {
            (c.friction_windage.value, c.friction_windage_index) for c in combos
        }
        assert indices == {("NONE", 1), ("CONSTANT_V1", 2)}
