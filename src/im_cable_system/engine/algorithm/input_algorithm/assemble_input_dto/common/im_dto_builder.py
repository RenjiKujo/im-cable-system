"""ImLoadedData から ImSeriesDto / ImDto を構築する（Forward / EstimateParams 共通）。"""

from __future__ import annotations

from enum import Enum
from typing import TypeVar

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.model_params_builder import (  # noqa: E501
    float_param_dtos_from_dict,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImBranchLoadedData,
    ImLoadedData,
    ImLossBranchLoadedData,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImDto,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImPoles,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
    ImSeriesDto,
    ImSeriesName,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)

_EnumT = TypeVar("_EnumT", bound=Enum)


def _format_enum_members(enum_cls: type[Enum]) -> str:
    """Enum の値一覧を ``a, b, c`` 形式で返す（エラーメッセージ用）。"""
    return ", ".join(sorted(str(member.value) for member in enum_cls))


def _poles_from_int(raw: int, *, im_name: str) -> ImPoles:
    """整数の極数を :class:`ImPoles` に変換する。失敗時は文脈付き ``ValueError``。"""
    for member in ImPoles:
        if int(member.value) == raw:
            return member
    allowed = ", ".join(sorted(str(int(member.value)) for member in ImPoles))
    raise ValueError(
        f"IM シリーズ {im_name!r} の極数 {raw!r} はサポート外です。"
        f" 取り得る値: {allowed}"
    )


def _cage_multiplicity_from_str(
    raw: str, *, im_name: str
) -> ImCageMultiplicityType:
    """``cage_multiplicity`` 文字列を Enum に変換する。

    空文字列は :class:`ImCageMultiplicityType.SINGLE_CAGE` 既定。
    それ以外でメンバ名・値のどちらにも一致しない場合は文脈付き ``ValueError``。
    """
    key = raw.strip()
    if key == "":
        return ImCageMultiplicityType.SINGLE_CAGE
    for member in ImCageMultiplicityType:
        if key in (member.name, member.value):
            return member
    raise ValueError(
        f"IM シリーズ {im_name!r} の cage_multiplicity {raw!r} は"
        f"サポート外です。 取り得る値: "
        f"{_format_enum_members(ImCageMultiplicityType)}"
    )


def _resolve_enum(
    enum_cls: type[_EnumT],
    raw: str,
    *,
    im_name: str,
    field_label: str,
) -> _EnumT:
    """``raw`` を IM シリーズ DTO の Enum 属性に変換する。

    モデル名以外の Enum 属性（``connection_type`` / ``circuit_type`` など）
    の汎用変換ヘルパー。失敗時は文脈付き ``ValueError`` を投げる。

    Args:
        enum_cls: 変換先 Enum クラス。
        raw: カタログ YAML 由来の文字列。
        im_name: IM シリーズ名（エラーメッセージ用）。
        field_label: 属性ラベル（"connection_type" / "circuit_type" など）。

    Returns:
        ``enum_cls`` の対応メンバ。

    Raises:
        ValueError: ``raw`` が ``enum_cls`` に存在しない場合。
    """
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の {field_label} {raw!r} は"
            f"サポート外です。 取り得る値: {_format_enum_members(enum_cls)}"
        ) from exc


def _resolve_im_model_type(
    enum_cls: type[_EnumT],
    raw: str,
    *,
    im_name: str,
    branch_label: str,
    role: str,
) -> _EnumT:
    """``raw`` を IM モデル enum に変換する。失敗時は文脈付き ``ValueError``。

    Args:
        enum_cls: 変換先 Enum クラス。
        raw: カタログ YAML 由来のモデル名文字列。
        im_name: IM シリーズ名（エラーメッセージ用）。
        branch_label: ブランチ識別子（"primary" / "excitation" / "secondary" /
            "secondary_inner" / "secondary_outer"）。
        role: モデル役割の日本語表現（"一次" / "励磁" / "二次"）。

    Returns:
        ``enum_cls`` の対応メンバ。

    Raises:
        ValueError: ``raw`` が ``enum_cls`` に存在しない場合。
    """
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の {branch_label} に指定された"
            f"{role}モデル名 {raw!r} はサポート外です。"
            f" 取り得る値: {_format_enum_members(enum_cls)}"
        ) from exc


def _primary_model_dto(
    branch: ImBranchLoadedData,
    *,
    im_name: str,
) -> ImPrimaryModelDto:
    model_type = _resolve_im_model_type(
        ImPrimaryModelType,
        branch.model,
        im_name=im_name,
        branch_label="primary",
        role="一次",
    )
    try:
        return ImPrimaryModelDto(
            name=model_type,
            params=float_param_dtos_from_dict(branch.model_params),
        )
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の primary モデル係数が不正です: {exc}"
        ) from exc


def _excitation_model_dto(
    branch: ImBranchLoadedData,
    *,
    im_name: str,
) -> ImExcitationModelDto:
    model_type = _resolve_im_model_type(
        ImExcitationModelType,
        branch.model,
        im_name=im_name,
        branch_label="excitation",
        role="励磁",
    )
    try:
        return ImExcitationModelDto(
            name=model_type,
            params=float_param_dtos_from_dict(branch.model_params),
        )
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の excitation モデル係数が不正です: {exc}"
        ) from exc


def _secondary_model_dto(
    branch: ImBranchLoadedData,
    *,
    im_name: str,
    branch_label: str,
) -> ImSecondaryModelDto:
    model_type = _resolve_im_model_type(
        ImSecondaryModelType,
        branch.model,
        im_name=im_name,
        branch_label=branch_label,
        role="二次",
    )
    try:
        return ImSecondaryModelDto(
            name=model_type,
            params=float_param_dtos_from_dict(branch.model_params),
        )
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の {branch_label} モデル係数が"
            f"不正です: {exc}"
        ) from exc


def _friction_windage_model_dto(
    branch: ImLossBranchLoadedData,
    *,
    im_name: str,
) -> ImFrictionWindageModelDto:
    model_type = _resolve_im_model_type(
        ImFrictionWindageModelType,
        branch.model,
        im_name=im_name,
        branch_label="friction_windage",
        role="摩擦・風損",
    )
    try:
        return ImFrictionWindageModelDto(
            name=model_type,
            params=float_param_dtos_from_dict(branch.model_params),
        )
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の friction_windage モデル係数が"
            f"不正です: {exc}"
        ) from exc


def _stray_load_model_dto(
    branch: ImLossBranchLoadedData,
    *,
    im_name: str,
) -> ImStrayLoadModelDto:
    model_type = _resolve_im_model_type(
        ImStrayLoadModelType,
        branch.model,
        im_name=im_name,
        branch_label="stray_load",
        role="漂遊負荷損",
    )
    try:
        return ImStrayLoadModelDto(
            name=model_type,
            params=float_param_dtos_from_dict(branch.model_params),
        )
    except ValueError as exc:
        raise ValueError(
            f"IM シリーズ {im_name!r} の stray_load モデル係数が不正です: {exc}"
        ) from exc


def build_im_series_dto(im_loaded: ImLoadedData) -> ImSeriesDto:
    """IM 中間表現から :class:`ImSeriesDto` を構築する。

    Args:
        im_loaded: ロード済み IM 中間表現。

    Returns:
        ImSeriesDto: シリーズ DTO。

    Raises:
        ValueError: スキーマ・enum が不正な場合。
    """
    np_data = im_loaded.nameplate
    im_name = im_loaded.name
    cage_multiplicity = _cage_multiplicity_from_str(
        im_loaded.cage_multiplicity, im_name=im_name
    )

    primary_model = _primary_model_dto(im_loaded.primary, im_name=im_name)
    excitation_model = _excitation_model_dto(
        im_loaded.excitation, im_name=im_name
    )
    friction_windage_model = _friction_windage_model_dto(
        im_loaded.friction_windage, im_name=im_name
    )
    stray_load_model = _stray_load_model_dto(
        im_loaded.stray_load, im_name=im_name
    )

    secondary_models: dict[ImSecondaryCageBranchType, ImSecondaryModelDto] = {}
    secondary_resistances: dict[
        ImSecondaryCageBranchType, FloatResistanceDto
    ] = {}
    secondary_inductances: dict[
        ImSecondaryCageBranchType, FloatInductanceDto
    ] = {}

    if cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE:
        if (
            im_loaded.secondary_inner is None
            or im_loaded.secondary_outer is None
        ):
            raise ValueError(
                f"二重かごシリーズ '{im_name}' には "
                "secondary_inner / secondary_outer が必要です。"
            )
        inner_b = ImSecondaryCageBranchType.INNER
        outer_b = ImSecondaryCageBranchType.OUTER
        for branch_type, branch, branch_label in (
            (inner_b, im_loaded.secondary_inner, "secondary_inner"),
            (outer_b, im_loaded.secondary_outer, "secondary_outer"),
        ):
            secondary_models[branch_type] = _secondary_model_dto(
                branch, im_name=im_name, branch_label=branch_label
            )
            secondary_resistances[branch_type] = FloatResistanceDto(
                value=branch.resistance,
                unit=branch.resistance_unit,
            )
            secondary_inductances[branch_type] = FloatInductanceDto(
                value=branch.inductance,
                unit=branch.inductance_unit,
            )
    else:
        if im_loaded.secondary is None:
            raise ValueError(
                f"単一かごシリーズ '{im_name}' には secondary が必要です。"
            )
        branch_key = ImSecondaryCageBranchType.SINGLE
        sec = im_loaded.secondary
        secondary_models[branch_key] = _secondary_model_dto(
            sec, im_name=im_name, branch_label="secondary"
        )
        secondary_resistances[branch_key] = FloatResistanceDto(
            value=sec.resistance,
            unit=sec.resistance_unit,
        )
        secondary_inductances[branch_key] = FloatInductanceDto(
            value=sec.inductance,
            unit=sec.inductance_unit,
        )

    return ImSeriesDto(
        name=ImSeriesName.create(value=im_loaded.name),
        poles=_poles_from_int(im_loaded.poles, im_name=im_name),
        nameplate_voltage=FloatVoltageDto(
            value=np_data.voltage,
            unit=np_data.voltage_unit,
        ),
        nameplate_current=FloatCurrentDto(
            value=np_data.current,
            unit=np_data.current_unit,
        ),
        nameplate_power=FloatActivePowerDto(
            value=np_data.power,
            unit=np_data.power_unit,
        ),
        nameplate_frequency=FloatFrequencyDto(
            value=np_data.frequency,
            unit=np_data.frequency_unit,
        ),
        connection_type=_resolve_enum(
            ImConnectionType,
            im_loaded.connection_type,
            im_name=im_name,
            field_label="connection_type",
        ),
        circuit_type=_resolve_enum(
            ImCircuitType,
            im_loaded.circuit_type,
            im_name=im_name,
            field_label="circuit_type",
        ),
        primary_model=primary_model,
        primary_resistance=FloatResistanceDto(
            value=im_loaded.primary.resistance,
            unit=im_loaded.primary.resistance_unit,
        ),
        primary_inductance=FloatInductanceDto(
            value=im_loaded.primary.inductance,
            unit=im_loaded.primary.inductance_unit,
        ),
        excitation_model=excitation_model,
        excitation_resistance=FloatResistanceDto(
            value=im_loaded.excitation.resistance,
            unit=im_loaded.excitation.resistance_unit,
        ),
        excitation_inductance=FloatInductanceDto(
            value=im_loaded.excitation.inductance,
            unit=im_loaded.excitation.inductance_unit,
        ),
        cage_multiplicity=cage_multiplicity,
        secondary_models=secondary_models,
        secondary_resistances=secondary_resistances,
        secondary_inductances=secondary_inductances,
        friction_windage_model=friction_windage_model,
        stray_load_model=stray_load_model,
    )


def build_im_dto(im_loaded: ImLoadedData) -> ImDto:
    """IM 中間表現から :class:`ImDto` を構築する。

    ``ImDto.name`` は指定せず、:class:`ImDto` のデフォルト ``SINGLE`` を
    そのまま採用する。Input アルゴリズムは単機構成のみを対象とするため。
    """
    return ImDto(im_series=build_im_series_dto(im_loaded))
