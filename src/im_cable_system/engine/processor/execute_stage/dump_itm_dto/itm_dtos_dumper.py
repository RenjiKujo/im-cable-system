"""ItmDtos の pickle ダンプ共通関数（ExecuteStage 内部用）。

forward / estimate_params の各 ExecuteStage が共有して呼び出す。
設定（``dump_data_config.dtos.itm_dtos``）が有効なときだけ ItmDtos を
pickle ファイルに書き出す。状態を持たない処理のため関数として提供する。
"""

from __future__ import annotations

import pickle
from datetime import datetime
from zoneinfo import ZoneInfo

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import ItmDtos


def dump_itm_dtos_if_enabled(
    config: IConfig,
    logger: ILogger,
    dtos: ItmDtos,
) -> None:
    """設定が有効なときだけ ItmDtos を pickle ダンプする。

    ダンプはデバッグ・解析用の **副次処理** であり、本処理（forward /
    estimate_params の ExecuteStage）の成否には影響させない契約とする。
    そのため書き出しで例外が起きても呼び出し元へ送出せず、``Exception``
    のみを捕捉して warning ログに記録し、本処理は成功扱いのまま継続する。
    ディスクフル・権限不足など環境起因の失敗で計算結果を失わないための
    意図的な握り潰しであり、``BaseException`` や生 ``except`` は用いない。

    Args:
        config: 設定オブジェクト（ダンプ有効可否・出力先を参照）。
        logger: ロガーオブジェクト。
        dtos: ダンプ対象の ItmDtos。

    Returns:
        None: 戻り値はない（成功・失敗とも例外を送出しない）。
    """
    dump_block = config.dump_data_config.dtos.itm_dtos
    if not dump_block.enabled:
        return

    base_dir = config.get_dump_base_dir()

    tz_name = config.project_info.timezone
    timestamp = datetime.now(ZoneInfo(tz_name)).strftime("%Y%m%dT%H%M%S")
    filename = dump_block.filename_pattern.format(timestamp=timestamp)
    sub_dir = dump_block.sub_dir

    dump_path = (base_dir / sub_dir / filename).resolve()

    try:
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        with dump_path.open("wb") as file_handle:
            pickle.dump(dtos, file_handle, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("ItmDtos dumped to %s", dump_path)
    except Exception as exc:  # noqa: BLE001
        # NOTE: ダンプは副次処理。失敗しても本処理は成功扱いとする契約のため
        #       Exception 限定で握り、warning に留める（docstring 参照）。
        logger.warning(
            "Failed to dump ItmDtos to %s: %s",
            dump_path,
            exc,
        )
