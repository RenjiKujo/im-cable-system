"""``float_param_dtos_from_dict`` の単体テスト。

モデルパラメータ辞書 → :class:`FloatParamDtos` 変換の純粋関数。
``None`` / 空辞書のスキップ規則と、要素変換時の :class:`FloatParamDto`
``__post_init__`` 契約への委譲を固定する。
"""

from __future__ import annotations

import math

import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.model_params_builder import (  # noqa: E501, PLC2701
    float_param_dtos_from_dict,
)


class TestFloatParamDtosFromDict:
    """``float_param_dtos_from_dict`` の挙動。"""

    def test_returns_none_when_input_is_none(self) -> None:
        assert float_param_dtos_from_dict(None) is None

    def test_returns_none_when_input_is_empty(self) -> None:
        assert float_param_dtos_from_dict({}) is None

    def test_single_entry_is_wrapped(self) -> None:
        result = float_param_dtos_from_dict({"alpha": 1.5})
        assert result is not None
        objs = result.get_all()
        assert len(objs) == 1
        assert objs[0].name == "alpha"
        assert objs[0].value == pytest.approx(1.5)

    def test_multiple_entries_preserve_insertion_order(self) -> None:
        """Python 3.7+ の dict 挿入順保持を前提に、順序が保たれることを確認。"""
        params = {"alpha": 1.0, "beta": 2.0, "gamma": 3.0}
        result = float_param_dtos_from_dict(params)
        assert result is not None
        names = [obj.name for obj in result.get_all()]
        assert names == ["alpha", "beta", "gamma"]

    def test_rejects_duplicate_name_via_collection_post_init(self) -> None:
        """同一 dict キーで重複 name は発生し得ないが、空文字 name は
        :class:`FloatParamDto.__post_init__` で raise されることを確認。"""
        with pytest.raises(ValueError, match="parameter name"):
            float_param_dtos_from_dict({"": 1.0})

    def test_rejects_non_finite_value_via_element_post_init(self) -> None:
        """値の NaN / inf は :class:`FloatParamDto.__post_init__` で raise。"""
        with pytest.raises(ValueError, match="finite"):
            float_param_dtos_from_dict({"alpha": math.inf})
        with pytest.raises(ValueError, match="finite"):
            float_param_dtos_from_dict({"alpha": math.nan})
