"""設定・ログ横断のデコレータ（内部束ね）。

``timer`` は親窓口 ``im_cable_system.engine.shared.config`` の ``__all__``
にも載せており、**層外・層横断からは config ルート窓口経由で import する**。
本パッケージはサブツリー内の束ねとして残し、層外向けの主窓口は config
ルートとする。
"""

from im_cable_system.engine.shared.config.decorators.timer import timer

__all__ = [
    "timer",
]
