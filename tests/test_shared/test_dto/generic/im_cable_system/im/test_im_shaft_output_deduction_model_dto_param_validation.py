"""IM 軸出力控除（摩擦・風損／漂遊負荷損）モデル DTO の __post_init__ パラメータ検証テスト。

カバー対象:
    - ``ImFrictionWindageModelDto``
    - ``ImStrayLoadModelDto``

それぞれについて以下を検証する。
    - 必須名が完全に揃っていれば OK（``NONE`` は params=None）
    - 必須があるのに params=None → ValueError
    - 必須名が足りない → ValueError（"不足"）
    - 余分な名前が混ざる → ValueError（"余分"）
    - パラメータを取らないモデル（NONE）に params が指定されている → ValueError
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)


def _params(items: dict[str, float]) -> FloatParamDtos:
    return FloatParamDtos(
        objects=[FloatParamDto(name=n, value=v) for n, v in items.items()]
    )


class TestImFrictionWindageModelDtoValidation:
    """ImFrictionWindageModelDto の __post_init__ テスト。"""

    def test_none_with_none_params_ok(self) -> None:
        ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.NONE, params=None
        )

    def test_none_with_extra_params_raises(self) -> None:
        with pytest.raises(ValueError, match="パラメータを取らないモデル"):
            ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.NONE,
                params=_params({"k_friction_windage": 0.01}),
            )

    def test_constant_v1_with_exact_params_ok(self) -> None:
        ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.CONSTANT_V1,
            params=_params({"k_friction_windage": 0.01}),
        )

    def test_constant_v1_missing_param_raises(self) -> None:
        with pytest.raises(ValueError, match="必須ですが params が None"):
            ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.CONSTANT_V1,
                params=None,
            )

    def test_constant_v1_with_extra_param_raises(self) -> None:
        with pytest.raises(ValueError, match="余分"):
            ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.CONSTANT_V1,
                params=_params({"k_friction_windage": 0.01, "extra": 0.1}),
            )

    def test_get_required_parameter_names(self) -> None:
        assert (
            ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.NONE
            ).get_required_parameter_names()
            == []
        )
        assert ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.CONSTANT_V1,
            params=_params({"k_friction_windage": 0.01}),
        ).get_required_parameter_names() == ["k_friction_windage"]


class TestImStrayLoadModelDtoValidation:
    """ImStrayLoadModelDto の __post_init__ テスト。"""

    def test_none_with_none_params_ok(self) -> None:
        ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE, params=None)

    def test_none_with_extra_params_raises(self) -> None:
        with pytest.raises(ValueError, match="パラメータを取らないモデル"):
            ImStrayLoadModelDto(
                name=ImStrayLoadModelType.NONE,
                params=_params({"k_stray_load": 0.005}),
            )

    def test_current_dependent_quadratic_v1_with_exact_params_ok(
        self,
    ) -> None:
        ImStrayLoadModelDto(
            name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
            params=_params({"k_stray_load": 0.005}),
        )

    def test_current_dependent_quadratic_v1_missing_param_raises(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="必須ですが params が None"):
            ImStrayLoadModelDto(
                name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
                params=None,
            )

    def test_current_dependent_quadratic_v1_with_extra_param_raises(
        self,
    ) -> None:
        with pytest.raises(ValueError, match="余分"):
            ImStrayLoadModelDto(
                name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
                params=_params({"k_stray_load": 0.005, "extra": 0.1}),
            )

    def test_get_required_parameter_names(self) -> None:
        assert (
            ImStrayLoadModelDto(
                name=ImStrayLoadModelType.NONE
            ).get_required_parameter_names()
            == []
        )
        assert ImStrayLoadModelDto(
            name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
            params=_params({"k_stray_load": 0.005}),
        ).get_required_parameter_names() == ["k_stray_load"]
