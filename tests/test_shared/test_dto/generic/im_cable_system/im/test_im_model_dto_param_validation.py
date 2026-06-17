"""IM 各モデル DTO の __post_init__ パラメータ検証テスト。

カバー対象:
    - ``ImPrimaryModelDto``
    - ``ImExcitationModelDto``
    - ``ImSecondaryModelDto``

それぞれについて以下を検証する。
    - 必須名が完全に揃っていれば OK
    - 必須名が足りない → ValueError（"不足"）
    - 余分な名前が混ざる → ValueError（"余分"）
    - 必須があるのに params=None → ValueError
    - パラメータを取らないモデルに params が指定されている → ValueError
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)


def _params(items: dict[str, float]) -> FloatParamDtos:
    return FloatParamDtos(
        objects=[FloatParamDto(name=n, value=v) for n, v in items.items()]
    )


class TestImPrimaryModelDtoValidation:
    """ImPrimaryModelDto の __post_init__ テスト。"""

    def test_basic_with_none_params_ok(self) -> None:
        ImPrimaryModelDto(name=ImPrimaryModelType.BASIC, params=None)

    def test_basic_with_extra_params_raises(self) -> None:
        with pytest.raises(ValueError, match="パラメータを取らないモデル"):
            ImPrimaryModelDto(
                name=ImPrimaryModelType.BASIC,
                params=_params({"alpha_primary_r": 1.0}),
            )

    def test_slip_dep_with_exact_params_ok(self) -> None:
        ImPrimaryModelDto(
            name=ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1,
            params=_params(
                {
                    "alpha_primary_r": 0.1,
                    "alpha_primary_x": 0.2,
                    "beta_primary_x": 0.3,
                }
            ),
        )

    def test_slip_dep_missing_param_raises(self) -> None:
        with pytest.raises(ValueError, match="不足"):
            ImPrimaryModelDto(
                name=ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1,
                params=_params(
                    {
                        "alpha_primary_r": 0.1,
                        "alpha_primary_x": 0.2,
                    }
                ),
            )

    def test_slip_dep_with_extra_param_raises(self) -> None:
        with pytest.raises(ValueError, match="余分"):
            ImPrimaryModelDto(
                name=ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1,
                params=_params(
                    {
                        "alpha_primary_r": 0.1,
                        "alpha_primary_x": 0.2,
                        "beta_primary_x": 0.3,
                        "extra_param": 0.4,
                    }
                ),
            )

    def test_slip_dep_none_params_raises(self) -> None:
        with pytest.raises(ValueError, match="必須ですが params が None"):
            ImPrimaryModelDto(
                name=ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1,
                params=None,
            )


class TestImExcitationModelDtoValidation:
    """ImExcitationModelDto の __post_init__ テスト。"""

    def test_basic_with_none_params_ok(self) -> None:
        ImExcitationModelDto(name=ImExcitationModelType.BASIC, params=None)

    def test_slip_dep_with_exact_params_ok(self) -> None:
        ImExcitationModelDto(
            name=ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
            params=_params(
                {
                    "alpha_excitation_r": 0.1,
                    "alpha_excitation_x": 0.2,
                    "beta_excitation_x": 0.3,
                }
            ),
        )

    def test_slip_dep_with_extra_param_raises(self) -> None:
        with pytest.raises(ValueError, match="余分"):
            ImExcitationModelDto(
                name=ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
                params=_params(
                    {
                        "alpha_excitation_r": 0.1,
                        "alpha_excitation_x": 0.2,
                        "beta_excitation_x": 0.3,
                        "extra": 0.4,
                    }
                ),
            )

    def test_slip_dep_missing_param_raises(self) -> None:
        with pytest.raises(ValueError, match="不足"):
            ImExcitationModelDto(
                name=ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
                params=_params({"alpha_excitation_r": 0.1}),
            )


class TestImSecondaryModelDtoValidation:
    """ImSecondaryModelDto の __post_init__ テスト。"""

    def test_basic_with_none_params_ok(self) -> None:
        ImSecondaryModelDto(name=ImSecondaryModelType.BASIC, params=None)

    def test_slip_dep_skin_effect_exact_params_ok(self) -> None:
        ImSecondaryModelDto(
            name=ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1,
            params=_params(
                {
                    "alpha_secondary_r": 0.1,
                    "beta_secondary_r": 1.0,
                    "alpha_secondary_x": 0.2,
                    "beta_secondary_x": 1.0,
                }
            ),
        )

    def test_slip_dep_skin_effect_extra_param_raises(self) -> None:
        with pytest.raises(ValueError, match="余分"):
            ImSecondaryModelDto(
                name=ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1,
                params=_params(
                    {
                        "alpha_secondary_r": 0.1,
                        "beta_secondary_r": 1.0,
                        "alpha_secondary_x": 0.2,
                        "beta_secondary_x": 1.0,
                        "extra": 0.5,
                    }
                ),
            )

    def test_current_dep_skin_effect_and_leakage_full_set_ok(self) -> None:
        ImSecondaryModelDto(
            name=ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1,
            params=_params(
                {
                    "alpha_secondary_r": 0.1,
                    "beta_secondary_r": 1.0,
                    "alpha_secondary_x": 0.2,
                    "beta_secondary_x": 1.0,
                    "alpha_secondary_leakage_x": 0.3,
                    "beta_secondary_leakage_x": 1.5,
                }
            ),
        )
