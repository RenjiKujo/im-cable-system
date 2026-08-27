"""FastAPI 窓口。ジョブの投入・照会・成果物配信を HTTP で公開する。

``store``（ジョブ台帳）と ``runner_gateway``（subprocess 実行）と
``engine_contract``（engine 入出力ファイル契約の写し）に依存する
（engine の公開窓口・リーフ実装には直接依存しない）。
"""

from apps.web.api.main import create_app

__all__ = ["create_app"]
