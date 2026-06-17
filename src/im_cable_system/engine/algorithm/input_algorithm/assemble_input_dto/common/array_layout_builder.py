"""AxesLoadedData から ArrayLayoutDto を構築する（Forward / EstimateParams 共通）。

参照軸（``reference_axes``）の指定はモードによって異なる：

- Forward (CartesianGrid): ``[SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]``
  （3 軸とも独立な参照軸 → 評価点は直積）。
- Forward (OperatingPoints): ``[SLIP]``（``slip`` だけが参照軸で、
  ``frequency`` / ``input_line_voltage`` は非参照軸 → ``slip`` と同じ
  長さの 1 次元配列として保持し、運転点列を co-indexed で表現する）。
- EstimateParams: ``[SLIP, FREQUENCY, INPUT_LINE_VOLTAGE]``
  （性能曲線由来の slip 配列と、供給条件由来の周波数・線間電圧 1 点を
  3 軸として与える）。

本ビルダは ``reference_axes`` を **引数で受け取るだけ** で、モードに
依存しない。モード分岐は ``orchestrate`` 層が担う。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.unit_normalizer import (  # noqa: E501
    normalize_loaded_unit_cell,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.axes_loaded_data import (  # noqa: E501
    AxesLoadedData,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    ArrayFrequencyDto,
    ArraySlipDto,
)


def _normalize_slip_unit_cell(raw: str) -> str:
    """スリップ DTO が受け取れる単位文字列に変換する。

    外側角括弧の剥がしは :func:`normalize_loaded_unit_cell` に委ね、
    本関数は「``%`` / ``-`` 等の表記揺れを ``ArraySlipDto`` の許容単位に
    集約する」スリップ固有の責務だけを持つ。
    """
    normalized = normalize_loaded_unit_cell(raw)
    lowered = normalized.lower()
    if lowered in ("%", "percent", "pct"):
        return "%"
    if lowered in ("-", "1", "dimensionless", "nounit"):
        return "-"
    return normalized


def build_array_layout(
    axes: AxesLoadedData,
    reference_axes: list[ArrayKey],
) -> ArrayLayoutDto:
    """評価点軸の中間表現から :class:`ArrayLayoutDto` を構築する。

    Args:
        axes: ロード済み評価点軸。
        reference_axes: 参照軸として扱う ``ArrayKey`` の順序付きリスト。
            CartesianGrid なら 3 軸すべて、OperatingPoints なら ``SLIP``
            のみ、のように呼び出し側（orchestrate 層）が決定する。

    Returns:
        ArrayLayoutDto: 配列レイアウト DTO。
    """
    volt_complex = axes.input_line_voltage.astype(
        np.complex128,
        copy=False,
    )
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=axes.slip,
                unit=_normalize_slip_unit_cell(axes.slip_unit),
            ),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=axes.frequency,
                unit=normalize_loaded_unit_cell(axes.frequency_unit),
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=volt_complex,
                unit=normalize_loaded_unit_cell(axes.voltage_unit),
            ),
        },
        reference_axes=list(reference_axes),
    )
