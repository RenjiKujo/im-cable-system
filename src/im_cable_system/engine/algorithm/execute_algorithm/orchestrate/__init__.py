"""im_cable_system オーケストレーターの内部パッケージ（束ね用）。

forward / estimate_params など実行モード別のオーケストレーター
サブパッケージを束ねる。本パッケージ自体は import 窓口ではない
（``__all__`` を持たない）。

Note:
    各シンボルは「同 Dir 公開」の方針に従い、それが定義された Dir の
    ``__init__.py`` 窓口から import する。
    - 全モード共通 IF（:class:`IExecuteAlgorithmsOrchestrator`）:
      ``execute_algorithm`` 直下の窓口。
    - モード別 IF / 実装 / ファクトリ:
      ``orchestrate.forward`` / ``orchestrate.estimate_params`` 等の窓口。
"""
