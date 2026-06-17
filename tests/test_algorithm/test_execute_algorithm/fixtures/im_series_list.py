"""テスト用 ImSeriesDto リストの参照ヘルパー。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSeriesDto,
    ImSeriesName,  # noqa: E501
)


def get_im_series_by_name(
    series_list: list[ImSeriesDto],
    series_name: str | ImSeriesName,
) -> ImSeriesDto:
    """シリーズ名で ImSeriesDto を取得する。

    Args:
        series_list: 検索対象の ImSeriesDto リスト。
        series_name: シリーズ名（文字列または ImSeriesName）。

    Returns:
        ImSeriesDto: 一致する DTO。

    Raises:
        ValueError: 一致する DTO がない場合。
    """
    if isinstance(series_name, str):
        key = series_name
    else:
        key = series_name.get_value()
    for dto in series_list:
        if dto.name.get_value() == key or dto.name == key:
            return dto
    raise ValueError(f"ImSeriesDto not found for {key!r}")
