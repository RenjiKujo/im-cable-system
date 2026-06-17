"""ItmDtos ダンプ機能（ExecuteStage 内部の共通処理）。

各 ExecuteStage が結果 ItmDtos を設定に応じて pickle ダンプするための
共通関数を提供する。
"""

from im_cable_system.engine.processor.execute_stage.dump_itm_dto.itm_dtos_dumper import (  # noqa: E501
    dump_itm_dtos_if_enabled,
)

__all__ = ["dump_itm_dtos_if_enabled"]
