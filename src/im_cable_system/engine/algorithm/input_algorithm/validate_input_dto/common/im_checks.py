"""IM 名板の経路非依存チェック（Forward / EstimateParams 共通）。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def _require_positive(value: float, path: str) -> None:
    if value <= 0.0:
        raise ValueError(f"{path} は正である必要があります。")


def check_im_values(input_dto: InputDto) -> None:
    """IM 名板値が正値であることを検証する（Forward / EstimateParams 共通）。

    DTO 側との責務分担:
        ``FloatVoltageDto`` / ``FloatCurrentDto`` / ``FloatActivePowerDto``
        は ``__post_init__`` で finite かつ ``>= 0`` を保証する
        （``0`` は通る）。``FloatFrequencyDto`` は ``> 0`` まで保証する。
        本関数では、Forward / EstimateParams いずれの実行モードでも
        名板値 ``0`` を許さないという契約として ``nameplate_voltage`` /
        ``nameplate_current`` / ``nameplate_power`` の ``> 0`` を追加で
        要求する。``nameplate_frequency`` の ``> 0`` チェックは DTO と
        重複するが、名板 4 項目を同じ ``> 0`` 契約で揃える方が読みやすい
        ので、意図的に明示している。

    Args:
        input_dto: 検証対象 InputDto。

    Raises:
        ValueError: 名板値が 0 以下の場合。
    """
    _check_im_series_values(input_dto.im)


def _check_im_series_values(im: ImDto) -> None:
    series = im.im_series
    prefix = "im.im_series"
    _require_positive(
        float(series.nameplate_voltage.get_value()),
        f"{prefix}.nameplate_voltage",
    )
    _require_positive(
        float(series.nameplate_current.get_value()),
        f"{prefix}.nameplate_current",
    )
    _require_positive(
        float(series.nameplate_power.get_value()),
        f"{prefix}.nameplate_power",
    )
    _require_positive(
        float(series.nameplate_frequency.get_value()),
        f"{prefix}.nameplate_frequency",
    )
