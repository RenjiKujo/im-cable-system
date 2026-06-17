"""``unified_input_parser`` の単体テスト。

統合 TSV テキストを書き出し、各種スキーマ違反（必須セクション欠落、
必須軸欠落、重複ラベル、double_inner/double_outer 片方欠如、未知ラベル、
名盤・供給キー重複、曲線単位行欠落など）が ``ValueError`` として
検出されることを確認する。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    parse_unified_estimate_params_csv,
)


def _minimal_meta_and_fixed() -> str:
    """最小限のヘッダ・nameplate・fixed・supply ブロック。"""
    return (
        "im_performance_curve_name\tCurve01\n"
        "\n"
        "nameplate\tvalue\tunit\n"
        "input_line_voltage\t400\tV\n"
        "input_line_current\t10\tA\n"
        "output_power\t5000\tW\n"
        "frequency\t50\tHz\n"
        "\n"
        "fixed_model_key\tvalue\n"
        "im_poles\t4\n"
        "im_circuit_type\tT\n"
        "im_connection_type\tDELTA\n"
        "cable_length\t0\tft\n"
        "\n"
    )


def _supply_and_curve_block() -> str:
    return (
        "supply\tvalue\tunit\n"
        "frequency\t50\tHz\n"
        "voltage\t400\tV\n"
        "\n"
        "rotational_speed\tpower\n"
        "[rpm]\t[-]\n"
        "1500\t0.01\n"
    )


def _candidate_axis_block_single() -> str:
    """``single`` のみ指定の最小候補軸ブロック。"""
    return (
        "model_candidate_axis\tcandidate_1\n"
        "im_primary\tBASIC\n"
        "im_excitation\tBASIC\n"
        "im_secondary(single)\tBASIC\n"
        "\n"
    )


def _full_tsv_single_only(tmp_path: Path) -> Path:
    """``single`` 系列だけを持つ最小限の TSV。"""
    path = tmp_path / "unified_single.tsv"
    path.write_text(
        _minimal_meta_and_fixed()
        + _candidate_axis_block_single()
        + _supply_and_curve_block(),
        encoding="utf-8",
    )
    return path


class TestParseUnifiedHappyPath:
    """正常系。"""

    def test_single_only_returns_separated_axes(self, tmp_path: Path) -> None:
        parsed = parse_unified_estimate_params_csv(
            _full_tsv_single_only(tmp_path)
        )
        assert parsed.candidate_secondary_single == ("BASIC",)
        assert parsed.candidate_secondary_double_inner == ()
        assert parsed.candidate_secondary_double_outer == ()
        assert parsed.candidate_primary == ("BASIC",)
        assert parsed.candidate_excitation == ("BASIC",)

    def test_double_only_returns_separated_axes(self, tmp_path: Path) -> None:
        path = tmp_path / "unified_double.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "im_secondary(double_inner)\tBASIC\n"
            "im_secondary(double_outer)\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        parsed = parse_unified_estimate_params_csv(path)
        assert parsed.candidate_secondary_single == ()
        assert parsed.candidate_secondary_double_inner == ("BASIC",)
        assert parsed.candidate_secondary_double_outer == ("BASIC",)

    def test_single_and_double_can_coexist(self, tmp_path: Path) -> None:
        """``single`` と ``double_inner/outer`` を同時指定できる。"""
        path = tmp_path / "unified_mixed.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "im_secondary(single)\tBASIC\n"
            "im_secondary(double_inner)\tBASIC\n"
            "im_secondary(double_outer)\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        parsed = parse_unified_estimate_params_csv(path)
        assert parsed.candidate_secondary_single == ("BASIC",)
        assert parsed.candidate_secondary_double_inner == ("BASIC",)
        assert parsed.candidate_secondary_double_outer == ("BASIC",)


class TestParseUnifiedRequiredAxisChecks:
    """必須軸チェック。"""

    def test_missing_primary_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "unified_no_primary.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\n"
            "im_excitation\tBASIC\n"
            "im_secondary(single)\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="im_primary 候補がありません"):
            parse_unified_estimate_params_csv(path)

    def test_missing_excitation_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "unified_no_exc.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\n"
            "im_secondary(single)\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="im_excitation 候補がありません"):
            parse_unified_estimate_params_csv(path)

    def test_no_secondary_at_all_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "unified_no_sec.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="im_secondary"):
            parse_unified_estimate_params_csv(path)

    def test_double_inner_only_raises(self, tmp_path: Path) -> None:
        """``double_inner`` だけは不正（``double_outer`` も必要）。"""
        path = tmp_path / "unified_inner_only.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "im_secondary(double_inner)\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="double_inner.*double_outer"):
            parse_unified_estimate_params_csv(path)

    def test_double_outer_only_raises(self, tmp_path: Path) -> None:
        """``double_outer`` だけは不正（``double_inner`` も必要）。"""
        path = tmp_path / "unified_outer_only.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "im_secondary(double_outer)\tBASIC\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="double_inner.*double_outer"):
            parse_unified_estimate_params_csv(path)


class TestParseUnifiedDuplicateLabels:
    """同じ軸ラベルが複数行現れる場合の重複エラー。"""

    def test_duplicate_single_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "unified_dup_single.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "im_secondary(single)\tBASIC\n"
            "im_secondary(single)\tSLIP_DEPENDENT_SKIN_EFFECT_V1\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(
            ValueError,
            match=r"同じ軸 'secondary_single' の行が重複",
        ):
            parse_unified_estimate_params_csv(path)


class TestParseUnifiedUnknownLabel:
    """未知ラベルはエラー。"""

    def test_unknown_label_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "unified_unknown_label.tsv"
        path.write_text(
            _minimal_meta_and_fixed() + "model_candidate_axis\tcandidate_1\n"
            "im_primary\tBASIC\n"
            "im_excitation\tBASIC\n"
            "im_secondary(single)\tBASIC\n"
            "unknown_axis\tFOO\n"
            "\n" + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="未知のラベル"):
            parse_unified_estimate_params_csv(path)


class TestParseUnifiedRequiredSections:
    """必須セクション欠落エラー。"""

    def test_missing_supply_section_raises(self, tmp_path: Path) -> None:
        """``supply`` セクション無しはエラー。"""
        path = tmp_path / "unified_no_supply.tsv"
        path.write_text(
            _minimal_meta_and_fixed()
            + _candidate_axis_block_single()
            + "rotational_speed\tpower\n"
            "[rpm]\t[-]\n"
            "1500\t0.01\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="supply"):
            parse_unified_estimate_params_csv(path)

    def test_duplicate_nameplate_raises(self, tmp_path: Path) -> None:
        """``nameplate`` セクションが 2 回現れるとエラー。"""
        path = tmp_path / "unified_dup_nameplate.tsv"
        path.write_text(
            "im_performance_curve_name\tCurve01\n"
            "\n"
            "nameplate\tvalue\tunit\n"
            "input_line_voltage\t400\tV\n"
            "input_line_current\t10\tA\n"
            "output_power\t5000\tW\n"
            "frequency\t50\tHz\n"
            "\n"
            "nameplate\tvalue\tunit\n"
            "input_line_voltage\t380\tV\n"
            "\n"
            "fixed_model_key\tvalue\n"
            "im_poles\t4\n"
            "im_circuit_type\tT\n"
            "im_connection_type\tDELTA\n"
            "cable_length\t0\tft\n"
            "\n" + _candidate_axis_block_single() + _supply_and_curve_block(),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match=r"nameplate.*回現れます"):
            parse_unified_estimate_params_csv(path)

    def test_missing_curve_unit_row_raises(self, tmp_path: Path) -> None:
        """単位行が無いとエラー。"""
        path = tmp_path / "unified_no_unit.tsv"
        path.write_text(
            _minimal_meta_and_fixed()
            + _candidate_axis_block_single()
            + "supply\tvalue\tunit\n"
            "frequency\t50\tHz\n"
            "voltage\t400\tV\n"
            "\n"
            "rotational_speed\tpower\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="単位行がありません"):
            parse_unified_estimate_params_csv(path)
