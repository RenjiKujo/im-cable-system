"""Forward / EstimateParams 両経路から共通利用される検査関数群。

本パッケージは ``validate_input_dto`` 配下の **層内専用窓口** であり、
``forward/validator.py`` / ``estimate_params/validator.py`` から
リーフモジュール（``array_layout_checks`` / ``cable_checks`` /
``im_checks`` / ``grid_size_checks`` / ``si_execute_input_contract``）を
直接 import して再利用するための置き場として機能する。

責務の方針:
    - 経路に依存しない、組み立て後 ``InputDto`` の構造・値域・
      SI 基本単位・grid size・cross-field 整合性チェック関数を扱う。
    - 経路ごとの差分（PC カタログの必須性、reference_axes の grid 上限の
      適用ポリシー、``@timer`` の付与など）は
      ``forward/validator.py`` / ``estimate_params/validator.py``
      側のオーケストレーションに置く。

公開範囲:
    本パッケージは層外・層横断・別責務ツリーからの公開窓口ではない
    （``__all__`` を意図的に持たない）。``validate_input_dto`` の
    層外向け窓口は ``validate_input_dto/__init__.py`` および
    ``forward/__init__.py`` / ``estimate_params/__init__.py`` であり、
    そちらが ``Validator`` クラスのみを再エクスポートする。
    ``docs/conventions/3_layering_and_imports.md`` の「``__all__`` なしの
    ``__init__.py``」運用に従う。
"""
