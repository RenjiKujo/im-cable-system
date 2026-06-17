"""``build_fitted_catalog`` の単体テスト。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.fitted_catalog_builder import (  # noqa: E501, PLC2701
    build_fitted_catalog,
)
from tests.test_algorithm.test_output_algorithm.make_report.estimate_params._estimate_params_report_helpers import (  # noqa: E501
    minimal_fit_summary,
)


class TestBuildFittedCatalog:
    """catalog 形式マッピングの組み立て。"""

    def test_builds_nested_mapping_with_metrics(self) -> None:
        summary = minimal_fit_summary()
        catalog = build_fitted_catalog(
            name="SYS01",
            summary=summary,
            nameplate_power_w=1000.0,
            nameplate_current_a=10.0,
        )
        assert catalog["name"] == "SYS01"
        assert catalog["nameplate"]["power"]["value"] == 1000.0
        assert (
            catalog["fitted_parameters"][0]["path"] == "im.primary_resistance"
        )
        assert catalog["fit_metrics"]["optimizer_success"] is True
