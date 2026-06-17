"""Forward 系 軸 TSV ローダの構造バリデーションテスト。

``axes_parser`` 単体での挙動を ``ForwardLoader`` 経由で確認する。
LoadData 層では値レベル検証は行わず、ヘッダ重複・必須列欠落・
データ行の幅不足など、構造・スキーマ違反のみを ``ValueError``
として上げることを担保する。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    input_files_dir,
)


def _series_forward_dir() -> Path:
    return input_files_dir() / "series_forward"


def _make_spec(
    *,
    series_csv_path: Path,
    axes_csv_path: Path,
) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=series_csv_path,
        axes_path=axes_csv_path,
    )


def _loader(config: IConfig, logger: ILogger) -> ForwardLoader:
    return ForwardLoader.create(config=config, logger=logger)


class TestForwardAxesLoaderHeaderValidation:
    """軸 TSV のヘッダおよびデータ行の構造バリデーション。"""

    def test_duplicate_required_column_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """必須列が重複していると ``ValueError``。

        ``slip`` 列を 2 回書くと、``header.index`` が最初の方を選んで
        しまい後段の集計がずれるため、Loader 段で弾く。
        """
        axes_path = tmp_path / "axes_dup_col.tsv"
        axes_path.write_text(
            "slip\tslip\tfrequency\tinput_line_voltage\n"
            "[-]\t[-]\t[Hz]\t[V]\n"
            "0\t0\t50\t200\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=_series_forward_dir() / "basic01_nocable.tsv",
            axes_csv_path=axes_path,
        )
        with pytest.raises(
            ValueError,
            match=r"必須列 'slip' が複数",
        ):
            _loader(config, logger).load(spec)

    def test_short_partial_data_row_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """非空のデータ行が必須 3 列の幅を満たさないと ``ValueError``。

        従来は黙ってスキップしていたが、部分的に埋まった短い行は
        ユーザの記入漏れである可能性が高いため、エラーとして扱う。
        """
        axes_path = tmp_path / "axes_short_row.tsv"
        axes_path.write_text(
            "slip\tfrequency\tinput_line_voltage\n"
            "[-]\t[Hz]\t[V]\n"
            "0\t50\t200\n"
            "0.001\t60\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=_series_forward_dir() / "basic01_nocable.tsv",
            axes_csv_path=axes_path,
        )
        with pytest.raises(
            ValueError,
            match="必須 3 列を満たさない行",
        ):
            _loader(config, logger).load(spec)

    def test_completely_empty_row_is_skipped(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """完全に空のデータ行はスキップされる（部分的に埋まった行と区別する）。"""
        axes_path = tmp_path / "axes_empty_row.tsv"
        axes_path.write_text(
            "slip\tfrequency\tinput_line_voltage\n"
            "[-]\t[Hz]\t[V]\n"
            "0\t50\t200\n"
            "\t\t\n"
            "0.001\t60\t115\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=_series_forward_dir() / "basic01_nocable.tsv",
            axes_csv_path=axes_path,
        )
        loaded = _loader(config, logger).load(spec)
        axes = loaded.axes
        assert axes.slip.size == 2
        assert axes.frequency.size == 2
        assert axes.input_line_voltage.size == 2
