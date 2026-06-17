"""OutputDtos ダンプ機能（OutputStage 内部の共通処理）。

各 OutputStage が結果 OutputDtos を設定に応じて pickle ダンプするための
共通関数を提供する。
"""

from im_cable_system.engine.processor.output_stage.dump_output_dto.output_dtos_dumper import (  # noqa: E501
    dump_output_dtos_if_enabled,
)

__all__ = ["dump_output_dtos_if_enabled"]
