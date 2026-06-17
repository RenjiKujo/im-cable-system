"""``build_catalog_vs_sim_curve_data`` の単体テスト（レポート専用）。

シミュ予測抽出（``_simulated_pred_arrays``）は stub に差し替え、カタログ
スリップ補間（マスク適用）と比較データ組み立てのロジックを検証する。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np

import im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.curve_sampling as ecs  # noqa: E501
from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.curve_sampling import (  # noqa: E501
    CatalogVsSimCurveData,
    build_catalog_vs_sim_curve_data,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImPerformanceCurveCatalogDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayComplexVoltageDto,
    ArrayCurrentMagnitudeDto,
    ArrayEfficiencyDto,
    ArrayFrequencyDto,
    ArrayPowerFactorDto,
    ArraySlipDto,
    FloatFrequencyDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.output import OutputDto

_F_HZ = 60.0
_V_V = 400.0
_SLIPS = [0.02, 0.04]
_N_GRID = len(_SLIPS)
_CAT_SLIP = np.array([0.0, 0.05, 0.10], dtype=np.float64)


def _layout() -> ArrayLayoutDto:
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.array(_SLIPS, dtype=np.float64),
                unit="-",
            ),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([_F_HZ], dtype=np.float64),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.array([_V_V + 0.0j], dtype=np.complex128),
                unit="V",
            ),
        },
        reference_axes=[
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        ],
    )


def _catalog_with_current_unobserved() -> ImPerformanceCurveCatalogDtos:
    """|I| だけ全点未観測（mask 全 False）のカタログ。"""
    cat = ImPerformanceCurveCatalogDto(
        name="cat_60Hz_400V",
        supply_frequency=FloatFrequencyDto(value=_F_HZ, unit="Hz"),
        supply_voltage=FloatVoltageDto(value=_V_V, unit="V"),
        slip_series=ArraySlipDto(value=_CAT_SLIP.copy(), unit="-"),
        power_series=ArrayActivePowerDto(
            value=np.array([100.0, 200.0, 300.0], dtype=np.float64),
            unit="W",
        ),
        power_series_mask=np.array([True, True, True], dtype=bool),
        current_series=ArrayCurrentMagnitudeDto(
            value=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            unit="A",
        ),
        current_series_mask=np.array([False, False, False], dtype=bool),
        power_factor_series=ArrayPowerFactorDto(
            value=np.array([0.80, 0.85, 0.90], dtype=np.float64),
            unit="-",
        ),
        power_factor_series_mask=np.array([True, True, True], dtype=bool),
        efficiency_series=ArrayEfficiencyDto(
            value=np.array([0.90, 0.91, 0.92], dtype=np.float64),
            unit="-",
        ),
        efficiency_series_mask=np.array([True, True, True], dtype=bool),
    )
    return ImPerformanceCurveCatalogDtos(objects=[cat])


def _fake_pred_arrays() -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray
]:
    """格子点数に合わせた stub の予測 (|I|, P, PF, η)。"""
    return (
        np.array([5.0, 5.0], dtype=np.float64),
        np.array([0.0, 0.0], dtype=np.float64),
        np.array([0.0, 0.0], dtype=np.float64),
        np.array([0.0, 0.0], dtype=np.float64),
    )


def _output_stub() -> SimpleNamespace:
    return SimpleNamespace(
        array_layout=_layout(),
        im_pc_catalogs=_catalog_with_current_unobserved(),
    )


class TestBuildCatalogVsSimCurveData:
    """カタログ補間目標とシミュ予測の組み立て。"""

    def test_returns_none_when_reference_axis_missing(self) -> None:
        """必要な参照軸（SLIP 等）が無い場合は None。"""
        layout = ArrayLayoutDto(
            arrays={
                ArrayKey.FREQUENCY: ArrayFrequencyDto(
                    value=np.array([_F_HZ], dtype=np.float64),
                    unit="Hz",
                ),
            },
            reference_axes=[ArrayKey.FREQUENCY],
        )
        output = SimpleNamespace(
            array_layout=layout,
            im_pc_catalogs=_catalog_with_current_unobserved(),
        )
        assert build_catalog_vs_sim_curve_data(cast(OutputDto, output)) is None

    def test_catalog_interpolation_and_pred_passthrough(
        self,
        monkeypatch,
    ) -> None:
        """|I| 未観測は target_i が NaN、他チャネルは補間値が入る。"""
        monkeypatch.setattr(
            ecs,
            "_simulated_pred_arrays",
            lambda _output: _fake_pred_arrays(),
        )
        data = build_catalog_vs_sim_curve_data(cast(OutputDto, _output_stub()))
        assert data is not None
        assert isinstance(data, CatalogVsSimCurveData)
        assert data.slip_fraction.size == _N_GRID
        assert np.all(np.isnan(data.target_i))
        assert np.all(np.isfinite(data.target_p))
        assert np.allclose(data.pred_i, np.array([5.0, 5.0]))
        # 回転速度系列が無いカタログのため catalog_rpm は全 NaN。
        assert np.all(np.isnan(data.catalog_rpm))
