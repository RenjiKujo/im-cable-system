"""ケーブルセクション長の数値チェック（Forward / EstimateParams 共通）。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def check_cable_section_lengths(input_dto: InputDto) -> None:
    """各ケーブルセクション長が正値であることを検証する（Forward / EstimateParams 共通）。

    DTO 側との責務分担:
        ``FloatLengthDto.__post_init__`` は finite かつ ``>= 0`` を保証する
        （``0`` は通る）。本関数では、Forward / EstimateParams いずれの
        実行モードでもセクション長 ``0`` を許さないという契約として
        ``length > 0`` を追加で要求する。
        SI 基本単位 ``m`` への正規化可能性は
        ``si_execute_input_contract.validate_cable_section_lengths_si_base_or_raise``
        が担当する。

    Args:
        input_dto: 検証対象 InputDto。

    Raises:
        ValueError: セクション長が 0 以下の場合。
    """
    cable = input_dto.cable
    if cable is None:
        return
    for idx, section in enumerate(cable.sections.get_all()):
        length_m = float(section.length.to_base_unit().get_value())
        path = f"cable.sections[{idx}].length"
        if length_m <= 0.0:
            raise ValueError(f"{path} は正である必要があります。")
