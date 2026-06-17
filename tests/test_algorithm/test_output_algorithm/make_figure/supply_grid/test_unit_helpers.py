"""supply_grid ``_unit_helpers`` の単体テスト。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid._unit_helpers import (  # noqa: E501, PLC2701
    _as_real_array,
    _ratio_to_base_unit,
    _scalar_base_value,
    _to_base_value_array,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayEfficiencyDto,
    FloatActivePowerDto,
)


class TestUnitHelpers:
    """単位付き DTO からの値取り出し。"""

    def test_as_real_array_strips_imaginary_part(self) -> None:
        values = np.array([1.0 + 2.0j, 3.0 + 4.0j], dtype=np.complex128)
        out = _as_real_array(values)
        np.testing.assert_allclose(out, [1.0, 3.0])

    def test_to_base_value_array_converts_power_to_watts(self) -> None:
        dto = FloatActivePowerDto(value=1.0, unit="kW")
        out = _to_base_value_array(dto)
        assert float(np.asarray(out).reshape(-1)[0]) == 1000.0

    def test_scalar_base_value_returns_first_element(self) -> None:
        dto = FloatActivePowerDto(value=2.5, unit="W")
        assert _scalar_base_value(dto) == 2.5

    def test_ratio_to_base_unit_converts_percent(self) -> None:
        dto = ArrayEfficiencyDto(value=np.array([80.0, 90.0]), unit="%")
        out = _ratio_to_base_unit(dto)
        np.testing.assert_allclose(out, [0.8, 0.9])

    def test_ratio_to_base_unit_keeps_dimensionless(self) -> None:
        dto = ArrayEfficiencyDto(value=np.array([0.8, 0.9]), unit="-")
        out = _ratio_to_base_unit(dto)
        np.testing.assert_allclose(out, [0.8, 0.9])
