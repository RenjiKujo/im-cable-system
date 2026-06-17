"""``catalog_vs_sim_curve_rows`` の単体テスト。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import pytest

import im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.catalog_vs_sim_curve_rows as rows_module  # noqa: E501
from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.catalog_vs_sim_curve_rows import (  # noqa: E501, PLC2701
    build_simulated_curve_rows_matching_input_estimate_params_csv,
    nameplate_power_current_w_a_for_estimate_params_table,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto


class TestNameplatePowerCurrent:
    """名板 P / I の抽出と検証。"""

    def test_returns_nameplate_w_and_a(
        self,
        build_estimate_params_output_dto: Callable[..., OutputDto],
    ) -> None:
        output_dto = build_estimate_params_output_dto()
        p_w, i_a = nameplate_power_current_w_a_for_estimate_params_table(
            output_dto,
        )
        assert p_w == 1000.0
        assert i_a == 10.0

    def test_raises_when_nameplate_power_non_positive(
        self,
        build_estimate_params_output_dto: Callable[..., OutputDto],
    ) -> None:
        output_dto = build_estimate_params_output_dto()
        bad_im_series = replace(
            output_dto.im.im_series,
            nameplate_power=replace(
                output_dto.im.im_series.nameplate_power,
                value=0.0,
            ),
        )
        bad_im = replace(output_dto.im, im_series=bad_im_series)
        bad_output = replace(output_dto, im=bad_im)
        with pytest.raises(ValueError, match="nameplate_power"):
            nameplate_power_current_w_a_for_estimate_params_table(bad_output)


class TestBuildSimulatedCurveRows:
    """sim/catalog 比較曲線行の組み立て。"""

    def test_returns_none_when_slip_axis_missing(
        self,
        build_estimate_params_output_dto: Callable[..., OutputDto],
    ) -> None:
        bad_output = build_estimate_params_output_dto(
            reference_axes=[ArrayKey.FREQUENCY],
        )
        assert (
            build_simulated_curve_rows_matching_input_estimate_params_csv(
                bad_output,
            )
            is None
        )

    def test_returns_rows_when_curve_data_available(
        self,
        build_estimate_params_output_dto: Callable[..., OutputDto],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        output_dto = build_estimate_params_output_dto()

        class _CurveData:
            slip_fraction = [0.1, 0.2]
            target_p = [100.0, 200.0]
            target_i = [10.0, 20.0]
            target_pf = [0.8, 0.9]
            target_eta = [0.85, 0.95]
            catalog_rpm = [1800.0, 1750.0]
            pred_p = [101.0, 201.0]
            pred_i = [11.0, 21.0]
            pred_pf = [0.81, 0.91]
            pred_eta = [0.86, 0.96]

        monkeypatch.setattr(
            rows_module,
            "build_catalog_vs_sim_curve_data",
            lambda _dto: _CurveData(),
        )

        result = build_simulated_curve_rows_matching_input_estimate_params_csv(
            output_dto,
        )
        assert result is not None
        rows, n_points = result
        assert n_points == 2
        assert len(rows) == 2
        assert len(rows[0]) == 12
