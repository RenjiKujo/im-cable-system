"""``curve_grid_sampling`` の観測マスク適用に関する単体テスト。

カバー対象（不具合修正の回帰防止）:
    - ``*_series_mask == False`` の未観測プレースホルダ点が補間元から除外され、
      プレースホルダ 0 が補間値（target）に混入しないこと。
    - マスク後の有効点が 2 点未満の系列は target が NaN になること。
    - チャネルごとに独立した mask が効き、ある系列だけ全点未観測でも他系列の
      target は有限値として得られること。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.curve_grid_sampling import (  # noqa: E501
    _catalog_targets_on_layout_grid,
    _interpolate_masked,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImPerformanceCurveCatalogDto,
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

_F_HZ = 60.0
_V_V = 400.0
_CAT_SLIP = np.array([0.0, 0.05, 0.10], dtype=np.float64)


def _layout_for_slips(slips: list[float]) -> ArrayLayoutDto:
    """SLIP/FREQUENCY/INPUT_LINE_VOLTAGE を参照軸とする最小レイアウト。

    FREQUENCY / INPUT_LINE_VOLTAGE は単一要素軸とし、参照直積の点数は
    ``len(slips)`` に一致させる。
    """
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.array(slips, dtype=np.float64),
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


def _make_catalog(
    *,
    power_values: np.ndarray,
    power_mask: np.ndarray,
    current_values: np.ndarray,
    current_mask: np.ndarray,
    pf_values: np.ndarray,
    pf_mask: np.ndarray,
    eta_values: np.ndarray,
    eta_mask: np.ndarray,
) -> ImPerformanceCurveCatalogDto:
    """4 チャネル + mask を持つカタログ行を 1 件作る。"""
    return ImPerformanceCurveCatalogDto(
        name="cat_60Hz_400V",
        supply_frequency=FloatFrequencyDto(value=_F_HZ, unit="Hz"),
        supply_voltage=FloatVoltageDto(value=_V_V, unit="V"),
        slip_series=ArraySlipDto(value=_CAT_SLIP.copy(), unit="-"),
        power_series=ArrayActivePowerDto(value=power_values, unit="W"),
        power_series_mask=power_mask,
        current_series=ArrayCurrentMagnitudeDto(value=current_values, unit="A"),
        current_series_mask=current_mask,
        power_factor_series=ArrayPowerFactorDto(value=pf_values, unit="-"),
        power_factor_series_mask=pf_mask,
        efficiency_series=ArrayEfficiencyDto(value=eta_values, unit="-"),
        efficiency_series_mask=eta_mask,
    )


def _targets_for_layout(
    layout: ArrayLayoutDto,
    catalog: ImPerformanceCurveCatalogDto,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return _catalog_targets_on_layout_grid(
        layout,
        n_grid=layout.get_reference_total_length(),
        ref_shape=layout.get_reference_shape(),
        slip_key=ArrayKey.SLIP,
        fk=ArrayKey.FREQUENCY,
        vk=ArrayKey.INPUT_LINE_VOLTAGE,
        cat_list=[catalog],
    )


class TestInterpolateMasked:
    """``_interpolate_masked`` 単体の挙動。"""

    def test_excludes_placeholder_points(self) -> None:
        """マスク False のプレースホルダ点は補間元から除外される。"""
        xp = np.array([0.0, 0.05, 0.10], dtype=np.float64)
        # 真値は線形に 100 -> 300 だが、中央点は未観測でプレースホルダ 0。
        fp = np.array([100.0, 0.0, 300.0], dtype=np.float64)
        mask = np.array([True, False, True], dtype=bool)
        value = _interpolate_masked(0.05, xp, fp, mask)
        # マスク適用後は (0.0->100, 0.10->300) の補間で 200。0 は混入しない。
        assert np.isclose(value, 200.0)

    def test_fewer_than_two_valid_points_returns_nan(self) -> None:
        """有効点が 2 点未満なら補間不能で NaN。"""
        xp = np.array([0.0, 0.05, 0.10], dtype=np.float64)
        fp = np.array([100.0, 200.0, 300.0], dtype=np.float64)
        mask = np.array([True, False, False], dtype=bool)
        assert np.isnan(_interpolate_masked(0.05, xp, fp, mask))


class TestCatalogTargetsMaskApplication:
    """``_catalog_targets_on_layout_grid`` のマスク適用。"""

    def test_masked_placeholder_not_mixed_into_targets(self) -> None:
        """未観測点 0 が target に混入しない（チャネルごとに正しく補間）。"""
        layout = _layout_for_slips([0.05])
        catalog = _make_catalog(
            power_values=np.array([100.0, 0.0, 300.0], dtype=np.float64),
            power_mask=np.array([True, False, True], dtype=bool),
            current_values=np.array([10.0, 20.0, 30.0], dtype=np.float64),
            current_mask=np.array([True, True, True], dtype=bool),
            pf_values=np.array([0.80, 0.85, 0.90], dtype=np.float64),
            pf_mask=np.array([True, True, True], dtype=bool),
            eta_values=np.array([0.90, 0.0, 0.92], dtype=np.float64),
            eta_mask=np.array([True, False, True], dtype=bool),
        )
        target_i, target_p, target_pf, target_eta = _targets_for_layout(
            layout, catalog
        )
        # power: 0 を除外して 100->300 補間で 200（0 混入なら 0 になる）。
        assert np.isclose(target_p[0], 200.0)
        # current: 全点観測なので素直に 20。
        assert np.isclose(target_i[0], 20.0)
        # power_factor: 全点観測で 0.85。
        assert np.isclose(target_pf[0], 0.85)
        # efficiency: 0 を除外して 0.90->0.92 補間で 0.91。
        assert np.isclose(target_eta[0], 0.91)

    def test_channel_independent_mask(self) -> None:
        """1 チャネル全点未観測でも他チャネルは有限の target を返す。"""
        layout = _layout_for_slips([0.02, 0.04])
        catalog = _make_catalog(
            power_values=np.array([100.0, 200.0, 300.0], dtype=np.float64),
            power_mask=np.array([True, True, True], dtype=bool),
            # current は全点未観測（プレースホルダ 0、mask 全 False）。
            current_values=np.array([0.0, 0.0, 0.0], dtype=np.float64),
            current_mask=np.array([False, False, False], dtype=bool),
            pf_values=np.array([0.80, 0.85, 0.90], dtype=np.float64),
            pf_mask=np.array([True, True, True], dtype=bool),
            eta_values=np.array([0.90, 0.91, 0.92], dtype=np.float64),
            eta_mask=np.array([True, True, True], dtype=bool),
        )
        target_i, target_p, target_pf, target_eta = _targets_for_layout(
            layout, catalog
        )
        # current は全点未観測 → 全格子点 NaN。
        assert np.all(np.isnan(target_i))
        # 他チャネルは未観測 current に巻き込まれず有限。
        assert np.all(np.isfinite(target_p))
        assert np.all(np.isfinite(target_pf))
        assert np.all(np.isfinite(target_eta))
