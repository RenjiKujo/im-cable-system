"""``descriptor_apply.apply_im_path`` の単体テスト（内部実装の単体テスト）。

``friction_windage_model`` / ``stray_load_model`` の新 path 2 種の往復
（apply → 反映後の値読み出し）を検証する。``descriptor_apply`` は
``apply_fitted_input`` の公開窓口に載っていない内部実装のため、
リーフ直 import で検証する。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input.descriptor_apply import (  # noqa: E501
    apply_im_path,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImCageMultiplicityType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImSeriesDto,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.input import InputDtos


def _series_with_shaft_output_deduction_models(
    input_im_cable_system_dtos: InputDtos,
) -> ImSeriesDto:
    """SINGLE_CAGE の im_series を 1 件取り、軸出力控除モデルを差し替えて返す。"""
    for input_dto in input_im_cable_system_dtos.get_all():
        im_series = input_dto.im.im_series
        if (
            im_series is not None
            and im_series.cage_multiplicity
            == ImCageMultiplicityType.SINGLE_CAGE
        ):
            return replace(
                im_series,
                friction_windage_model=ImFrictionWindageModelDto(
                    name=ImFrictionWindageModelType.CONSTANT_V1,
                    params=FloatParamDtos(
                        objects=[
                            FloatParamDto(name="k_friction_windage", value=0.01)
                        ]
                    ),
                ),
                stray_load_model=ImStrayLoadModelDto(
                    name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
                    params=FloatParamDtos(
                        objects=[
                            FloatParamDto(name="k_stray_load", value=0.005)
                        ]
                    ),
                ),
            )
    raise AssertionError("SINGLE_CAGE の InputDto が見つかりません。")


class TestApplyImPathShaftOutputDeduction:
    """``friction_windage_model`` / ``stray_load_model`` の path 適用往復。"""

    def test_friction_windage_model_param_round_trips(
        self,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        im = _series_with_shaft_output_deduction_models(
            input_im_cable_system_dtos
        )
        updated = apply_im_path(
            im,
            ("im", "friction_windage_model", "params", "k_friction_windage"),
            0.03,
            None,
        )
        assert updated.friction_windage_model.params.get_by_name(
            "k_friction_windage"
        ).get_value() == pytest.approx(0.03)
        # 他フィールドは変更されない。
        assert updated.stray_load_model == im.stray_load_model

    def test_stray_load_model_param_round_trips(
        self,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        im = _series_with_shaft_output_deduction_models(
            input_im_cable_system_dtos
        )
        updated = apply_im_path(
            im,
            ("im", "stray_load_model", "params", "k_stray_load"),
            0.02,
            None,
        )
        assert updated.stray_load_model.params.get_by_name(
            "k_stray_load"
        ).get_value() == pytest.approx(0.02)
        assert updated.friction_windage_model == im.friction_windage_model

    def test_raises_when_friction_windage_params_is_none(
        self,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        im = _series_with_shaft_output_deduction_models(
            input_im_cable_system_dtos
        )
        im_none = replace(
            im,
            friction_windage_model=ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.NONE
            ),
        )
        with pytest.raises(ValueError, match="friction_windage_model.params"):
            apply_im_path(
                im_none,
                (
                    "im",
                    "friction_windage_model",
                    "params",
                    "k_friction_windage",
                ),
                0.03,
                None,
            )
