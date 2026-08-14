"""docs/ とコード・設定の整合性を検証するテスト（本番パッケージ非対応）。

``tests/`` 配下の他ディレクトリはすべて ``src/im_cable_system/`` のパッケージ構成
（domain / algorithm / processor / pipeline / shared）と対応するが、本ディレクトリは
例外である。「ドキュメントが実装からドリフトしていないか」というリポジトリ横断の
整合性を扱うため、単一パッケージには対応しない
（docs/conventions/5_testing.md のディレクトリ構成規約における例外として明示）。
"""
