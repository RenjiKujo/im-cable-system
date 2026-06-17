"""CableLoadedData から CableDto を構築する（Forward / EstimateParams 共通）。

ケーブル長単位（``section.length_unit``）はシリーズ選択 TSV 由来で、
LoadData 段では ``strip()`` のみで保持されている（``axes_parser`` /
``performance_curve_parser`` と同じ責務分担）。本モジュールでは、
``FloatLengthDto`` に渡す前に角括弧 ``[...]`` 表記を剥がす正規化を
:func:`normalize_loaded_unit_cell`（``assemble_input_dto.common``
配下の共通ヘルパー）を通じて行う。単位値域の妥当性
（``ft`` / ``m`` 等の許容単位かどうか）は ``FloatLengthDto.__post_init__``
が担う。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.model_params_builder import (  # noqa: E501
    float_param_dtos_from_dict,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.unit_normalizer import (  # noqa: E501
    normalize_loaded_unit_cell,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
    CableSectionLoadedData,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    CableDto,
    CableName,
    CableSectionDto,
    CableSectionDtos,
    CableSectionName,
    CableSeriesDto,
    CableSeriesName,
    CableShapeTypeDto,
    ConductorModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


def _section_dto(
    section: CableSectionLoadedData, section_index: int
) -> CableSectionDto:
    series_dto = CableSeriesDto(
        name=CableSeriesName(value=section.name),
        shape_type=CableShapeTypeDto(value=section.shape_type),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=section.conductor_resistance_per_length,
            unit=section.conductor_resistance_per_length_unit,
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=section.conductor_inductance_per_length,
            unit=section.conductor_inductance_per_length_unit,
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=section.ground_resistance_length,
            unit=section.ground_resistance_length_unit,
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=section.ground_capacitance_per_length,
            unit=section.ground_capacitance_per_length_unit,
        ),
    )
    return CableSectionDto(
        name=CableSectionName(value=f"SECTION_{section_index}"),
        length=FloatLengthDto(
            value=section.length,
            unit=normalize_loaded_unit_cell(section.length_unit),
        ),
        series=series_dto,
    )


def _format_conductor_enum_members() -> str:
    """`ConductorModelType` の値一覧を ``a, b, c`` 形式で返す（エラー文面用）。"""
    return ", ".join(sorted(str(member.value) for member in ConductorModelType))


def _conductor_model_dto(
    cable_loaded: CableLoadedData,
) -> CableConductorModelDto:
    """導体モデル DTO を構築する。enum / 係数の不正は文脈付き ``ValueError``。"""
    try:
        model_type = ConductorModelType(cable_loaded.conductor_model)
    except ValueError as exc:
        raise ValueError(
            f"Cable {cable_loaded.name!r} の conductor_model 名 "
            f"{cable_loaded.conductor_model!r} はサポート外です。"
            f" 取り得る値: {_format_conductor_enum_members()}"
        ) from exc
    try:
        return CableConductorModelDto(
            name=model_type,
            params=float_param_dtos_from_dict(
                cable_loaded.conductor_model_params
            ),
        )
    except ValueError as exc:
        raise ValueError(
            f"Cable {cable_loaded.name!r} の conductor_model 係数が"
            f"不正です: {exc}"
        ) from exc


def build_cable_dto(cable_loaded: CableLoadedData) -> CableDto:
    """ケーブル中間表現から :class:`CableDto` を構築する。

    Args:
        cable_loaded: ロード済みケーブル中間表現。

    Returns:
        CableDto: ケーブル DTO。

    Raises:
        ValueError:
            - ``conductor_model`` が ``ConductorModelType`` の Enum 値にない。
            - ``conductor_model_params`` がモデル仕様（必須名集合・余分・
              重複・finite 値）を満たさない。
    """
    section_dtos = [
        _section_dto(section, idx)
        for idx, section in enumerate(cable_loaded.sections)
    ]
    conductor_model = _conductor_model_dto(cable_loaded)
    return CableDto(
        name=CableName(value=cable_loaded.name),
        sections=CableSectionDtos(objects=section_dtos),
        conductor_model=conductor_model,
    )
