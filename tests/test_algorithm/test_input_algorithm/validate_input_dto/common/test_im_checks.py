"""``check_im_values`` の経路非依存テスト。

IM 名板値が ``> 0`` であることを直接検証する。``nameplate_frequency`` の
``> 0`` 契約は :class:`FloatFrequencyDto` 側で既に強制されているため、
common 関数だけで失敗を再現するテストは ``voltage`` / ``current`` /
``power`` の 3 種に絞っている（``frequency`` の重複契約は実装側 docstring
に明示済み）。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any, cast

import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.im_checks import (  # noqa: E501, PLC2701
    check_im_values,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def _replace_im_series(
    dto: InputDto,
    **series_overrides: object,
) -> InputDto:
    new_series = dataclasses.replace(
        dto.im.im_series,
        **cast(Any, series_overrides),
    )
    new_im = dataclasses.replace(dto.im, im_series=new_series)
    return dataclasses.replace(dto, im=new_im)


class TestCheckImValues:
    """``check_im_values`` の単体テスト。"""

    def test_accepts_positive_nameplates(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """名板 4 項目が正のとき pass する。"""
        dto = build_cartesian_dto()
        check_im_values(dto)

    def test_rejects_zero_nameplate_voltage(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """``nameplate_voltage == 0`` で raise する。"""
        dto = build_cartesian_dto()
        original_unit = dto.im.im_series.nameplate_voltage.get_unit()
        invalid = _replace_im_series(
            dto,
            nameplate_voltage=FloatVoltageDto(value=0.0, unit=original_unit),
        )
        with pytest.raises(ValueError, match="nameplate_voltage"):
            check_im_values(invalid)

    def test_rejects_zero_nameplate_current(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """``nameplate_current == 0`` で raise する。"""
        dto = build_cartesian_dto()
        original_unit = dto.im.im_series.nameplate_current.get_unit()
        invalid = _replace_im_series(
            dto,
            nameplate_current=FloatCurrentDto(value=0.0, unit=original_unit),
        )
        with pytest.raises(ValueError, match="nameplate_current"):
            check_im_values(invalid)

    def test_rejects_zero_nameplate_power(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """``nameplate_power == 0`` で raise する。"""
        dto = build_cartesian_dto()
        original_unit = dto.im.im_series.nameplate_power.get_unit()
        invalid = _replace_im_series(
            dto,
            nameplate_power=FloatActivePowerDto(value=0.0, unit=original_unit),
        )
        with pytest.raises(ValueError, match="nameplate_power"):
            check_im_values(invalid)
