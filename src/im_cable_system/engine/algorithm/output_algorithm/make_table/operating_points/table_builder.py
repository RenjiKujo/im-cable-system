"""make_table（operating_points 系）の実装。

operating_points Figure（運転点横軸の性能図）を素直に表へ写したもの。運転点
（リスト番号）を 1 行 1 点で並べ、各運転点の特性量（回転数 / 電流 / 電圧 /
周波数 / 出力 / トルク / 効率 / 力率）を列に持つ ``DataFrame`` を組み立てる。
``OutputDto.result`` / ``array_layout`` から派生計算する（保存は export の責務）。

列順は ``operating_point, slip`` を先頭に、以降は Figure の軸（回転数 / 電流 /
電圧 / 周波数 / 出力 / トルク / 効率 / 力率）の順に並べる。供給条件の軸
（slip / 周波数 / 電圧）が ``array_layout`` に無い場合、その列は省く。
"""

from __future__ import annotations

import numpy as np
from pandas import DataFrame

from im_cable_system.engine.algorithm.output_algorithm.make_table.i_table_builder import (  # noqa: E501
    ITableBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto


def _real_flat(value: object) -> np.ndarray:
    """単位 DTO 値を実数 1 次元 ``float64`` 配列にする。"""
    return np.asarray(np.real(np.asarray(value)), dtype=np.float64).reshape(-1)


def _power_factor(complex_power: object) -> np.ndarray:
    """複素電力から力率 ``Re(S) / |S|`` を 1 次元配列で返す。"""
    power = np.asarray(complex_power, dtype=np.complex128).reshape(-1)
    magnitude = np.abs(power)
    finite = np.isfinite(power.real) & np.isfinite(power.imag)
    valid = finite & (magnitude > 0.0)
    out = np.zeros(power.shape, dtype=np.float64)
    out[valid] = power.real[valid] / magnitude[valid]
    return out


def _axis_column_if_present(
    output_dto: OutputDto,
    axis: ArrayKey,
) -> np.ndarray | None:
    """array_layout に軸があれば基準単位の 1 次元配列を、なければ ``None`` を返す。"""
    arrays = output_dto.array_layout.arrays
    if axis not in arrays:
        return None
    return _real_flat(arrays[axis].to_base_unit().get_value())


class OperatingPointsTableBuilder(ITableBuilder):
    """OutputDto から運転点ごとの index 性能表を組み立てるビルダー。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ITableBuilder:
        """ビルダーのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def build(self, output_dto: OutputDto) -> DataFrame:
        """OutputDto から運転点 index 性能表（1 運転点 1 行）を組み立てて返す。

        operating_points Figure をそのまま表へ写したもの。先頭列は
        ``operating_point``（リスト番号）で、以降は Figure の軸量を並べる。
        供給条件軸（slip / 周波数 / 電圧）が ``array_layout`` に無い場合、その
        列は省く。

        運転点数が 0 の場合は、呼び出し側の出力フローを止めないため空の
        ``DataFrame`` を返す。
        """
        num_points = output_dto.array_layout.get_reference_total_length()
        if num_points <= 0:
            return DataFrame()

        result = output_dto.result
        columns: dict[str, np.ndarray] = {
            "operating_point": np.arange(num_points, dtype=np.int64),
        }

        slip = _axis_column_if_present(output_dto, ArrayKey.SLIP)
        if slip is not None:
            columns["slip"] = slip

        columns["rotational_speed_rpm"] = _real_flat(
            result.rotational_speed.convert_to_unit("rpm").get_value()
        )
        columns["input_current_magnitude_a"] = np.abs(
            np.asarray(
                result.input_line_current.to_base_unit().get_value(),
                dtype=np.complex128,
            ).reshape(-1)
        )

        voltage = _axis_column_if_present(
            output_dto, ArrayKey.INPUT_LINE_VOLTAGE
        )
        if voltage is not None:
            columns["voltage_v"] = voltage
        frequency = _axis_column_if_present(output_dto, ArrayKey.FREQUENCY)
        if frequency is not None:
            columns["frequency_hz"] = frequency

        columns["output_power_w"] = _real_flat(
            result.output_power.to_base_unit().get_value()
        )
        columns["torque_nm"] = _real_flat(
            result.torque.to_base_unit().get_value()
        )
        columns["efficiency"] = _real_flat(
            result.system_efficiency.to_base_unit().get_value()
        )
        columns["power_factor"] = _power_factor(
            result.cable_input_phase_power.to_base_unit().get_value()
        )
        return DataFrame(columns)
