"""``FittableParamDescriptor`` データ保持スモークテスト。

このクラスは ``__post_init__`` を持たない素のデータホルダ。バリデーションは
利用側エンジンに委ねるため、ここではフィールドが正しく保持されること、
``frozen=True`` で immutable であることだけを確認する。
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)


class TestFittableParamDescriptor:
    def test_fields_held(self) -> None:
        d = FittableParamDescriptor(
            path=("im", "primary_resistance"),
            current_value=1.0,
            lb=0.1,
            ub=10.0,
            unit="Ω",
        )
        assert d.path == ("im", "primary_resistance")
        assert d.current_value == 1.0
        assert d.lb == 0.1
        assert d.ub == 10.0
        assert d.unit == "Ω"

    def test_unit_can_be_none(self) -> None:
        d = FittableParamDescriptor(
            path=("global", "alpha"),
            current_value=0.5,
            lb=0.0,
            ub=1.0,
            unit=None,
        )
        assert d.unit is None

    def test_is_frozen(self) -> None:
        d = FittableParamDescriptor(
            path=("im", "primary_resistance"),
            current_value=1.0,
            lb=0.1,
            ub=10.0,
            unit="Ω",
        )
        with pytest.raises(FrozenInstanceError):
            d.current_value = 2.0  # type: ignore[misc]
