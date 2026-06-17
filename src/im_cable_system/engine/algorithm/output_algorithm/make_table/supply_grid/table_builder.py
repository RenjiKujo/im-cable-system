"""make_table（supply_grid 系）の実装。

``OutputDto.array_layout`` の参照軸直積（slip × 供給条件 (V, f)）を 1 行 1 点の
long 形式で展開し、``OutputDto.result`` から派生量（Pout / |I_line| / 力率 /
効率）を算出した表（``DataFrame``）を組み立てる。保存はしない（export の責務）。

列順は先頭 3 列を ``voltage_v, frequency_hz, slip`` とし、行は slip が最も速く、
次に周波数、最後に電圧が動く順（電圧外側・slip 内側）に並べる。カタログ
（``OutputDto.im_pc_catalogs``）があれば、対応行へ ``catalog_`` 接頭の参照列を
右側に追加する。
"""

from __future__ import annotations

import numpy as np
from pandas import DataFrame

from im_cable_system.engine.algorithm.output_algorithm.make_table.i_table_builder import (  # noqa: E501
    ITableBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.supply_grid.catalog_columns import (  # noqa: E501
    build_catalog_columns,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.dto.output import OutputDto

_REQUIRED_AXES = (
    ArrayKey.SLIP,
    ArrayKey.FREQUENCY,
    ArrayKey.INPUT_LINE_VOLTAGE,
)


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


def _axis_grid(
    output_dto: OutputDto,
    axis: ArrayKey,
    *,
    reference_axes: list[ArrayKey],
    reference_shape: tuple[int, ...],
) -> np.ndarray:
    """参照軸直積（C 順）各点における 1 次元軸スカラーを展開して返す。"""
    raw = _real_flat(
        output_dto.array_layout.arrays[axis].to_base_unit().get_value()
    )
    position = reference_axes.index(axis)
    broadcast_shape = [1] * len(reference_shape)
    broadcast_shape[position] = reference_shape[position]
    grid = raw.reshape(broadcast_shape) * np.ones(reference_shape)
    return np.asarray(grid, dtype=np.float64).reshape(-1)


def _simulated_columns(
    output_dto: OutputDto,
    *,
    voltage_v: np.ndarray,
    frequency_hz: np.ndarray,
    slip: np.ndarray,
) -> dict[str, np.ndarray]:
    """OutputDto.result から表本体の列（供給条件＋派生量）を作る。

    先頭 3 列は ``voltage_v, frequency_hz, slip`` の順とする。
    """
    result = output_dto.result
    return {
        "voltage_v": voltage_v,
        "frequency_hz": frequency_hz,
        "slip": slip,
        "output_power_w": _real_flat(
            result.output_power.to_base_unit().get_value()
        ),
        "input_current_magnitude_a": np.abs(
            np.asarray(
                result.input_line_current.to_base_unit().get_value(),
                dtype=np.complex128,
            ).reshape(-1)
        ),
        "power_factor": _power_factor(
            result.cable_input_phase_power.to_base_unit().get_value()
        ),
        "efficiency": _real_flat(
            result.system_efficiency.to_base_unit().get_value()
        ),
        "rotational_speed_rpm": _real_flat(
            result.rotational_speed.convert_to_unit("rpm").get_value()
        ),
        "torque_nm": _real_flat(result.torque.to_base_unit().get_value()),
    }


class SupplyGridTableBuilder(ITableBuilder):
    """OutputDto から slip 軸グリッド表示の表を組み立てるビルダー。"""

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
        """OutputDto から slip 軸グリッド表（long 形式）を組み立てて返す。

        先頭 3 列は ``voltage_v, frequency_hz, slip`` の順で、行は slip が最も
        速く・次に周波数・最後に電圧が動く順に並べる。カタログがあれば対応行へ
        ``catalog_`` 接頭の参照列を右側に追加する（一致しない行は NaN）。

        必須軸（slip / frequency / input_line_voltage）が揃わない場合は、
        呼び出し側の出力フローを止めないため空の ``DataFrame`` を返す。
        """
        layout = output_dto.array_layout
        if not all(axis in layout.reference_axes for axis in _REQUIRED_AXES):
            return DataFrame()

        reference_axes = list(layout.reference_axes)
        reference_shape = layout.get_reference_shape()

        frequency_hz = _axis_grid(
            output_dto,
            ArrayKey.FREQUENCY,
            reference_axes=reference_axes,
            reference_shape=reference_shape,
        )
        voltage_v = _axis_grid(
            output_dto,
            ArrayKey.INPUT_LINE_VOLTAGE,
            reference_axes=reference_axes,
            reference_shape=reference_shape,
        )
        slip = _axis_grid(
            output_dto,
            ArrayKey.SLIP,
            reference_axes=reference_axes,
            reference_shape=reference_shape,
        )

        columns = _simulated_columns(
            output_dto,
            voltage_v=voltage_v,
            frequency_hz=frequency_hz,
            slip=slip,
        )
        columns.update(
            build_catalog_columns(
                output_dto,
                voltage_v=voltage_v,
                frequency_hz=frequency_hz,
                slip=slip,
            )
        )
        # 電圧を外側・周波数を中間・slip を内側にして slip を最も速く動かす。
        order = np.lexsort((slip, frequency_hz, voltage_v))
        return DataFrame(
            {
                name: np.asarray(values)[order]
                for name, values in columns.items()
            }
        )
