"""ケーブル π 型パラメータフィット記述子の探索上下限（cable_descriptor_bounds_and_init.yaml 由来）。

``im_cable_system.execution.estimate_params.parameter_definitions.cable_file_path`` で
指定される YAML のルート（``conductor`` / ``ground``）を解釈する。
固定パラメータとモデル係数の欠損は設定誤りとして扱う。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from im_cable_system.engine.shared.estimate_params_fit_spec.parameter_fit_spec import (  # noqa: E501
    ParameterFitSpec,
)
from im_cable_system.engine.shared.estimate_params_fit_spec.yaml_bounds_parsing import (  # noqa: E501
    document_body_without_version,
    parse_fixed_parameters_block_with_init,
    parse_model_parameters_block_with_init,
)

_REQUIRED_FIXED_CABLE_KEYS: tuple[str, ...] = (
    "conductor_resistance_per_length",
    "conductor_inductance_per_length",
    "ground_resistance_length",
    "ground_capacitance_per_length",
)


def _model_type_key(model_type_name: str | Enum) -> str:
    """モデル種別名を YAML キー文字列に正規化する。"""
    if isinstance(model_type_name, Enum):
        return str(model_type_name.value)
    return model_type_name


def _require_fixed_specs(
    fixed_specs: dict[str, ParameterFitSpec],
) -> dict[str, ParameterFitSpec]:
    """ケーブル固定パラメータの必須キーが YAML に全て存在することを確認する。"""
    missing = [
        key for key in _REQUIRED_FIXED_CABLE_KEYS if key not in fixed_specs
    ]
    if missing:
        missing_keys = ", ".join(missing)
        raise ValueError(
            "cable bounds YAML missing required fixed parameters: "
            f"{missing_keys}"
        )
    return fixed_specs


@dataclass(frozen=True)
class CableParameterFitDescriptorBounds:
    """ケーブル導体・ground 固定パラメータと導体モデル係数の探索境界 + 初期化仕様。

    bounds と init 設定は :class:`ParameterFitSpec` で保持する。既存の
    ``cable_fixed`` / ``conductor_model_param`` は spec から ``(lb, ub)``
    タプルを返すアダプタ。新規利用は ``*_spec`` 系 API を推奨。
    """

    _fixed_cable_specs: dict[str, ParameterFitSpec]
    _conductor_model_specs: dict[str, dict[str, ParameterFitSpec]]

    @classmethod
    def from_estimation_document(
        cls,
        document: dict[str, Any],
    ) -> CableParameterFitDescriptorBounds:
        """cable_descriptor_bounds_and_init.yaml 相当のルート辞書から構築する。

        Args:
            document: ``yaml.safe_load`` 結果。``version`` 以外のトップレベルが
                ``conductor`` / ``ground``。レガシーとして ``im_cable_system.cable``
                があればそちらを優先する。

        Returns:
            CableParameterFitDescriptorBounds: 解釈結果。

        Raises:
            ValueError: ``bounds`` が無い・``lb``/``ub`` の片方欠落、``init``
                設定が無い、``init.method`` が未対応の値、``method='value'``
                で ``value`` が無い、または固定パラメータの必須キーが無い場合。
        """
        cable_node = _resolve_cable_subtree(document)
        if not isinstance(cable_node, dict):
            cable_node = {}

        cable_fixed: dict[str, ParameterFitSpec] = {}
        for edge_name in ("conductor", "ground"):
            sub = cable_node.get(edge_name, {})
            if isinstance(sub, dict):
                cable_fixed.update(parse_fixed_parameters_block_with_init(sub))

        cond = cable_node.get("conductor", {})
        conductor_mt: dict[str, dict[str, ParameterFitSpec]] = {}
        if isinstance(cond, dict):
            conductor_mt = parse_model_parameters_block_with_init(cond)

        return cls(
            _fixed_cable_specs=_require_fixed_specs(cable_fixed),
            _conductor_model_specs=conductor_mt,
        )

    def cable_fixed(self, key: str) -> tuple[float, float]:
        """ケーブル π 型の導体・アース固定パラメータの境界。"""
        spec = self.cable_fixed_spec(key)
        return (spec.lb, spec.ub)

    def cable_fixed_spec(self, key: str) -> ParameterFitSpec:
        """固定 R/L/C の bounds + init 仕様。

        Raises:
            KeyError: YAML に無い未知キーが与えられた場合。
        """
        if key in self._fixed_cable_specs:
            return self._fixed_cable_specs[key]
        raise KeyError(f"unknown cable fixed parameter in bounds YAML: {key}")

    def conductor_model_param(
        self,
        model_type_name: str | Enum,
        param_name: str,
    ) -> tuple[float, float]:
        """導体モデル係数の境界。

        Raises:
            KeyError: YAML にモデル種別またはパラメータ名が定義されて
                いない場合。
        """
        spec = self.conductor_model_param_spec(
            model_type_name=model_type_name,
            param_name=param_name,
        )
        return (spec.lb, spec.ub)

    def conductor_model_param_spec(
        self,
        model_type_name: str | Enum,
        param_name: str,
    ) -> ParameterFitSpec:
        """導体モデル係数の bounds + init 仕様。

        Raises:
            KeyError: YAML にモデル種別またはパラメータ名が定義されて
                いない場合。
        """
        model_key = _model_type_key(model_type_name)
        if model_key not in self._conductor_model_specs:
            raise KeyError(
                f"unknown conductor model in bounds YAML: {model_key}"
            )
        model_row = self._conductor_model_specs[model_key]
        if param_name not in model_row:
            raise KeyError(
                "missing bounds/init for conductor model parameter: "
                f"{model_key}.{param_name}"
            )
        return model_row[param_name]


def _resolve_cable_subtree(document: dict[str, Any]) -> dict[str, Any]:
    """フラット root またはレガシー ``im_cable_system.cable`` からケーブルノードを得る。"""
    legacy = document.get("im_cable_system")
    if isinstance(legacy, dict):
        inner = legacy.get("cable")
        if isinstance(inner, dict):
            return inner
    return document_body_without_version(document)
