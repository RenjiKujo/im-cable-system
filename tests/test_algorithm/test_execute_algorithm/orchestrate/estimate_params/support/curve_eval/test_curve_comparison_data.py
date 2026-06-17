"""``extract_curve_fit_comparison_data`` の単体テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np

import im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.curve_comparison_data as ccd  # noqa: E501
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval import (  # noqa: E501
    CurveFitComparisonData,
    extract_curve_fit_comparison_data,
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
from im_cable_system.engine.shared.dto.itm import ItmDto

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


def _catalog_with_power_placeholder() -> ImPerformanceCurveCatalogDtos:
    """power の中央点だけ未観測（mask False のプレースホルダ）のカタログ。"""
    cat = ImPerformanceCurveCatalogDto(
        name="cat_60Hz_400V",
        supply_frequency=FloatFrequencyDto(value=_F_HZ, unit="Hz"),
        supply_voltage=FloatVoltageDto(value=_V_V, unit="V"),
        slip_series=ArraySlipDto(value=_CAT_SLIP.copy(), unit="-"),
        # 中央点 (slip=0.05) はプレースホルダ 999、mask False。
        power_series=ArrayActivePowerDto(
            value=np.array([100.0, 999.0, 300.0], dtype=np.float64),
            unit="W",
        ),
        power_series_mask=np.array([True, False, True], dtype=bool),
        current_series=ArrayCurrentMagnitudeDto(
            value=np.array([10.0, 20.0, 30.0], dtype=np.float64),
            unit="A",
        ),
        current_series_mask=np.array([True, True, True], dtype=bool),
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


def _itm_stub() -> SimpleNamespace:
    return SimpleNamespace(
        model=SimpleNamespace(array_layout=_layout()),
        simulation_result=SimpleNamespace(
            power=object(),
            characteristic=object(),
        ),
    )


class TestExtractCurveFitComparisonData:
    """共有比較データ抽出の振る舞い。"""

    def test_returns_none_when_simulation_missing(self) -> None:
        """シミュレーション不足時は None。"""
        itm = SimpleNamespace(
            model=SimpleNamespace(array_layout=_layout()),
            simulation_result=None,
        )
        assert (
            extract_curve_fit_comparison_data(
                _catalog_with_current_unobserved(),
                cast(ItmDto, itm),
            )
            is None
        )

    def test_channel_independent_valid_mask(
        self,
        monkeypatch,
    ) -> None:
        """|I| 未観測でも他チャネルの valid は True のまま。"""
        monkeypatch.setattr(
            ccd,
            "_simulated_pred_arrays",
            lambda _itm: _fake_pred_arrays(),
        )
        data = extract_curve_fit_comparison_data(
            _catalog_with_current_unobserved(),
            cast(ItmDto, _itm_stub()),
        )
        assert data is not None
        assert isinstance(data, CurveFitComparisonData)
        assert data.slip_fraction.size == _N_GRID
        assert not np.any(data.valid_i)
        assert np.all(data.valid_p)
        assert np.all(data.valid_pf)
        assert np.all(data.valid_eta)
        assert np.all(np.isfinite(data.target_p))
        assert np.all(np.isnan(data.target_i))

    def test_masked_placeholder_excluded_from_target_via_public_api(
        self,
        monkeypatch,
    ) -> None:
        """mask False のプレースホルダが公開 API 経由の target 補間に混入しない。

        カタログ slip [0, 0.05, 0.10]、power [100, 999(未観測), 300] を、
        評価格子 slip [0.02, 0.04] で補間する。プレースホルダ 999 を除外すると
        (0→100, 0.10→300) の線形補間で 140 / 180 になる。999 が混入していれば
        まったく異なる値になるため、混入の有無を値で判定できる。
        """
        monkeypatch.setattr(
            ccd,
            "_simulated_pred_arrays",
            lambda _itm: _fake_pred_arrays(),
        )
        data = extract_curve_fit_comparison_data(
            _catalog_with_power_placeholder(),
            cast(ItmDto, _itm_stub()),
        )
        assert data is not None
        np.testing.assert_allclose(data.target_p, [140.0, 180.0])
