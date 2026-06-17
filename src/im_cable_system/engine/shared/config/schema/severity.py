"""共通の Severity Enum（ERROR / WARNING / INFO）。

複数セクション（validation の各バリデータ、current_estimation の収束失敗、
など）で重大度を扱うため、共通の Enum として切り出す。Config が値を解釈・
検証し終えた状態で各セクション dataclass に保持されるので、利用側は
``severity is Severity.ERROR`` のように比較すればよい。
"""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    """重大度レベル。"""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
