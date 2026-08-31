"""bounds + init 仕様による R/L とモデル係数の初期化（estimate_params 用）。

EstimateParams の InputStage では、推定の初期値となる R/L とモデル係数を
:class:`ImParameterFitDescriptorBounds` /
:class:`CableParameterFitDescriptorBounds` の **bounds と init 設定**
（``midpoint`` / ``lb`` / ``ub`` / ``value`` のいずれか）から決定する。
本モジュールは Loader 内部から呼ばれる純関数群を提供する。

責務:
    - 固定 R/L / 単位長物性 / 接地物性の初期値生成
    - bounds YAML が当該モデル種別に定義する係数をそのまま初期化する。
      名前集合の契約は DTO ``__post_init__`` が持つ
    - パラメータ名と spec から ``{param_name: initial}`` 辞書の生成

NOTE: 単位は :class:`ImParameterFitDescriptorBounds` /
:class:`CableParameterFitDescriptorBounds` の YAML 規約に準拠する SI 基本単位
（Ω / H / Ω/m / H/m / Ω·m / F/m）で固定する。
"""

from __future__ import annotations

from typing import Literal, overload

from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableConductorModelName,
    CableParameterFitDescriptorBounds,
    ImExcitationModelName,
    ImFrictionWindageModelName,
    ImParameterFitDescriptorBounds,
    ImPrimaryModelName,
    ImSecondaryModelName,
    ImStrayLoadModelName,
    ImSubsystemName,
)


# subsystem とモデル種別名 NewType の対応を型で固定する。実装シグネチャだけだと
# ``("secondary", combo.primary, ...)`` のような取り違えが型検査を素通りし、
# しかも一部の種別名（CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1 など）は
# primary / secondary の双方に存在するため KeyError にもならない。
@overload
def im_model_param_initials(
    subsystem: Literal["primary"],
    model: ImPrimaryModelName,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]: ...


@overload
def im_model_param_initials(
    subsystem: Literal["excitation"],
    model: ImExcitationModelName,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]: ...


@overload
def im_model_param_initials(
    subsystem: Literal["secondary"],
    model: ImSecondaryModelName,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]: ...


@overload
def im_model_param_initials(
    subsystem: Literal["friction_windage"],
    model: ImFrictionWindageModelName,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]: ...


@overload
def im_model_param_initials(
    subsystem: Literal["stray_load"],
    model: ImStrayLoadModelName,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]: ...


def im_model_param_initials(
    subsystem: ImSubsystemName,
    model: str,
    bounds: ImParameterFitDescriptorBounds,
) -> dict[str, float]:
    """bounds YAML が当該モデル種別に定義する全係数の初期値を返す。

    Args:
        subsystem: IM サブシステム名。
        model: モデル種別名。
        bounds: IM 探索境界。

    Returns:
        dict[str, float]: ``{param_name: initial}``。
            ``params: {}`` の種別では空辞書。

    Raises:
        KeyError: YAML に当該 ``model_type`` キーが無い場合。
    """
    return {
        name: spec.resolve_initial()
        for name, spec in bounds.im_model_param_specs(subsystem, model).items()
    }


def conductor_model_param_initials(
    model: CableConductorModelName,
    bounds: CableParameterFitDescriptorBounds,
) -> dict[str, float]:
    """bounds YAML が当該導体モデル種別に定義する全係数の初期値を返す。

    Args:
        model: 導体モデル種別名。
        bounds: ケーブル探索境界。

    Returns:
        dict[str, float]: ``{param_name: initial}``。
            ``params: {}`` の種別（``BASIC`` など）では空辞書。

    Raises:
        KeyError: YAML に当該 ``model_type`` キーが無い場合。
    """
    return {
        name: spec.resolve_initial()
        for name, spec in bounds.conductor_model_param_specs(model).items()
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
