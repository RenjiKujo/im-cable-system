"""supply_grid 図群が共有する定格比系列の算出。

出力比横軸 Figure で使う出力比 [%] と電流比 [%] を、``OutputDto.im`` の
銘板値（定格電力・定格電流）と描画用系列から算出する。描画やレイアウトには
関与しない。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid._unit_helpers import (  # noqa: E501
    _scalar_base_value,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501
    _SupplyGridSeries,
)
from im_cable_system.engine.shared.dto.output import OutputDto


def _positive_nameplate_value(value: float, *, label: str) -> float:
    """定格値が正の有限値であることを検証して返す。

    Args:
        value: 検証する定格値。
        label: エラーメッセージ用の定格値名。

    Returns:
        正の有限値。

    Raises:
        ValueError: 定格値が正の有限値でない場合。
    """
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be a positive finite value: {value}")
    return value


def _nameplate_power_w(output_dto: OutputDto) -> float:
    """OutputDto の IM 銘板電力を W 基準で返す。"""
    im_series = output_dto.im.im_series
    power_w = _scalar_base_value(im_series.nameplate_power)
    return _positive_nameplate_value(power_w, label="nameplate_power")


def _nameplate_current_a(output_dto: OutputDto) -> float:
    """OutputDto の IM 銘板電流を A 基準で返す。"""
    im_series = output_dto.im.im_series
    current_a = _scalar_base_value(im_series.nameplate_current)
    return _positive_nameplate_value(current_a, label="nameplate_current")


def _output_ratio_percent(
    series: _SupplyGridSeries,
    output_dto: OutputDto,
) -> np.ndarray:
    """出力比 [%]（Pout / 銘板電力）を返す。"""
    return series.output_power_w / _nameplate_power_w(output_dto) * 100.0


def _current_ratio_percent(
    series: _SupplyGridSeries,
    output_dto: OutputDto,
) -> np.ndarray:
    """電流比 [%]（|I_line| / 銘板電流）を返す。"""
    return (
        series.input_current_magnitude_a
        / _nameplate_current_a(output_dto)
        * 100.0
    )


def _ratio_to_percent(values: np.ndarray) -> np.ndarray:
    """無次元比 [-] を percent 表示値へ変換する。"""
    return np.asarray(values, dtype=np.float64) * 100.0
