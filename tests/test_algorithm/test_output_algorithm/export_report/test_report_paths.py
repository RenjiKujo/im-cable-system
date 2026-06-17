"""``report_paths`` ヘルパーの単体テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.output_algorithm.export_report.report_paths import (  # noqa: E501, PLC2701
    format_report_filename,
    safe_system_name,
)


class TestReportPaths:
    """ファイル名整形と系統名の無害化。"""

    def test_safe_system_name_replaces_path_separators(self) -> None:
        assert safe_system_name("A/B\\C") == "A_B_C"

    def test_format_report_filename_with_all_placeholders(self) -> None:
        filename = format_report_filename(
            "report_{im_cable_system_name}_{timestamp}.csv",
            timestamp="20260101T120000",
            im_cable_system_name="SYS",
        )
        assert filename == "report_SYS_20260101T120000.csv"

    def test_format_report_filename_ignores_unused_kwargs(self) -> None:
        filename = format_report_filename(
            "report_{im_cable_system_name}.csv",
            timestamp="20260101T120000",
            im_cable_system_name="SYS",
        )
        assert filename == "report_SYS.csv"

    def test_format_report_filename_raises_on_unknown_placeholder(self) -> None:
        with pytest.raises(KeyError):
            format_report_filename(
                "report_{unknown}.csv",
                timestamp="20260101T120000",
                im_cable_system_name="SYS",
            )
