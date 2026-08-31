"""estimate_params 統合入力 CSV/TSV の候補軸検証・s≈0 判定。

公開窓口 ``apps.web.engine_contract`` から import する。
"""

from __future__ import annotations

from pathlib import Path

from apps.web.engine_contract import (
    find_missing_required_axes,
    find_unknown_candidate_kind_errors,
    read_rows,
    teacher_curve_has_near_zero_slip,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLE_CSV = _REPO_ROOT / "examples/input/estimate_params_input.csv"
_REQUIRED_LABELS = ("im_friction_windage", "im_stray_load")


def _example_rows() -> list[list[str]]:
    return read_rows(_EXAMPLE_CSV.read_bytes(), filename=_EXAMPLE_CSV.name)


def _drop_required_axis_rows(rows: list[list[str]]) -> list[list[str]]:
    return [
        row for row in rows if not row or row[0].strip() not in _REQUIRED_LABELS
    ]


class TestFindMissingRequiredAxes:
    """行が無い／候補セルが全て空の両方を欠落とみなす。"""

    def test_example_csv_has_no_missing_axes(self) -> None:
        assert find_missing_required_axes(_example_rows()) == []

    def test_missing_when_rows_are_absent(self) -> None:
        rows = _drop_required_axis_rows(_example_rows())

        missing = find_missing_required_axes(rows)

        assert missing == list(_REQUIRED_LABELS)

    def test_missing_when_candidate_cells_are_empty(self) -> None:
        rows = _example_rows()
        for row in rows:
            if row and row[0].strip() in _REQUIRED_LABELS:
                for idx in range(1, len(row)):
                    row[idx] = ""

        missing = find_missing_required_axes(rows)

        assert missing == list(_REQUIRED_LABELS)

    def test_missing_when_candidate_block_is_absent(self) -> None:
        rows = [["im_performance_curve_name", "dummy"], ["slip", "current"]]

        missing = find_missing_required_axes(rows)

        assert missing == list(_REQUIRED_LABELS)


class TestFindUnknownCandidateKindErrors:
    """候補セルの種別名を軸ごとの語彙と照合する。

    engine は種別名を検証せず bounds YAML 引きの ``KeyError`` にするため
    （runner の exit 1 ＝ unexpected）、投入時に拾えることをここで固定する。
    """

    def test_example_csv_has_no_unknown_kinds(self) -> None:
        assert find_unknown_candidate_kind_errors(_example_rows()) == []

    def test_typo_in_primary_is_reported_with_label_and_token(self) -> None:
        rows = [
            ["model_candidate_axis", "candidate_1"],
            ["im_primary", "SLIP_DEPENDNET_LEAKAGE_SATURATION_V1"],
            ["im_friction_windage", "NONE"],
        ]

        errors = find_unknown_candidate_kind_errors(rows)

        assert len(errors) == 1
        assert "im_primary" in errors[0]
        assert "SLIP_DEPENDNET_LEAKAGE_SATURATION_V1" in errors[0]
        assert "BASIC" in errors[0]

    def test_kind_valid_for_another_axis_is_still_rejected(self) -> None:
        """``CURRENT_DEPENDENT_SKIN_EFFECT_V1`` は secondary/導体にはあるが励磁には無い。"""
        rows = [
            ["model_candidate_axis", "candidate_1"],
            ["im_excitation", "CURRENT_DEPENDENT_SKIN_EFFECT_V1"],
        ]

        errors = find_unknown_candidate_kind_errors(rows)

        assert len(errors) == 1
        assert "im_excitation" in errors[0]

    def test_none_is_legal_for_cable_conductor(self) -> None:
        """導体軸の ``NONE`` は Enum メンバではないが「ケーブル無し」の特別値。"""
        rows = [
            ["model_candidate_axis", "candidate_1"],
            ["cable_conductor_model", "NONE"],
        ]

        assert find_unknown_candidate_kind_errors(rows) == []

    def test_unknown_axis_label_is_left_to_engine(self) -> None:
        """未知の**ラベル**は engine が ``ValueError``（exit 2）にするので触らない。"""
        rows = [
            ["model_candidate_axis", "candidate_1"],
            ["im_not_a_real_axis", "WHATEVER"],
        ]

        assert find_unknown_candidate_kind_errors(rows) == []

    def test_no_candidate_block_yields_no_errors(self) -> None:
        rows = [["slip", "current"], ["0.1", "1.0"]]

        assert find_unknown_candidate_kind_errors(rows) == []


class TestNearZeroSlip:
    """example CSV は同期速度点を含む。"""

    def test_example_csv_has_near_zero_slip(self) -> None:
        assert teacher_curve_has_near_zero_slip(_example_rows()) is True
