"""test_processor 配下の共通 pytest 設定。

重い結合テスト（``slow``）を収集順の末尾へ寄せ、軽い疎通を先に実行する。
"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(
    config: pytest.Config,  # noqa: ARG001
    items: list[pytest.Item],
) -> None:
    """``slow`` マーカー付きテストを末尾へ移動する。"""
    regular_items: list[pytest.Item] = []
    slow_items: list[pytest.Item] = []
    for item in items:
        if item.get_closest_marker("slow") is not None:
            slow_items.append(item)
        else:
            regular_items.append(item)
    items[:] = regular_items + slow_items
