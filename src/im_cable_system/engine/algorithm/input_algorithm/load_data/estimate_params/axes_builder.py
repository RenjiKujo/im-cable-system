"""性能曲線から AxesLoadedData（評価点軸）を構築する。

EstimateParams では、3 軸（slip / frequency / input_line_voltage）の
うち frequency / voltage は単一の供給条件、slip は性能曲線の
回転速度配列から ``s = (N_sync - rpm) / N_sync`` で導出する。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.axes_loaded_data import (  # noqa: E501
    AxesLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)


def _derive_slip(
    rpm: np.ndarray, poles: int, frequency_hz: float
) -> np.ndarray:
    n_sync = 120.0 * float(frequency_hz) / float(poles)
    return (n_sync - rpm) / n_sync


def build_axes_loaded_data_from_performance_curve(
    perf_curve: ImPerformanceCurveLoadedData,
) -> AxesLoadedData:
    """性能曲線中間表現から評価点軸の中間表現を組み立てる。

    Args:
        perf_curve: 性能曲線の中間表現。

    Returns:
        AxesLoadedData: 評価点軸の中間表現。``frequency`` /
            ``input_line_voltage`` は供給条件 1 点配列、``slip`` は
            ``rotational_speed`` 由来の 1 次元配列。
    """
    poles_int = int(round(perf_curve.poles))
    slip = _derive_slip(
        rpm=perf_curve.rotational_speed,
        poles=poles_int,
        frequency_hz=perf_curve.supply_frequency,
    )
    frequency = np.array([float(perf_curve.supply_frequency)], dtype=np.float64)
    voltage = np.array([float(perf_curve.supply_voltage)], dtype=np.float64)
    return AxesLoadedData(
        slip=slip,
        frequency=frequency,
        input_line_voltage=voltage,
        slip_unit="-",
        frequency_unit=perf_curve.supply_frequency_unit,
        voltage_unit=perf_curve.supply_voltage_unit,
    )
