"""共通 ``build_cable_dto`` が、導体モデル名・係数の不正を
文脈付き ValueError として通知することを確認するテスト。

本ファイルは ``_conductor_model_dto`` のエラー文脈に寄せる。
経路別アセンブラの正常系 smoke は各経路配下で確認する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.cable_dto_builder import (  # noqa: E501
    build_cable_dto,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
    CableSectionLoadedData,
)


def _section() -> CableSectionLoadedData:
    """モデル係数の検証に影響しない最小のケーブル区間を返す。"""
    return CableSectionLoadedData(
        name="dummy_series",
        length=10.0,
        length_unit="m",
        shape_type="ROUND",
        conductor_resistance_per_length=1.0e-3,
        conductor_resistance_per_length_unit="Ω/m",
        conductor_inductance_per_length=1.0e-6,
        conductor_inductance_per_length_unit="H/m",
        ground_resistance_length=1.0e3,
        ground_resistance_length_unit="Ω*m",
        ground_capacitance_per_length=1.0e-10,
        ground_capacitance_per_length_unit="F/m",
    )


def _cable_loaded(
    *,
    name: str = "cable_sample",
    conductor_model: str = "BASIC",
    conductor_model_params: dict[str, float] | None = None,
) -> CableLoadedData:
    return CableLoadedData(
        name=name,
        sections=(_section(),),
        conductor_model=conductor_model,
        conductor_model_params=conductor_model_params,
    )


class TestCableDtoBuilderEnumErrors:
    """``conductor_model`` 名が Enum 変換できないときの文脈付きエラー。"""

    def test_unknown_conductor_model_raises_with_cable_name(self) -> None:
        cable_loaded = _cable_loaded(
            name="cable_sample",
            conductor_model="NOT_A_MODEL",
        )
        with pytest.raises(ValueError) as excinfo:
            build_cable_dto(cable_loaded)
        msg = str(excinfo.value)
        assert "'cable_sample'" in msg
        assert "NOT_A_MODEL" in msg
        assert "conductor_model" in msg

    def test_unknown_conductor_model_lists_allowed_values(self) -> None:
        """エラー文面に「取り得る値」一覧が含まれる。"""
        with pytest.raises(ValueError) as excinfo:
            build_cable_dto(_cable_loaded(conductor_model="NOT_A_MODEL"))
        msg = str(excinfo.value)
        assert "取り得る値" in msg
        assert "BASIC" in msg
        assert "CURRENT_DEPENDENT_SKIN_EFFECT_V1" in msg


class TestCableDtoBuilderParamErrors:
    """``conductor_model_params`` がモデル仕様と整合しないときのエラー。"""

    def test_missing_required_param_raises_with_context(self) -> None:
        """必須係数の不足は ``不足`` を含む文脈付きエラー。"""
        cable_loaded = _cable_loaded(
            name="cable_sample",
            conductor_model="CURRENT_DEPENDENT_SKIN_EFFECT_V1",
            conductor_model_params={
                "alpha_conductor_r": 0.1,
                "beta_conductor_r": 0.2,
                "alpha_conductor_x": 0.3,
            },
        )
        with pytest.raises(ValueError) as excinfo:
            build_cable_dto(cable_loaded)
        msg = str(excinfo.value)
        assert "'cable_sample'" in msg
        assert "conductor_model" in msg
        assert "不足" in msg

    def test_extra_param_raises_with_context(self) -> None:
        """必須集合外の係数は ``余分`` を含む文脈付きエラー。"""
        cable_loaded = _cable_loaded(
            name="cable_sample",
            conductor_model="CURRENT_DEPENDENT_SKIN_EFFECT_V1",
            conductor_model_params={
                "alpha_conductor_r": 0.1,
                "beta_conductor_r": 0.2,
                "alpha_conductor_x": 0.3,
                "beta_conductor_x": 0.4,
                "unexpected_param": 9.9,
            },
        )
        with pytest.raises(ValueError) as excinfo:
            build_cable_dto(cable_loaded)
        msg = str(excinfo.value)
        assert "'cable_sample'" in msg
        assert "余分" in msg

    def test_nonfinite_param_value_raises_with_context(self) -> None:
        """``NaN`` などの非 finite 値は係数値のバリデーションでエラー。"""
        cable_loaded = _cable_loaded(
            name="cable_sample",
            conductor_model="CURRENT_DEPENDENT_SKIN_EFFECT_V1",
            conductor_model_params={
                "alpha_conductor_r": float("nan"),
                "beta_conductor_r": 0.2,
                "alpha_conductor_x": 0.3,
                "beta_conductor_x": 0.4,
            },
        )
        with pytest.raises(ValueError) as excinfo:
            build_cable_dto(cable_loaded)
        msg = str(excinfo.value)
        assert "'cable_sample'" in msg
        assert "conductor_model" in msg
