"""IM ケーブルシステム Input オーケストレーション群の束ねパッケージ。

このパッケージ自体は import 窓口ではない（``__all__`` を持たない）。
実行モードごとに分割した次のサブパッケージを公開窓口として用いる：

- :mod:`im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward`
    Forward 系（CartesianGrid / OperatingPoints 共通）。モード差は
    ``ForwardInputOrchestrator.create`` の ``reference_axes`` 引数で表現する。
- :mod:`im_cable_system.engine.algorithm.input_algorithm.orchestrate.estimate_params`

層外・層横断からは上記サブパッケージの ``__init__`` から
インターフェイス／具象クラスを import すること。

設計方針（Strategy + Factory を採らない理由）:
    Input 層は実行モード（Forward / EstimateParams）が固定で、新モード
    追加の見込みが薄いため、``execute_algorithm`` 系で採用している
    Strategy + ``factory_*`` 構成は採用しない。``processor/input_stage``
    側がモードごとに具象 Orchestrator を直接 import し、
    ``Orchestrator.create(...)`` でインスタンス化する方針とする。
    Strategy パターンの旨味（同じ入力型で実装だけ差し替える）も、
    ``ForwardJobSpec`` と ``EstimateParamsJobSpec`` のように入力型が
    モードごとに異なる本層では成立しない。新モード追加が現実に必要に
    なった段階で、``execute_algorithm`` 同様の Factory 構成へ昇格させる。
"""
