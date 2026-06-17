"""フィット記述子の DTO への path 適用（estimate_params 専用）。

``apply_*_from_descriptors`` と path ベースの DTO 更新ヘルパを提供する。
ケーブルは **セクション 1 本** 前提（推定オーケストレーターと同一）。
二次かご枝は path に枝名（Enum の value）を含めて区別する。
記述子の組み立ては :mod:`collect_descriptors.im.descriptor_build` /
:mod:`collect_descriptors.cable.descriptor_build` を参照。
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    CableSectionDtos,
    CableSeriesDto,
    FloatParamDto,
    FloatParamDtos,
    ImSecondaryCageBranchType,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitancePerLengthDto,
    FloatInductanceDto,
    FloatInductancePerLengthDto,
    FloatResistanceDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


def apply_im_from_descriptors(
    im_series_dto: ImSeriesDto,
    descriptors: list[FittableParamDescriptor],
    x: np.ndarray,
) -> ImSeriesDto:
    """IM 記述子とベクトル x から ImSeriesDto を更新する。"""
    n = len(descriptors)
    if len(x) != n:
        raise ValueError(
            f"x の長さ {len(x)} が descriptors の長さ {n} と一致しません。"
        )
    new_im = im_series_dto
    for idx, desc in enumerate(descriptors):
        if desc.path[0] != "im":
            raise ValueError(f"IM 記述子以外が混在しています: path={desc.path}")
        val = float(x[idx])
        val = max(desc.lb, min(desc.ub, val))
        new_im = apply_im_path(new_im, desc.path, val, desc.unit)
    return new_im


def apply_cable_dto_from_descriptors(
    cable_dto: CableDto,
    descriptors: list[FittableParamDescriptor],
    x: np.ndarray,
) -> CableDto:
    """ケーブル記述子とベクトル x から CableDto を更新する（1 セクション前提）。

    π 型は第 1 セクションの :class:`CableSeriesDto` に、導体モデル係数は
    ``conductor_model.params`` に反映する。

    Args:
        cable_dto: 元のケーブル DTO。
        descriptors: ``collect_cable_fittable_descriptors`` と同一順序の記述子。
        x: 各記述子に対応する値。

    Returns:
        更新後の CableDto。

    Raises:
        ValueError: セクション数、長さ、path の不整合。
    """
    sections = cable_dto.sections.get_all()
    if len(sections) != 1:
        raise ValueError(
            "Parameter fit expects exactly one cable section "
            f"when applying descriptors, got {len(sections)}."
        )
    section = sections[0]
    new_series = section.series
    new_conductor = cable_dto.conductor_model
    n = len(descriptors)
    if len(x) != n:
        raise ValueError(
            f"x の長さ {len(x)} が descriptors の長さ {n} と一致しません。"
        )
    for idx, desc in enumerate(descriptors):
        if desc.path[0] != "cable":
            raise ValueError(
                f"ケーブル記述子以外が混在しています: path={desc.path}"
            )
        val = float(x[idx])
        val = max(desc.lb, min(desc.ub, val))
        if len(desc.path) == 2:
            new_series = apply_cable_path(new_series, desc.path, val, desc.unit)
            continue
        if (
            len(desc.path) == 4
            and desc.path[1] == "conductor_model"
            and desc.path[2] == "params"
        ):
            param_name = desc.path[3]
            if new_conductor.params is None:
                raise ValueError(
                    "conductor_model.params が None のため記述子を反映できません: "
                    f"path={desc.path}"
                )
            new_params = replace_param_in_dtos(
                new_conductor.params,
                param_name,
                val,
            )
            new_conductor = replace(new_conductor, params=new_params)
            continue
        raise ValueError(f"Unsupported cable descriptor path: {desc.path}")
    new_section = replace(section, series=new_series)
    new_sections = CableSectionDtos(objects=[new_section])
    return replace(
        cable_dto,
        sections=new_sections,
        conductor_model=new_conductor,
    )


def apply_im_path(  # noqa: PLR0911, PLR0912, PLR0915
    im: ImSeriesDto,
    path: tuple[str, ...],
    value: float,
    unit: str | None,
) -> ImSeriesDto:
    """path に従い ImSeriesDto を更新したコピーを返す。

    Args:
        im: 更新対象の IM シリーズ DTO。
        path: ``("im", ...)`` 形式の記述子パス。
        value: 反映する値。
        unit: 値の単位（None なら既定単位）。

    Returns:
        path に対応するフィールドを更新した ImSeriesDto。

    Raises:
        ValueError: path が未対応、または対応モデルの params が None の場合。
    """
    if len(path) == 2 and path[1] in (
        "primary_resistance",
        "primary_inductance",
        "excitation_resistance",
        "excitation_inductance",
    ):
        key = path[1]
        if key == "primary_resistance":
            return replace(
                im,
                primary_resistance=FloatResistanceDto(
                    value=value, unit=unit or "Ω"
                ),
            )
        if key == "primary_inductance":
            return replace(
                im,
                primary_inductance=FloatInductanceDto(
                    value=value, unit=unit or "H"
                ),
            )
        if key == "excitation_resistance":
            return replace(
                im,
                excitation_resistance=FloatResistanceDto(
                    value=value, unit=unit or "Ω"
                ),
            )
        return replace(
            im,
            excitation_inductance=FloatInductanceDto(
                value=value, unit=unit or "H"
            ),
        )

    if len(path) == 3 and path[1] == "secondary_resistance":
        branch = ImSecondaryCageBranchType(path[2])
        new_r = dict(im.secondary_resistances)
        new_r[branch] = FloatResistanceDto(value=value, unit=unit or "Ω")
        return replace(im, secondary_resistances=new_r)

    if len(path) == 3 and path[1] == "secondary_inductance":
        branch = ImSecondaryCageBranchType(path[2])
        new_xmap = dict(im.secondary_inductances)
        new_xmap[branch] = FloatInductanceDto(value=value, unit=unit or "H")
        return replace(im, secondary_inductances=new_xmap)

    if len(path) == 5 and path[1] == "secondary_model" and path[3] == "params":
        branch = ImSecondaryCageBranchType(path[2])
        param_name = path[4]
        model = im.secondary_models[branch]
        if model.params is None:
            raise ValueError(
                f"secondary_model.params が None のため反映できません: path={path}"
            )
        new_params = replace_param_in_dtos(model.params, param_name, value)
        new_model = replace(model, params=new_params)
        new_secondary_models = dict(im.secondary_models)
        new_secondary_models[branch] = new_model
        return replace(im, secondary_models=new_secondary_models)

    if (
        len(path) == 4
        and path[1] in ("primary_model", "excitation_model")
        and path[2] == "params"
    ):
        param_name = path[3]
        if path[1] == "primary_model":
            primary_model = im.primary_model
            if primary_model.params is None:
                raise ValueError(
                    f"primary_model.params が None のため反映できません: path={path}"
                )
            new_params = replace_param_in_dtos(
                primary_model.params,
                param_name,
                value,
            )
            new_primary_model = replace(primary_model, params=new_params)
            return replace(im, primary_model=new_primary_model)
        excitation_model = im.excitation_model
        if excitation_model.params is None:
            raise ValueError(
                f"excitation_model.params が None のため反映できません: path={path}"
            )
        new_params = replace_param_in_dtos(
            excitation_model.params,
            param_name,
            value,
        )
        new_excitation_model = replace(excitation_model, params=new_params)
        return replace(im, excitation_model=new_excitation_model)

    raise ValueError(f"未対応の IM 記述子 path です: {path}")


def replace_param_in_dtos(
    params: FloatParamDtos, param_name: str, value: float
) -> FloatParamDtos:
    """指定名の FloatParamDto のみ value を差し替えた FloatParamDtos を返す。

    Args:
        params: 差し替え対象のパラメータ集合。
        param_name: 差し替えるパラメータ名。
        value: 反映する値。

    Returns:
        指定名のみ value を更新した FloatParamDtos。

    Raises:
        ValueError: param_name が params に存在しない場合
            （記述子と DTO の不整合を黙って無視しないため）。
    """
    new_list: list[FloatParamDto] = []
    replaced = False
    for param in params.get_all():
        if param.name == param_name:
            new_list.append(FloatParamDto(name=param.name, value=value))
            replaced = True
        else:
            new_list.append(param)
    if not replaced:
        raise ValueError(f"パラメータ {param_name} が params に存在しません。")
    return FloatParamDtos(objects=new_list)


def apply_cable_path(
    cable: CableSeriesDto,
    path: tuple[str, ...],
    value: float,
    unit: str | None,
) -> CableSeriesDto:
    """path に従い CableSeriesDto の 1 フィールドを更新したコピーを返す。

    Args:
        cable: 更新対象のケーブルシリーズ DTO。
        path: ``("cable", <field>)`` 形式の記述子パス。
        value: 反映する値。
        unit: 値の単位（None なら既定単位）。

    Returns:
        path に対応するフィールドを更新した CableSeriesDto。

    Raises:
        ValueError: path 長が 2 以外、または未対応のフィールド名の場合。
    """
    if len(path) != 2:
        raise ValueError(f"未対応のケーブル記述子 path です: {path}")
    key = path[1]
    if key == "conductor_resistance_per_length":
        return replace(
            cable,
            conductor_resistance_per_length=FloatResistancePerLengthDto(
                value=value, unit=unit or "Ω/m"
            ),
        )
    if key == "conductor_inductance_per_length":
        return replace(
            cable,
            conductor_inductance_per_length=FloatInductancePerLengthDto(
                value=value, unit=unit or "H/m"
            ),
        )
    if key == "ground_resistance_length":
        return replace(
            cable,
            ground_resistance_length=FloatResistanceLengthDto(
                value=value, unit=unit or "Ω*m"
            ),
        )
    if key == "ground_capacitance_per_length":
        return replace(
            cable,
            ground_capacitance_per_length=FloatCapacitancePerLengthDto(
                value=value, unit=unit or "F/m"
            ),
        )
    raise ValueError(f"未対応のケーブル記述子フィールドです: {key}")
