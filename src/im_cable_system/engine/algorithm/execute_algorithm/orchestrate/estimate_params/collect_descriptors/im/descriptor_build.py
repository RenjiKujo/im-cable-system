"""IM フィット記述子の組み立て（estimate_params 専用）。

一次・励磁・二次の :class:`FittableParamDescriptor` 付与を提供する。
探索上下限は
:class:`~im_cable_system.engine.shared.estimate_params_fit_spec.ImParameterFitDescriptorBounds`
（config 経由）を参照する。二次かご枝は path に枝名（Enum の value）を含めて区別する。
記述子の DTO への適用は :mod:`apply_fitted_input.descriptor_apply` を参照。
"""

from __future__ import annotations

from typing import Literal

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImExcitationModelDto,
    ImPrimaryModelDto,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSeriesDto,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    ImParameterFitDescriptorBounds,
)


def get_model_param_names(
    model_dto: ImPrimaryModelDto | ImExcitationModelDto | ImSecondaryModelDto,
) -> list[str]:
    """モデル DTO の get_required_parameter_names を共通で呼ぶ。"""
    if hasattr(model_dto, "get_required_parameter_names"):
        return model_dto.get_required_parameter_names()
    return []


def append_primary_and_excitation_fixed_rl_descriptors(
    im_series_dto: ImSeriesDto,
    bounds: ImParameterFitDescriptorBounds,
    descriptors: list[FittableParamDescriptor],
) -> None:
    """一次・励磁の固定 R/L 4 個の記述子を descriptors に追加する。"""
    pr_lb, pr_ub = bounds.im_fixed("primary_resistance")
    pl_lb, pl_ub = bounds.im_fixed("primary_inductance")
    er_lb, er_ub = bounds.im_fixed("excitation_resistance")
    el_lb, el_ub = bounds.im_fixed("excitation_inductance")
    descriptors.append(
        FittableParamDescriptor(
            path=("im", "primary_resistance"),
            current_value=im_series_dto.primary_resistance.get_value(),
            lb=pr_lb,
            ub=pr_ub,
            unit=im_series_dto.primary_resistance.get_unit(),
        )
    )
    descriptors.append(
        FittableParamDescriptor(
            path=("im", "primary_inductance"),
            current_value=im_series_dto.primary_inductance.get_value(),
            lb=pl_lb,
            ub=pl_ub,
            unit=im_series_dto.primary_inductance.get_unit(),
        )
    )
    descriptors.append(
        FittableParamDescriptor(
            path=("im", "excitation_resistance"),
            current_value=im_series_dto.excitation_resistance.get_value(),
            lb=er_lb,
            ub=er_ub,
            unit=im_series_dto.excitation_resistance.get_unit(),
        )
    )
    descriptors.append(
        FittableParamDescriptor(
            path=("im", "excitation_inductance"),
            current_value=im_series_dto.excitation_inductance.get_value(),
            lb=el_lb,
            ub=el_ub,
            unit=im_series_dto.excitation_inductance.get_unit(),
        )
    )


def append_primary_and_excitation_model_param_descriptors(
    im_series_dto: ImSeriesDto,
    bounds: ImParameterFitDescriptorBounds,
    descriptors: list[FittableParamDescriptor],
) -> None:
    """一次・励磁モデルの params 記述子を descriptors に追加する。"""
    append_model_param_descriptors(
        model_attr="primary_model",
        model_kind="primary",
        model_dto=im_series_dto.primary_model,
        bounds=bounds,
        descriptors=descriptors,
    )
    append_model_param_descriptors(
        model_attr="excitation_model",
        model_kind="excitation",
        model_dto=im_series_dto.excitation_model,
        bounds=bounds,
        descriptors=descriptors,
    )


def append_model_param_descriptors(
    *,
    model_attr: str,
    model_kind: Literal["primary", "excitation"],
    model_dto: ImPrimaryModelDto | ImExcitationModelDto,
    bounds: ImParameterFitDescriptorBounds,
    descriptors: list[FittableParamDescriptor],
) -> None:
    """一次・励磁モデルの params 記述子を追加する。"""
    param_names = get_model_param_names(model_dto)
    if not param_names or model_dto.params is None:
        return
    model_name = model_dto.name
    for name in param_names:
        param = model_dto.params.get_by_name(name)
        if param is None:
            continue
        plb, pub = bounds.im_model_param(model_kind, model_name, name)
        descriptors.append(
            FittableParamDescriptor(
                path=("im", model_attr, "params", name),
                current_value=param.get_value(),
                lb=plb,
                ub=pub,
                unit=None,
            )
        )


def append_secondary_branch_fixed_rl_descriptors(
    im_series_dto: ImSeriesDto,
    branch: ImSecondaryCageBranchType,
    bounds: ImParameterFitDescriptorBounds,
    descriptors: list[FittableParamDescriptor],
) -> None:
    """指定二次枝の R/L 記述子のみ追加する。"""
    branch_key = branch.value
    sec_r = im_series_dto.secondary_resistances[branch]
    sec_x = im_series_dto.secondary_inductances[branch]
    sr_lb, sr_ub = bounds.im_fixed("secondary_resistance")
    sx_lb, sx_ub = bounds.im_fixed("secondary_inductance")
    descriptors.append(
        FittableParamDescriptor(
            path=("im", "secondary_resistance", branch_key),
            current_value=sec_r.get_value(),
            lb=sr_lb,
            ub=sr_ub,
            unit=sec_r.get_unit(),
        )
    )
    descriptors.append(
        FittableParamDescriptor(
            path=("im", "secondary_inductance", branch_key),
            current_value=sec_x.get_value(),
            lb=sx_lb,
            ub=sx_ub,
            unit=sec_x.get_unit(),
        )
    )


def append_secondary_branch_model_param_descriptors(
    im_series_dto: ImSeriesDto,
    branch: ImSecondaryCageBranchType,
    bounds: ImParameterFitDescriptorBounds,
    descriptors: list[FittableParamDescriptor],
) -> None:
    """指定二次枝のモデル params 記述子のみ追加する。"""
    branch_key = branch.value
    model_dto = im_series_dto.secondary_models[branch]
    param_names = get_model_param_names(model_dto)
    if not param_names or model_dto.params is None:
        return
    model_name = model_dto.name
    for name in param_names:
        param = model_dto.params.get_by_name(name)
        if param is None:
            continue
        plb, pub = bounds.im_model_param("secondary", model_name, name)
        descriptors.append(
            FittableParamDescriptor(
                path=(
                    "im",
                    "secondary_model",
                    branch_key,
                    "params",
                    name,
                ),
                current_value=param.get_value(),
                lb=plb,
                ub=pub,
                unit=None,
            )
        )
