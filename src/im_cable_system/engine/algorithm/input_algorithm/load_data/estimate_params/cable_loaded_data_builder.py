"""1 直積要素から ``CableLoadedData`` を構築する。

ケーブル長 0 / ``combo.cable_conductor`` が ``None`` のときは ``None`` を
返す（=ケーブル無しシステム）。それ以外は :class:`CableParameterFitDescriptorBounds`
の bounds + init 仕様で 1 区間ケーブルを初期化する。

単位は :class:`CableParameterFitDescriptorBounds` の YAML 規約に準拠する SI
基本単位（Ω/m / H/m / Ω·m / F/m）で固定する。

値レベルの妥当性（正値・有限性、単位文字列の妥当性、配列長一致など）は
本層では検証せず、DTO ``__post_init__`` と ``_validate_input_dto`` に
寄せる（:class:`...load_data.i_data_loader.IInputDataLoader` の契約に従う）。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
    CableSectionLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.bounds_initializer import (  # noqa: E501
    cable_fixed_initial,
    conductor_model_param_initials,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    EstimateParamsModelCombo,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
)

_LEN_RES_UNIT = "Ω/m"
_LEN_IND_UNIT = "H/m"
_RES_LEN_UNIT = "Ω*m"
_LEN_CAP_UNIT = "F/m"
_CABLE_SHAPE_TYPE = "ROUND"


def _build_cable_section(
    *,
    section_name: str,
    cable_length: float,
    cable_length_unit: str,
    bounds: CableParameterFitDescriptorBounds,
) -> CableSectionLoadedData:
    return CableSectionLoadedData(
        name=section_name,
        length=cable_length,
        shape_type=_CABLE_SHAPE_TYPE,
        length_unit=cable_length_unit,
        conductor_resistance_per_length=cable_fixed_initial(
            "conductor_resistance_per_length",
            bounds,
        ),
        conductor_resistance_per_length_unit=_LEN_RES_UNIT,
        conductor_inductance_per_length=cable_fixed_initial(
            "conductor_inductance_per_length",
            bounds,
        ),
        conductor_inductance_per_length_unit=_LEN_IND_UNIT,
        ground_resistance_length=cable_fixed_initial(
            "ground_resistance_length",
            bounds,
        ),
        ground_resistance_length_unit=_RES_LEN_UNIT,
        ground_capacitance_per_length=cable_fixed_initial(
            "ground_capacitance_per_length",
            bounds,
        ),
        ground_capacitance_per_length_unit=_LEN_CAP_UNIT,
    )


def build_cable_loaded_data(
    *,
    combo: EstimateParamsModelCombo,
    cable_length: float,
    cable_length_unit: str,
    bounds: CableParameterFitDescriptorBounds,
    cable_name: str,
    section_name: str,
) -> CableLoadedData | None:
    """1 区間ケーブルの中間表現を構築する（ケーブル無しのときは ``None``）。

    Args:
        combo: 1 直積要素（候補モデル種別の組み合わせ）。
        cable_length: ケーブル長（:func:`resolve_cable_length` の戻り値）。
            ``<=0`` のときケーブル無し扱い。
        cable_length_unit: ケーブル長の単位文字列。
        bounds: ケーブル探索境界。導体物性は bounds + init 仕様で初期化する。
        cable_name: ``CableLoadedData.name``。
        section_name: ``CableSectionLoadedData.name``。

    Returns:
        CableLoadedData | None: ケーブル無しシステムのとき ``None``、それ
        以外は 1 区間ケーブルの中間表現。
    """
    if cable_length <= 0.0 or combo.cable_conductor is None:
        return None

    section = _build_cable_section(
        section_name=section_name,
        cable_length=cable_length,
        cable_length_unit=cable_length_unit,
        bounds=bounds,
    )
    conductor_params = conductor_model_param_initials(
        combo.cable_conductor,
        bounds,
    )
    conductor_params_or_none: dict[str, float] | None = (
        conductor_params if conductor_params else None
    )
    return CableLoadedData(
        name=cable_name,
        sections=(section,),
        conductor_model=combo.cable_conductor.value,
        conductor_model_params=conductor_params_or_none,
    )
