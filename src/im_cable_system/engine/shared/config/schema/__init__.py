"""Config の正規化済みスナップショット dataclass と組み立て factory。

Config 構築時（``Config.create``）にここで YAML スキーマ検証を行うため、
不正値は Config 取得時点で ``ValueError`` として弾かれる（fail-fast）。

設計方針:
    - **キーが欠損している場合**: そのセクションは既定値で補完する
      （クライアントが最小構成 YAML を渡したときの保険）
    - **キーは存在するが値が不正**: ``ValueError`` を送出し、YAML キーの
      フルパスと受け取った値・期待条件をメッセージに含める

公開窓口:
    各セクションの dataclass / Enum / ``ConfigSnapshot`` は、
    親パッケージ ``im_cable_system.engine.shared.config`` の ``__init__``
    に再エクスポートされている。**層外（algorithm / processor / pipeline
    / tests）は親パッケージ ``config`` ルートから import すること**。
    ``schema/`` 配下への直接 import は config パッケージ自身（``app_config`` /
    ``i_app_config`` / ``app_logger``）と schema 内部実装のみが行う。

    ``*ConfigFactory`` / ``ConfigSnapshotFactory`` および ``_parsers`` は
    層外向け窓口に載せない（生成は ``Config.create`` が一本化する責務を持ち、
    層外から個別 factory を呼ぶ必要は無い）。

そのため本 ``__init__.py`` は import 窓口ではなく、``__all__`` を持たない。
"""
