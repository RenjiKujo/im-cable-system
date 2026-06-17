"""CableConductorModelDto の __post_init__ パラメータ検証テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    ConductorModelType,
    FloatParamDto,
    FloatParamDtos,
)


def _params(items: dict[str, float]) -> FloatParamDtos:
    return FloatParamDtos(
        objects=[FloatParamDto(name=n, value=v) for n, v in items.items()]
    )


class TestCableConductorModelDtoValidation:
    """CableConductorModelDto の __post_init__ テスト。"""

    def test_basic_with_none_params_ok(self) -> None:
        CableConductorModelDto(name=ConductorModelType.BASIC, params=None)

    def test_basic_with_extra_params_raises(self) -> None:
        with pytest.raises(ValueError, match="パラメータを取らないモデル"):
            CableConductorModelDto(
                name=ConductorModelType.BASIC,
                params=_params({"alpha_conductor_r": 1.0}),
            )

    def test_frequency_dependent_full_params_ok(self) -> None:
        CableConductorModelDto(
            name=ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
            params=_params(
                {
                    "alpha_conductor_r": 0.1,
                    "beta_conductor_r": 1.0,
                    "alpha_conductor_x": 0.2,
                    "beta_conductor_x": 1.0,
                }
            ),
        )

    def test_frequency_dependent_missing_param_raises(self) -> None:
        with pytest.raises(ValueError, match="不足"):
            CableConductorModelDto(
                name=ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
                params=_params(
                    {
                        "alpha_conductor_r": 0.1,
                        "beta_conductor_r": 1.0,
                    }
                ),
            )

    def test_frequency_dependent_extra_param_raises(self) -> None:
        with pytest.raises(ValueError, match="余分"):
            CableConductorModelDto(
                name=ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
                params=_params(
                    {
                        "alpha_conductor_r": 0.1,
                        "beta_conductor_r": 1.0,
                        "alpha_conductor_x": 0.2,
                        "beta_conductor_x": 1.0,
                        "extra": 0.5,
                    }
                ),
            )
