"""Tests for numerical stability event codes.

DTO / ログに載るキー文字列の一意性・命名規約（英語 snake_case）を担保する。
公開窓口経由でモジュールが import できることも併せて確認する。
"""

from __future__ import annotations

import re

from im_cable_system.engine.shared import numerical_stability
from im_cable_system.engine.shared.numerical_stability import event_codes


def _public_code_attribute_names() -> list[str]:
    """大文字定数（イベントコード）名の一覧を返す。"""
    return [
        name
        for name in dir(event_codes)
        if name.isupper() and not name.startswith("_")
    ]


class TestEventCodes:
    """イベントコード定数群の不変条件。"""

    def test_event_codes_module_accessible_from_public_init(self) -> None:
        # 公開窓口（__all__）に event_codes が載っている。
        assert numerical_stability.event_codes is event_codes

    def test_event_codes_are_non_empty_strings(self) -> None:
        names = _public_code_attribute_names()
        assert len(names) > 0
        for name in names:
            value = getattr(event_codes, name)
            assert isinstance(value, str), name
            assert value, f"empty value: {name}"

    def test_event_codes_use_lowercase_snake_case(self) -> None:
        pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        for name in _public_code_attribute_names():
            value = getattr(event_codes, name)
            assert pattern.match(value), f"non snake_case: {name}={value!r}"

    def test_event_code_values_are_unique(self) -> None:
        values = [
            getattr(event_codes, name)
            for name in _public_code_attribute_names()
        ]
        assert len(values) == len(set(values)), "duplicated event code values"

    def test_well_known_codes_exist(self) -> None:
        # 代表的なキーが存在することで、配下モジュールからの参照が壊れていないか確認。
        assert (
            event_codes.SLIP_NEAR_ZERO_SECONDARY_LOAD_IMM
            == "slip_near_zero_secondary_load_immittance"
        )
        assert (
            event_codes.IMPEDANCE_TOO_SMALL_FOR_ADMITTANCE
            == "impedance_too_small_for_admittance"
        )
