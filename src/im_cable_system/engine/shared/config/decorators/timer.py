"""処理時間計測デコレーター（:class:`ILogger` 用）。

例外時はメソッド名と経過時間のみを INFO で残し、エラーログ（および
スタックトレース）は最上位境界（Runner 等）で
``logger.exception(...)`` として 1 度だけ出力する方針。
@timer が層ごとに ERROR を出すと、同じ例外が層数分だけログに重複する
ためこの形に統一する。
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Literal

from im_cable_system.engine.shared.config.i_app_logger import ILogger


def timer(
    logger: ILogger | None = None,
    line: Literal["#", "=", "-", "*"] | None = None,
    min_duration: float = 0.0,
) -> Callable:
    """処理時間を計測し :class:`ILogger` に出力するデコレーター。

    Args:
        logger: ログ出力用の :class:`ILogger`。
            ``None`` のときは ``self._logger`` を使う。
        line: ログの区切り文字。
        min_duration: ログを出力する最小実行時間（秒）。既定は ``0.0``。

    Returns:
        Callable: デコレーター関数。
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            actual_logger = _resolve_logger(
                logger=logger,
                args=args,
            )
            lines = _format_line_prefix(line=line)

            start_time = time.time()
            if min_duration == 0.0:
                actual_logger.info(
                    f"{lines}[start] {func.__qualname__} {lines}",
                )

            try:
                result = func(*args, **kwargs)
                time_sec = time.time() - start_time
                time_min = time_sec / 60.0

                if time_sec >= min_duration:
                    if min_duration > 0.0:
                        actual_logger.info(
                            f"{lines}[start] {func.__qualname__} {lines}",
                        )
                    actual_logger.info(
                        f"{lines}[end] {func.__qualname__} {lines} "
                        f"{time_sec:.2f} seconds ({time_min:.2f} minutes)",
                    )
            except Exception:
                time_sec = time.time() - start_time
                time_min = time_sec / 60.0

                if min_duration > 0.0 and time_sec < min_duration:
                    actual_logger.info(
                        f"{lines}[start] {func.__qualname__} {lines}",
                    )
                actual_logger.info(
                    f"{lines}[abort] {func.__qualname__} {lines} "
                    f"{time_sec:.2f} seconds ({time_min:.2f} minutes)",
                )
                raise

            return result

        return wrapper

    return decorator


def _resolve_logger(
    logger: ILogger | None,
    args: tuple[object, ...],
) -> ILogger:
    """デコレーター適用時のロガーを解決する。"""
    if logger is not None:
        return logger
    if len(args) > 0 and hasattr(args[0], "_logger"):
        candidate = args[0]._logger  # type: ignore[attr-defined]
        if hasattr(candidate, "info"):
            return candidate  # type: ignore[no-any-return]
    msg = "logger が指定されておらず、self._logger も存在しません。"
    raise ValueError(msg)


def _format_line_prefix(
    line: Literal["#", "=", "-", "*"] | None,
) -> str:
    """区切り行のプレフィックス文字列を返す。"""
    if line in ("#", "=", "-", "*"):
        return line * 30 + " "
    return ""
