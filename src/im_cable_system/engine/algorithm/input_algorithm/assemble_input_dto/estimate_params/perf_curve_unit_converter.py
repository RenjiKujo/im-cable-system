"""EstimateParams 統合 TSV の性能曲線比率列を絶対単位に変換するヘルパ。

EstimateParams では 1 つの統合 TSV に名盤情報と観測曲線が併載されるため、
``power`` 列は「名盤機械出力に対する比 ``[-]``」、``current`` 列は「名盤
電流に対する百分率 ``[%]``」で記録することが許容される。

一方、性能曲線 DTO ビルダー
（:mod:`...common.performance_curve_dto_builder`）は **絶対単位前提**
で設計されており、``power`` / ``torque`` / ``current`` 列の比率単位
``-`` / ``%`` を明示的に拒否する。

そのため EstimateParams 経路では、共通ビルダーに委譲する直前に本
ヘルパで ``ratio→absolute`` 変換を行う。

変換規則:
    - ``power[-]`` × ``nameplate.power[W]`` → ``power[W]``
    - ``current[%]`` × ``nameplate.current[A]`` / 100 → ``current[A]``
    - ``torque`` / ``power_factor`` / ``efficiency`` は単位を変えない。
    - 既に絶対単位（``W`` / ``A`` など）が指定されている列はスケーリング
      しない（単位文字列をそのまま伝搬し、許容単位かどうかは共通
      ビルダー側の DTO 検証に委ねる）。

名盤値の単位文字列は ``ACTIVE_POWER_FACTORS`` / ``CURRENT_FACTORS`` を
通じて SI 基本単位（``W`` / ``A``）に揃えてからスケーリング係数として用いる。

公開範囲:
    本モジュールは EstimateParams アセンブラ内部のヘルパであり、
    ``estimate_params`` 配下からの **層内 import 専用**。層外・層横断
    （pipeline / processor / 他の algorithm サブツリー）からは直接
    参照しない（``docs/rules/layering_and_imports.md`` の「非公開モジュールは
    docstring に理由を書く」ルールに従い、公開窓口
    ``assemble_input_dto/estimate_params/__init__.py`` の ``__all__``
    にも載せない）。
"""

from __future__ import annotations

import dataclasses

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.unit_normalizer import (  # noqa: E501
    normalize_loaded_unit_cell,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImNameplateLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ACTIVE_POWER_FACTORS,
    CURRENT_FACTORS,
)


def _nameplate_power_in_w(nameplate: ImNameplateLoadedData) -> float:
    """名盤機械出力を SI (W) に揃えて返す。"""
    unit = normalize_loaded_unit_cell(nameplate.power_unit)
    if unit not in ACTIVE_POWER_FACTORS:
        raise ValueError(
            f"EstimateParams 名盤 output_power の単位 "
            f"{nameplate.power_unit!r} はサポート外です "
            f"(allowed={list(ACTIVE_POWER_FACTORS.keys())!r})。"
        )
    return float(nameplate.power) * ACTIVE_POWER_FACTORS[unit]


def _nameplate_current_in_a(nameplate: ImNameplateLoadedData) -> float:
    """名盤電流を SI (A) に揃えて返す。"""
    unit = normalize_loaded_unit_cell(nameplate.current_unit)
    if unit not in CURRENT_FACTORS:
        raise ValueError(
            f"EstimateParams 名盤 input_line_current の単位 "
            f"{nameplate.current_unit!r} はサポート外です "
            f"(allowed={list(CURRENT_FACTORS.keys())!r})。"
        )
    return float(nameplate.current) * CURRENT_FACTORS[unit]


def convert_ratio_columns_to_absolute(
    pc: ImPerformanceCurveLoadedData,
    nameplate: ImNameplateLoadedData,
) -> ImPerformanceCurveLoadedData:
    """``power[-]`` / ``current[%]`` を絶対単位（W / A）に変換する。

    ``torque`` / ``power_factor`` / ``efficiency`` 列は変換せずそのまま
    伝搬する。``power`` / ``current`` 列が既に絶対単位だった場合も
    スケーリングは行わず、単位文字列をそのまま伝搬する（許容単位かどうかは
    共通ビルダー側の DTO 契約で判定される）。

    Args:
        pc: 統合 TSV 由来の性能曲線中間表現
            （比率単位を含み得る）。
        nameplate: 同じ統合 TSV 由来の名盤中間表現。

    Returns:
        絶対単位に揃え直した新しい :class:`ImPerformanceCurveLoadedData`。

    Raises:
        ValueError: 名盤の ``power_unit`` / ``current_unit`` が
            ``ACTIVE_POWER_FACTORS`` / ``CURRENT_FACTORS`` に登録されて
            いない場合。
    """
    new_power = pc.power
    new_power_unit = pc.power_unit
    if pc.power is not None and pc.power_unit is not None:
        normalized = normalize_loaded_unit_cell(pc.power_unit)
        if normalized == "-":
            ref_w = _nameplate_power_in_w(nameplate)
            new_power = np.asarray(pc.power, dtype=np.float64) * ref_w
            new_power_unit = "W"

    new_current = pc.current
    new_current_unit = pc.current_unit
    if pc.current is not None and pc.current_unit is not None:
        normalized = normalize_loaded_unit_cell(pc.current_unit)
        if normalized == "%":
            ref_a = _nameplate_current_in_a(nameplate)
            new_current = (
                np.asarray(pc.current, dtype=np.float64) / 100.0 * ref_a
            )
            new_current_unit = "A"

    return dataclasses.replace(
        pc,
        power=new_power,
        power_unit=new_power_unit,
        current=new_current,
        current_unit=new_current_unit,
    )
