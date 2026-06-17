"""FloatParamDto / FloatParamDtos / validate_param_names_match のテスト。"""

from __future__ import annotations

import math

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    validate_param_names_match,
)


class TestFloatParamDtoValueValidation:
    """``FloatParamDto.__post_init__`` の値検証テスト。"""

    def test_finite_value_is_accepted(self) -> None:
        param = FloatParamDto(name="alpha", value=1.5)
        assert param.get_value() == pytest.approx(1.5)

    def test_nan_value_raises(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            FloatParamDto(name="alpha", value=math.nan)

    def test_positive_inf_raises(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            FloatParamDto(name="alpha", value=math.inf)

    def test_negative_inf_raises(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            FloatParamDto(name="alpha", value=-math.inf)

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            FloatParamDto(name="", value=1.0)


class TestFloatParamDtosDuplicateNames:
    """``FloatParamDtos.__init__`` の重複 name 検出テスト。"""

    def test_unique_names_accepted(self) -> None:
        collection = FloatParamDtos(
            objects=[
                FloatParamDto(name="alpha", value=1.0),
                FloatParamDto(name="beta", value=2.0),
            ]
        )
        assert sorted(collection.get_names()) == ["alpha", "beta"]

    def test_duplicate_names_raise(self) -> None:
        with pytest.raises(ValueError, match="重複"):
            FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha", value=1.0),
                    FloatParamDto(name="alpha", value=2.0),
                ]
            )


class TestValidateParamNamesMatch:
    """``validate_param_names_match`` のケース別テスト。"""

    def test_empty_required_and_none_params_ok(self) -> None:
        validate_param_names_match(
            None,
            required_names=[],
            context="ctx",
        )

    def test_empty_required_and_empty_params_ok(self) -> None:
        empty = FloatParamDtos(objects=[])
        validate_param_names_match(
            empty,
            required_names=[],
            context="ctx",
        )

    def test_empty_required_but_params_present_raises(self) -> None:
        params = FloatParamDtos(
            objects=[FloatParamDto(name="x", value=1.0)],
        )
        with pytest.raises(ValueError, match="パラメータを取らないモデル"):
            validate_param_names_match(
                params,
                required_names=[],
                context="ctx",
            )

    def test_required_but_params_none_raises(self) -> None:
        with pytest.raises(ValueError, match="必須ですが params が None"):
            validate_param_names_match(
                None,
                required_names=["alpha"],
                context="ctx",
            )

    def test_missing_required_param_raises(self) -> None:
        params = FloatParamDtos(
            objects=[FloatParamDto(name="alpha", value=1.0)]
        )
        with pytest.raises(ValueError, match="不足"):
            validate_param_names_match(
                params,
                required_names=["alpha", "beta"],
                context="ctx",
            )

    def test_unexpected_param_raises(self) -> None:
        params = FloatParamDtos(
            objects=[
                FloatParamDto(name="alpha", value=1.0),
                FloatParamDto(name="extra", value=2.0),
            ]
        )
        with pytest.raises(ValueError, match="余分"):
            validate_param_names_match(
                params,
                required_names=["alpha"],
                context="ctx",
            )

    def test_exact_match_ok(self) -> None:
        params = FloatParamDtos(
            objects=[
                FloatParamDto(name="alpha", value=1.0),
                FloatParamDto(name="beta", value=2.0),
            ]
        )
        validate_param_names_match(
            params,
            required_names=["alpha", "beta"],
            context="ctx",
        )
