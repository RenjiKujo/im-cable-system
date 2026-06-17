"""``ArrayLayoutDto`` の経路非依存チェック（Forward / EstimateParams 共通）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def check_line_voltage_real_constraints(input_dto: InputDto) -> None:
    """線間電圧が実数入力であることを検証する（Forward / EstimateParams 共通）。

    DTO 側との責務分担:
        ``ArrayComplexVoltageDto.__post_init__`` は配列が複素 numpy 配列
        であること・空でないこと・全要素 finite であることを保証する
        （実部の符号や虚部の値は問わない）。
        ``slip`` / ``frequency`` 軸の finite チェックや ``frequency > 0``
        チェックも、それぞれ ``ArraySlipDto`` / ``ArrayFrequencyDto`` の
        ``__post_init__`` 側で保証されるので本関数では扱わない。
        本関数では、Forward / EstimateParams いずれの実行モードでも
        線間電圧を実数として扱う前提なので、その契約として
        **実部 ``>= 0`` かつ虚部 ``== 0``** を追加で要求する。
        SI 基本単位 ``V`` への正規化可能性は
        ``si_execute_input_contract.validate_array_layout_reference_axes_si_base_or_raise``
        が担当する。

    Args:
        input_dto: 検証対象 InputDto。

    Raises:
        ValueError: 線間電圧の実部が負、または虚部が非ゼロの場合。
    """
    arrays = input_dto.array_layout.arrays
    volt = np.asarray(
        arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_value(),
        dtype=np.complex128,
    )
    if np.any(np.real(volt) < 0.0):
        raise ValueError(
            "array_layout.arrays['input_line_voltage'] の"
            "実部に負の要素があります。"
        )
    if np.any(np.abs(np.imag(volt)) > 0.0):
        raise ValueError(
            "array_layout.arrays['input_line_voltage'] の"
            "虚部がゼロでありません。"
        )
