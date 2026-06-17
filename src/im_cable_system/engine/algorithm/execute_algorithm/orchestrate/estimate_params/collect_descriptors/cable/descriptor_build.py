"""ケーブルフィット記述子の組み立て（estimate_params 専用）。

:class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.CableDto`
単位の π 型 4 パラメータ＋導体モデル係数を提供する。
ケーブルは **セクション 1 本** 前提（推定オーケストレーターと同一）。
探索上下限は
:class:`~im_cable_system.engine.shared.estimate_params_fit_spec.CableParameterFitDescriptorBounds`
（config 経由）を参照する。
記述子の DTO への適用は :mod:`apply_fitted_input.descriptor_apply` を参照。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
)


def collect_cable_fittable_descriptors(
    cable_dto: CableDto,
    cable_bounds: CableParameterFitDescriptorBounds,
) -> list[FittableParamDescriptor]:
    """ケーブル（1 セクション）のフィット対象記述子を返す。

    π 型シリーズ 4 スカラに加え、導体モデルで必須パラメータがある場合は
    ``("cable", "conductor_model", "params", name)``
    形式の記述子を付与する。

    Args:
        cable_dto: ケーブル DTO。セクションはちょうど 1 件であること。
        cable_bounds: 探索上下限。

    Returns:
        フィット記述子のリスト（先頭 4 件は π 型、続けて導体モデル係数）。

    Raises:
        ValueError: セクション数が 1 以外、またはシリーズ未埋め込みのとき。
    """
    sections = cable_dto.sections.get_all()
    if len(sections) != 1:
        raise ValueError(
            "Parameter fit expects exactly one cable section, "
            f"got {len(sections)}."
        )
    cable_series_dto = sections[0].series
    if cable_series_dto is None:
        raise ValueError(
            "CableSeriesDto is not embedded in cable_dto.sections[0]. "
            "Please set CableSectionDto.series."
        )
    cr_lb, cr_ub = cable_bounds.cable_fixed("conductor_resistance_per_length")
    cl_lb, cl_ub = cable_bounds.cable_fixed("conductor_inductance_per_length")
    gr_lb, gr_ub = cable_bounds.cable_fixed("ground_resistance_length")
    gc_lb, gc_ub = cable_bounds.cable_fixed("ground_capacitance_per_length")
    descriptors: list[FittableParamDescriptor] = [
        FittableParamDescriptor(
            path=("cable", "conductor_resistance_per_length"),
            current_value=(
                cable_series_dto.conductor_resistance_per_length.get_value()
            ),
            lb=cr_lb,
            ub=cr_ub,
            unit=cable_series_dto.conductor_resistance_per_length.get_unit(),
        ),
        FittableParamDescriptor(
            path=("cable", "conductor_inductance_per_length"),
            current_value=(
                cable_series_dto.conductor_inductance_per_length.get_value()
            ),
            lb=cl_lb,
            ub=cl_ub,
            unit=cable_series_dto.conductor_inductance_per_length.get_unit(),
        ),
        FittableParamDescriptor(
            path=("cable", "ground_resistance_length"),
            current_value=cable_series_dto.ground_resistance_length.get_value(),
            lb=gr_lb,
            ub=gr_ub,
            unit=cable_series_dto.ground_resistance_length.get_unit(),
        ),
        FittableParamDescriptor(
            path=("cable", "ground_capacitance_per_length"),
            current_value=(
                cable_series_dto.ground_capacitance_per_length.get_value()
            ),
            lb=gc_lb,
            ub=gc_ub,
            unit=cable_series_dto.ground_capacitance_per_length.get_unit(),
        ),
    ]
    conductor = cable_dto.conductor_model
    for param_name in conductor.get_required_parameter_names():
        if conductor.params is None:
            break
        param = conductor.params.get_by_name(param_name)
        if param is None:
            continue
        plb, pub = cable_bounds.conductor_model_param(
            conductor.name,
            param_name,
        )
        descriptors.append(
            FittableParamDescriptor(
                path=("cable", "conductor_model", "params", param_name),
                current_value=param.get_value(),
                lb=plb,
                ub=pub,
                unit=None,
            )
        )
    return descriptors
