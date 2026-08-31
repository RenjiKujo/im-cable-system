"""IM パラメータフィット記述子の探索上下限（im_descriptor_bounds_and_init.yaml 由来）。

``im_cable_system.execution.estimate_params.parameter_definitions.im_file_path`` で
指定される YAML のルート（``primary`` / ``excitation`` / ``secondary``）を解釈する。
固定 R/L とモデル係数の欠損は設定誤りとして扱う。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, NewType

from im_cable_system.engine.shared.estimate_params_fit_spec.parameter_fit_spec import (  # noqa: E501
    ParameterFitSpec,
)
from im_cable_system.engine.shared.estimate_params_fit_spec.yaml_bounds_parsing import (  # noqa: E501
    document_body_without_version,
    parse_fixed_parameters_block_with_init,
    parse_model_parameters_block_with_init,
)

ImSubsystemName = Literal[
    "primary",
    "excitation",
    "secondary",
    "friction_windage",
    "stray_load",
]

# subsystem ごとにモデル種別名を型で分離する。bounds YAML には
# CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1 のように複数 subsystem に同名キーが
# 存在するものがあり、素の str だと取り違えが KeyError にすらならない。
# NewType はランタイムでは恒等関数で、値の検証は一切行わない
# （検証は _assemble_input_dto 段の DTO __post_init__ が持つ）。
ImPrimaryModelName = NewType("ImPrimaryModelName", str)
ImExcitationModelName = NewType("ImExcitationModelName", str)
ImSecondaryModelName = NewType("ImSecondaryModelName", str)
ImFrictionWindageModelName = NewType("ImFrictionWindageModelName", str)
ImStrayLoadModelName = NewType("ImStrayLoadModelName", str)

_REQUIRED_FIXED_IM_KEYS: tuple[str, ...] = (
    "primary_resistance",
    "primary_inductance",
    "excitation_resistance",
    "excitation_inductance",
    "secondary_resistance",
    "secondary_inductance",
)


def _model_type_key(model_type_name: str | Enum) -> str:
    """モデル種別名を YAML キー文字列に正規化する。"""
    if isinstance(model_type_name, Enum):
        return str(model_type_name.value)
    return model_type_name


def _require_fixed_specs(
    fixed_specs: dict[str, ParameterFitSpec],
) -> dict[str, ParameterFitSpec]:
    """IM 固定 R/L の必須キーが YAML に全て存在することを確認する。"""
    missing = [key for key in _REQUIRED_FIXED_IM_KEYS if key not in fixed_specs]
    if missing:
        missing_keys = ", ".join(missing)
        raise ValueError(
            f"IM bounds YAML missing required fixed parameters: {missing_keys}"
        )
    return fixed_specs


@dataclass(frozen=True)
class ImParameterFitDescriptorBounds:
    """IM 固定 R・L と IM モデル係数の探索境界 + 初期化仕様。

    bounds と init 設定は :class:`ParameterFitSpec` で保持する。
    既存の ``im_fixed`` / ``im_model_param`` は spec から ``(lb, ub)``
    タプルを返すアダプタ。新規利用は ``*_spec`` 系 API を推奨。
    """

    _fixed_im_specs: dict[str, ParameterFitSpec]
    _primary_model_specs: dict[str, dict[str, ParameterFitSpec]]
    _excitation_model_specs: dict[str, dict[str, ParameterFitSpec]]
    _secondary_model_specs: dict[str, dict[str, ParameterFitSpec]]
    _friction_windage_model_specs: dict[str, dict[str, ParameterFitSpec]]
    _stray_load_model_specs: dict[str, dict[str, ParameterFitSpec]]

    @classmethod
    def from_estimation_document(
        cls,
        document: dict[str, Any],
    ) -> ImParameterFitDescriptorBounds:
        """im_descriptor_bounds_and_init.yaml 相当のルート辞書から構築する。

        Args:
            document: ``yaml.safe_load`` 結果。``version`` 以外のトップレベルが
                ``primary`` / ``excitation`` / ``secondary``。レガシーとして
                ``im_cable_system.im`` があればそちらを優先する。

        Returns:
            ImParameterFitDescriptorBounds: 解釈結果。

        Raises:
            ValueError: ``bounds`` が無い・``lb``/``ub`` の片方欠落、``init``
                設定が無い、``init.method`` が未対応の値、``method='value'``
                で ``value`` が無い、または固定 R/L の必須キーが無い場合。
        """
        im_node = _resolve_im_subtree(document)
        if not isinstance(im_node, dict):
            im_node = {}

        im_fixed: dict[str, ParameterFitSpec] = {}
        for part in ("primary", "excitation", "secondary"):
            sub = im_node.get(part, {})
            if isinstance(sub, dict):
                im_fixed.update(parse_fixed_parameters_block_with_init(sub))

        primary_mt: dict[str, dict[str, ParameterFitSpec]] = {}
        excitation_mt: dict[str, dict[str, ParameterFitSpec]] = {}
        secondary_mt: dict[str, dict[str, ParameterFitSpec]] = {}
        friction_windage_mt: dict[str, dict[str, ParameterFitSpec]] = {}
        stray_load_mt: dict[str, dict[str, ParameterFitSpec]] = {}
        prim = im_node.get("primary", {})
        exc = im_node.get("excitation", {})
        sec = im_node.get("secondary", {})
        # friction_windage / stray_load はイミタンスを持たず rl_parameters が
        # 無いため、im_fixed には含めない（primary/excitation/secondary との
        # ループとは別にモデル係数だけを読む）。
        fw = im_node.get("friction_windage", {})
        sl = im_node.get("stray_load", {})
        if isinstance(prim, dict):
            primary_mt = parse_model_parameters_block_with_init(prim)
        if isinstance(exc, dict):
            excitation_mt = parse_model_parameters_block_with_init(exc)
        if isinstance(sec, dict):
            secondary_mt = parse_model_parameters_block_with_init(sec)
        if isinstance(fw, dict):
            friction_windage_mt = parse_model_parameters_block_with_init(fw)
        if isinstance(sl, dict):
            stray_load_mt = parse_model_parameters_block_with_init(sl)

        return cls(
            _fixed_im_specs=_require_fixed_specs(im_fixed),
            _primary_model_specs=primary_mt,
            _excitation_model_specs=excitation_mt,
            _secondary_model_specs=secondary_mt,
            _friction_windage_model_specs=friction_windage_mt,
            _stray_load_model_specs=stray_load_mt,
        )

    def im_fixed(self, key: str) -> tuple[float, float]:
        """一次・励磁・二次の固定 R/L など（枝共通の secondary_*）の境界。"""
        spec = self.im_fixed_spec(key)
        return (spec.lb, spec.ub)

    def im_fixed_spec(self, key: str) -> ParameterFitSpec:
        """固定 R/L の bounds + init 仕様。

        Raises:
            KeyError: YAML に無い未知キーが与えられた場合。
        """
        if key in self._fixed_im_specs:
            return self._fixed_im_specs[key]
        raise KeyError(f"unknown IM fixed parameter in bounds YAML: {key}")

    def im_model_param(
        self,
        subsystem: ImSubsystemName,
        model_type_name: str | Enum,
        param_name: str,
    ) -> tuple[float, float]:
        """一次・励磁・二次・摩擦風損・漂遊負荷損のモデル係数の境界。

        Raises:
            KeyError: YAML にモデル種別またはパラメータ名が定義されて
                いない場合。
        """
        spec = self.im_model_param_spec(
            subsystem=subsystem,
            model_type_name=model_type_name,
            param_name=param_name,
        )
        return (spec.lb, spec.ub)

    def im_model_param_specs(
        self,
        subsystem: ImSubsystemName,
        model_type_name: str | Enum,
    ) -> dict[str, ParameterFitSpec]:
        """当該モデル種別の params 行を丸ごと返す（コピー）。

        Args:
            subsystem: IM サブシステム名。
            model_type_name: モデル種別（文字列または Enum）。

        Returns:
            dict[str, ParameterFitSpec]: 係数名 → bounds/init 仕様。
                ``params: {}`` の種別では空辞書。

        Raises:
            KeyError: YAML に当該 ``model_type`` キーが無い場合。
        """
        if subsystem == "primary":
            table = self._primary_model_specs
        elif subsystem == "excitation":
            table = self._excitation_model_specs
        elif subsystem == "secondary":
            table = self._secondary_model_specs
        elif subsystem == "friction_windage":
            table = self._friction_windage_model_specs
        else:
            table = self._stray_load_model_specs
        model_key = _model_type_key(model_type_name)
        if model_key not in table:
            raise KeyError(
                f"unknown IM {subsystem} model in bounds YAML: {model_key}"
            )
        return dict(table[model_key])

    def im_model_param_spec(
        self,
        subsystem: ImSubsystemName,
        model_type_name: str | Enum,
        param_name: str,
    ) -> ParameterFitSpec:
        """モデル係数の bounds + init 仕様。

        Raises:
            KeyError: YAML にモデル種別またはパラメータ名が定義されて
                いない場合。
        """
        model_key = _model_type_key(model_type_name)
        model_row = self.im_model_param_specs(subsystem, model_type_name)
        if param_name not in model_row:
            raise KeyError(
                f"missing bounds/init for IM {subsystem} model parameter: "
                f"{model_key}.{param_name}"
            )
        return model_row[param_name]


def _resolve_im_subtree(document: dict[str, Any]) -> dict[str, Any]:
    """フラット root またはレガシー ``im_cable_system.im`` から IM ノードを得る。"""
    legacy = document.get("im_cable_system")
    if isinstance(legacy, dict):
        inner = legacy.get("im")
        if isinstance(inner, dict):
            return inner
    return document_body_without_version(document)
