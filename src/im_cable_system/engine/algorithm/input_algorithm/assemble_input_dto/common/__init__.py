"""Forward / EstimateParams 両経路から共通利用される組み立てヘルパ群。

本パッケージは ``assemble_input_dto`` 配下の **層内専用窓口** であり、
``forward/assembler.py`` / ``estimate_params/assembler.py`` の Assembler
から直接 import するリーフと、それらが内部で利用するヘルパで構成する。

Assembler から直接 import するリーフ:
    - ``array_layout_builder``: ``ArrayLayoutDto`` 構築
    - ``cable_dto_builder``: ``CableDto`` 構築
    - ``im_dto_builder``: ``ImDto`` 構築
    - ``performance_curve_dto_builder``:
      ``ImPerformanceCurveCatalogDtos`` 構築（絶対単位前提・比率単位拒否）
    - ``si_normalizer``: 組み立て後 ``InputDto`` 全体の SI 基本単位化

builder から内部利用されるヘルパ:
    - ``unit_normalizer``: 単位文字列の正規化
    - ``model_params_builder``: モデルパラメータ辞書 →
      ``FloatParamDtos`` の変換

責務の方針:
    - 経路に依存しない、LoadedData → ``InputDto`` 構成要素 DTO への
      純粋な変換と、組み立て後 ``InputDto`` の SI 基本単位化を扱う。
    - 経路ごとの差分（参照軸の選び方、ratio→absolute 変換の有無など）は
      ``forward/assembler.py`` / ``estimate_params/assembler.py``
      側のオーケストレーションに置く。

公開範囲:
    本パッケージは層外・層横断・別責務ツリーからの公開窓口ではない
    （``__all__`` を意図的に持たない）。``assemble_input_dto`` の
    層外向け窓口は ``assemble_input_dto/__init__.py`` および
    ``forward/__init__.py`` / ``estimate_params/__init__.py`` であり、
    そちらが ``Assembler`` クラスのみを再エクスポートする。
    ``docs/conventions/3_layering_and_imports.md`` の「``__all__`` なしの
    ``__init__.py``」運用に従う。
"""
