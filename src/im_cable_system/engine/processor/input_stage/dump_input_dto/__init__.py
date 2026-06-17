"""InputDtos ダンプ機能（InputStage 内部の共通処理）。

各 InputStage が結果 InputDtos を設定に応じて pickle ダンプするための
共通関数を提供する。
"""

from im_cable_system.engine.processor.input_stage.dump_input_dto.input_dtos_dumper import (  # noqa: E501
    dump_input_dtos_if_enabled,
)

__all__ = ["dump_input_dtos_if_enabled"]
