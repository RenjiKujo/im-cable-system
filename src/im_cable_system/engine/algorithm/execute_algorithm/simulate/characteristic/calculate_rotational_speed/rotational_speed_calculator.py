"""回転速度計算器。

配列レイアウトのスリップ・定格回転速度から、ドメイン層の回転速度計算を用いて
回転速度 DTO を算出する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_rotational_speed.i_rotational_speed_calculator import (  # noqa: E501
    IRotationalSpeedCalculator,
)
from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
)
from im_cable_system.engine.domain.physics import (
    calculate_rotational_speed,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayFrequencyDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
)


class RotationalSpeedCalculator(IRotationalSpeedCalculator):
    """回転速度計算器実装（im_cable_system）。

    周波数・極数・すべりから回転速度を計算します。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IRotationalSpeedCalculator:
        return cls(config=config, logger=logger)

    def calculate(
        self, *, array_layout: ArrayLayoutDto, poles: int
    ) -> ArrayRotationalSpeedDto:
        """回転速度を計算する。"""
        slip_key = ArrayKey.SLIP
        frequency_key = ArrayKey.FREQUENCY
        if slip_key not in array_layout.arrays:
            raise ValueError(
                f"array_layout.arraysに'{slip_key}'が存在しません。"
            )
        if frequency_key not in array_layout.arrays:
            raise ValueError(
                f"array_layout.arraysに'{frequency_key}'が存在しません。"
            )

        slip_dto_raw = array_layout.arrays[slip_key]
        frequency_dto_raw = array_layout.arrays[frequency_key]

        if not isinstance(slip_dto_raw, ArraySlipDto):
            raise ValueError(
                f"array_layout.arrays['{slip_key}']はArraySlipDtoである必要があります。"
                f"実際の型: {type(slip_dto_raw)}"
            )
        if not isinstance(frequency_dto_raw, ArrayFrequencyDto):
            raise ValueError(
                f"array_layout.arrays['{frequency_key}']はArrayFrequencyDtoである必要があります。"
                f"実際の型: {type(frequency_dto_raw)}"
            )

        extended_arrays = create_extended_arrays(array_layout=array_layout)
        slip = ArraySlipDto(
            value=extended_arrays[slip_key],
            unit=slip_dto_raw.get_unit(),
        ).to_base_unit()
        frequency = ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=frequency_dto_raw.get_unit(),
        ).to_base_unit()

        return calculate_rotational_speed(
            slip_array=slip,
            frequency_array=frequency,
            poles=poles,
        )
