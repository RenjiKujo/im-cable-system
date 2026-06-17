"""``compute_residual_vector`` のチャネル別 valid に関する単体テスト。

カバー対象（不具合修正の回帰防止）:
    - あるチャネル（|I|）だけ全点未観測でも、他チャネル（P/PF/η）の残差は
      評価されること（チャネル別 valid が効く）。
    - 旧実装（4 チャネル共通の単一 valid）では未観測チャネルに引きずられて
      全体が ``[0.0]`` に潰れていたが、本修正後は他チャネルの残差が残る。

シミュレーション量抽出（``_simulated_pred_arrays``）は本テストの対象外なので
stub に差し替え、カタログ補間（マスク適用）と残差連結のロジックだけを検証する。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np

import im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.curve_comparison_data as ccd  # noqa: E501
import im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.curve_residual_vector as crv  # noqa: E501
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization import (  # noqa: E501
    ByCurveScaleResidualNormalizationStrategy,
)
from im_cable_system.engine.shared.config import ResidualNormalizationStatistic
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


def _fake_pred_arrays() -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray
]:
    """格子点数に合わせた stub の予測 (|I|, P, PF, η)（target と異なる値）。"""
    return (
        np.array([5.0, 5.0], dtype=np.float64),
        np.array([0.0, 0.0], dtype=np.float64),
        np.array([0.0, 0.0], dtype=np.float64),
        np.array([0.0, 0.0], dtype=np.float64),
    )


def _itm_stub() -> SimpleNamespace:
    """compute_residual_vector が参照する最小限の itm stub。"""
    return SimpleNamespace(
        model=SimpleNamespace(array_layout=_layout()),
        simulation_result=SimpleNamespace(
            power=object(),
            characteristic=object(),
        ),
    )


class TestComputeResidualVectorChannelValid:
    """チャネル別 valid の振る舞い。"""

    def test_unobserved_channel_does_not_zero_out_others(
        self,
        monkeypatch,
    ) -> None:
        """|I| 未観測でも P/PF/η の残差は評価される。"""
        monkeypatch.setattr(
            ccd,
            "_simulated_pred_arrays",
            lambda _itm: _fake_pred_arrays(),
        )
        out = crv.compute_residual_vector(
            catalogs=_catalog_with_current_unobserved(),
            itm=cast(ItmDto, _itm_stub()),
            weights=(1.0, 1.0, 1.0, 1.0),
            normalization_strategy=ByCurveScaleResidualNormalizationStrategy(
                statistic=ResidualNormalizationStatistic.STD,
                eps=1.0e-12,
            ),
        )
        # 4 チャネル × n_grid の残差ベクトルが返る（[0.0] へ潰れない）。
        assert out.size == 4 * _N_GRID
        # |I| チャネルは未観測なので残差ゼロ。
        assert np.allclose(out[:_N_GRID], 0.0)
        # P チャネルは観測ありで pred(=0) と異なるため非ゼロが残る。
        p_block = out[_N_GRID : 2 * _N_GRID]
        assert np.any(p_block != 0.0)
