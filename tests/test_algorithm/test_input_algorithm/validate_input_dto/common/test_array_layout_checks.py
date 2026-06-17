"""``check_line_voltage_real_constraints`` の経路非依存テスト。

線間電圧の実数制約（実部 ``>= 0`` かつ虚部 ``== 0``）を直接検証する。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.array_layout_checks import (  # noqa: E501, PLC2701
    check_line_voltage_real_constraints,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def _replace_voltage(dto: InputDto, volt: ArrayComplexVoltageDto) -> InputDto:
    new_arrays = dict(dto.array_layout.arrays)
    new_arrays[ArrayKey.INPUT_LINE_VOLTAGE] = volt
    new_layout = dataclasses.replace(
        dto.array_layout,
        arrays=new_arrays,
    )
    return dataclasses.replace(dto, array_layout=new_layout)


class TestCheckLineVoltageRealConstraints:
    """``check_line_voltage_real_constraints`` の単体テスト。"""

    def test_accepts_real_positive_voltage(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """実部正・虚部ゼロの正常系を通す。"""
        dto = build_cartesian_dto()
        check_line_voltage_real_constraints(dto)

    def test_rejects_negative_real_voltage(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """実部が負の要素を含む場合に raise する。"""
        dto = build_cartesian_dto()
        unit = dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_unit()
        bad = ArrayComplexVoltageDto(
            value=np.array([-460.0 + 0.0j], dtype=np.complex128),
            unit=unit,
        )
        bad_dto = _replace_voltage(dto, bad)
        with pytest.raises(ValueError, match="input_line_voltage.*実部"):
            check_line_voltage_real_constraints(bad_dto)

    def test_rejects_nonzero_imaginary_voltage(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """虚部が非ゼロの要素を含む場合に raise する。"""
        dto = build_cartesian_dto()
        unit = dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_unit()
        bad = ArrayComplexVoltageDto(
            value=np.array([460.0 + 1.0j], dtype=np.complex128),
            unit=unit,
        )
        bad_dto = _replace_voltage(dto, bad)
        with pytest.raises(ValueError, match="input_line_voltage.*虚部"):
            check_line_voltage_real_constraints(bad_dto)

    def test_rejects_when_only_partial_element_violates(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """混在配列で 1 要素のみ負実部の場合も raise する。"""
        dto = build_cartesian_dto()
        unit = dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_unit()
        bad = ArrayComplexVoltageDto(
            value=np.array(
                [460.0 + 0.0j, -460.0 + 0.0j],
                dtype=np.complex128,
            ),
            unit=unit,
        )
        bad_dto = _replace_voltage(dto, bad)
        with pytest.raises(ValueError, match="input_line_voltage.*実部"):
            check_line_voltage_real_constraints(bad_dto)
