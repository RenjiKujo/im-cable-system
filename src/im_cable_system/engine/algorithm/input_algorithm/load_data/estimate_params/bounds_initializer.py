"""bounds + init 仕様による R/L とモデル係数の初期化（estimate_params 用）。

EstimateParams の InputStage では、推定の初期値となる R/L とモデル係数を
:class:`ImParameterFitDescriptorBounds` /
:class:`CableParameterFitDescriptorBounds` の **bounds と init 設定**
（``midpoint`` / ``lb`` / ``ub`` / ``value`` のいずれか）から決定する。
本モジュールは Loader 内部から呼ばれる純関数群を提供する。

責務:
    - 固定 R/L / 単位長物性 / 接地物性の初期値生成
    - モデル種別ごとの必須パラメータ名定義
    - パラメータ名と spec から ``{param_name: initial}`` 辞書の生成

NOTE: 単位は :class:`ImParameterFitDescriptorBounds` /
:class:`CableParameterFitDescriptorBounds` の YAML 規約に準拠する SI 基本単位
（Ω / H / Ω/m / H/m / Ω·m / F/m）で固定する。
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ConductorModelType,
    ImExcitationModelType,
    ImPrimaryModelType,
    ImSecondaryModelType,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
    ImParameterFitDescriptorBounds,
)


def _primary_required_param_names(model: ImPrimaryModelType) -> list[str]:
    if model == ImPrimaryModelType.BASIC:
        return []
    if model == ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1:
        return [
            "alpha_primary_r",
            "alpha_primary_x",
            "beta_primary_x",
        ]
    if model == ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1:
        return [
            "alpha_primary_leakage_x",
            "beta_primary_leakage_x",
        ]
    raise ValueError(f"未対応の一次モデル型です: {model!r}")


def _excitation_required_param_names(
    model: ImExcitationModelType,
) -> list[str]:
    if model == ImExcitationModelType.BASIC:
        return []
    if model in (
        ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
        ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1,
    ):
        return [
            "alpha_excitation_r",
            "alpha_excitation_x",
            "beta_excitation_x",
        ]
    raise ValueError(f"未対応の励磁モデル型です: {model!r}")


def _secondary_required_param_names(
    model: ImSecondaryModelType,
) -> list[str]:
    if model == ImSecondaryModelType.BASIC:
        return []
    if model in (
        ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1,
        ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
    ):
        return [
            "alpha_secondary_r",
            "beta_secondary_r",
            "alpha_secondary_x",
            "beta_secondary_x",
        ]
    if model == ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1:
        return [
            "alpha_secondary_leakage_x",
            "beta_secondary_leakage_x",
        ]
    if (
        model
        == ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1
    ):
        return [
            "alpha_secondary_r",
            "beta_secondary_r",
            "alpha_secondary_x",
            "beta_secondary_x",
            "alpha_secondary_leakage_x",
            "beta_secondary_leakage_x",
        ]
    raise ValueError(f"未対応の二次モデル型です: {model!r}")


def _conductor_required_param_names(
    model: ConductorModelType,
) -> list[str]:
    if model == ConductorModelType.BASIC:
        return []
    if model in (
        ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
        ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
    ):
        return [
            "alpha_conductor_r",
            "beta_conductor_r",
            "alpha_conductor_x",
            "beta_conductor_x",
        ]
    raise ValueError(f"未対応の導体モデル型です: {model!r}")


def primary_model_param_initials(
    model: ImPrimaryModelType,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]:
    """一次モデル種別と境界から ``{param_name: initial}`` を返す。"""
    return {
        param: bounds.im_model_param_spec(
            subsystem="primary",
            model_type_name=model.value,
            param_name=param,
        ).resolve_initial()
        for param in _primary_required_param_names(model)
    }


def excitation_model_param_initials(
    model: ImExcitationModelType,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]:
    """励磁モデル種別と境界から ``{param_name: initial}`` を返す。"""
    return {
        param: bounds.im_model_param_spec(
            subsystem="excitation",
            model_type_name=model.value,
            param_name=param,
        ).resolve_initial()
        for param in _excitation_required_param_names(model)
    }


def secondary_model_param_initials(
    model: ImSecondaryModelType,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]:
    """二次モデル種別と境界から ``{param_name: initial}`` を返す。"""
    return {
        param: bounds.im_model_param_spec(
            subsystem="secondary",
            model_type_name=model.value,
            param_name=param,
        ).resolve_initial()
        for param in _secondary_required_param_names(model)
    }


def conductor_model_param_initials(
    model: ConductorModelType,
    bounds: CableParameterFitDescriptorBounds,
) -> dict[str, float]:
    """ケーブル導体モデルから ``{param_name: initial}`` を返す。"""
    return {
        param: bounds.conductor_model_param_spec(
            model_type_name=model.value,
            param_name=param,
        ).resolve_initial()
        for param in _conductor_required_param_names(model)
    }


def im_fixed_initial(
    key: str,
    bounds: ImParameterFitDescriptorBounds,
) -> float:
    """IM 固定 R/L の初期値を返す。"""
    return bounds.im_fixed_spec(key).resolve_initial()


def cable_fixed_initial(
    key: str,
    bounds: CableParameterFitDescriptorBounds,
) -> float:
    """ケーブル固定パラメータの初期値を返す。"""
    return bounds.cable_fixed_spec(key).resolve_initial()
