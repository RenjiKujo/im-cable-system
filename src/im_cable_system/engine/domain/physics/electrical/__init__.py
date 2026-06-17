"""電気物理計算（公開窓口）。

このモジュールは、回路理論に基づく汎用的な電気計算ロジック
（キルヒホッフの法則、オームの法則、インピーダンス合成・変換、電力計算、
電圧・電流変換など）を提供する。

クランプ方針:
    イミタンス・電流・電圧まではクランプするが、それ以降の計算で算出される
    電力などの特性値はクランプしない。

層外からの import:
    >>> from im_cable_system.engine.domain.physics.electrical import (
    ...     calculate_current_from_voltage_and_impedance,
    ...     combine_impedance_series,
    ... )
"""

from im_cable_system.engine.domain.physics.electrical.circuit_laws.kirchhoff import (  # noqa: E501
    solve_kirchhoff_current,
    solve_kirchhoff_voltage,
)
from im_cable_system.engine.domain.physics.electrical.circuit_laws.ohms_law import (  # noqa: E501
    calculate_current_from_voltage_and_admittance,
    calculate_current_from_voltage_and_impedance,
    calculate_voltage_from_current_and_admittance,
    calculate_voltage_from_current_and_impedance,
)
from im_cable_system.engine.domain.physics.electrical.immittance.admittance_combiner import (  # noqa: E501
    combine_admittance_parallel,
    combine_admittance_series,
    combine_admittances_parallel,
    combine_admittances_series,
)
from im_cable_system.engine.domain.physics.electrical.immittance.admittance_converter import (  # noqa: E501
    admittance_from_capacitance_and_frequency,
    admittance_from_conductance_and_frequency,
    admittance_from_impedance,
    admittance_from_inductance_and_frequency,
)
from im_cable_system.engine.domain.physics.electrical.immittance.impedance_combiner import (  # noqa: E501
    combine_impedance_parallel,
    combine_impedance_series,
    combine_impedances_parallel,
    combine_impedances_series,
)
from im_cable_system.engine.domain.physics.electrical.immittance.impedance_converter import (  # noqa: E501
    impedance_from_admittance,
    impedance_from_capacitance_and_frequency,
    impedance_from_inductance_and_frequency,
    impedance_from_resistance_and_frequency,
)
from im_cable_system.engine.domain.physics.electrical.immittance.line_density_impedance_converter import (  # noqa: E501
    impedance_from_conductor_line_density,
    impedance_from_ground_line_density,
)
from im_cable_system.engine.domain.physics.electrical.power.power_calculator import (  # noqa: E501
    add_power,
    power_from_current_and_impedance,
    power_from_voltage_and_admittance,
    power_from_voltage_and_current,
)
from im_cable_system.engine.domain.physics.electrical.power.three_phase_power_builder import (  # noqa: E501
    sum_power_dict_values,
    three_phase_power_dict_from_voltage_and_current_phase_dict,
    three_phase_power_from_voltage_and_current_phase,
)
from im_cable_system.engine.domain.physics.electrical.power.three_phase_power_converter import (  # noqa: E501
    to_three_phase_power_from_line,
    to_three_phase_power_from_phase,
)
from im_cable_system.engine.domain.physics.electrical.voltage_current.connection_type_converter import (  # noqa: E501
    convert_current_delta_to_star,
    convert_current_delta_to_star_balanced,
    convert_current_star_to_delta,
    convert_current_star_to_delta_balanced,
    convert_voltage_delta_to_star,
    convert_voltage_delta_to_star_balanced,
    convert_voltage_star_to_delta,
    convert_voltage_star_to_delta_balanced,
)
from im_cable_system.engine.domain.physics.electrical.voltage_current.delta_line_phase_converter import (  # noqa: E501
    line_to_phase_current_delta,
    line_to_phase_current_delta_balanced,
    line_to_phase_voltage_delta,
    phase_to_line_current_delta,
    phase_to_line_current_delta_balanced,
    phase_to_line_voltage_delta,
)
from im_cable_system.engine.domain.physics.electrical.voltage_current.star_line_phase_converter import (  # noqa: E501
    line_to_phase_current_star,
    line_to_phase_voltage_star,
    line_to_phase_voltage_star_balanced,
    phase_to_line_current_star,
    phase_to_line_voltage_star,
    phase_to_line_voltage_star_balanced,
)

__all__ = [
    "add_power",
    "admittance_from_capacitance_and_frequency",
    "admittance_from_conductance_and_frequency",
    "admittance_from_impedance",
    "admittance_from_inductance_and_frequency",
    "calculate_current_from_voltage_and_admittance",
    "calculate_current_from_voltage_and_impedance",
    "calculate_voltage_from_current_and_admittance",
    "calculate_voltage_from_current_and_impedance",
    "combine_admittance_parallel",
    "combine_admittance_series",
    "combine_admittances_parallel",
    "combine_admittances_series",
    "combine_impedance_parallel",
    "combine_impedance_series",
    "combine_impedances_parallel",
    "combine_impedances_series",
    "convert_current_delta_to_star",
    "convert_current_delta_to_star_balanced",
    "convert_current_star_to_delta",
    "convert_current_star_to_delta_balanced",
    "convert_voltage_delta_to_star",
    "convert_voltage_delta_to_star_balanced",
    "convert_voltage_star_to_delta",
    "convert_voltage_star_to_delta_balanced",
    "impedance_from_admittance",
    "impedance_from_capacitance_and_frequency",
    "impedance_from_conductor_line_density",
    "impedance_from_ground_line_density",
    "impedance_from_inductance_and_frequency",
    "impedance_from_resistance_and_frequency",
    "line_to_phase_current_delta",
    "line_to_phase_current_delta_balanced",
    "line_to_phase_current_star",
    "line_to_phase_voltage_delta",
    "line_to_phase_voltage_star",
    "line_to_phase_voltage_star_balanced",
    "phase_to_line_current_delta",
    "phase_to_line_current_delta_balanced",
    "phase_to_line_current_star",
    "phase_to_line_voltage_delta",
    "phase_to_line_voltage_star",
    "phase_to_line_voltage_star_balanced",
    "power_from_current_and_impedance",
    "power_from_voltage_and_admittance",
    "power_from_voltage_and_current",
    "solve_kirchhoff_current",
    "solve_kirchhoff_voltage",
    "sum_power_dict_values",
    "three_phase_power_dict_from_voltage_and_current_phase_dict",
    "three_phase_power_from_voltage_and_current_phase",
    "to_three_phase_power_from_line",
    "to_three_phase_power_from_phase",
]
