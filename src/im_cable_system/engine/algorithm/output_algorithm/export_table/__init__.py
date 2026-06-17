"""export_table ステップ（表 artifact のファイル保存）の内部パッケージ。

build と分離した I/O 専用ステップ。エクスポート可否の判定は orchestrator が
config フラグ（``dump.output.tables.enabled``）で行い、本パッケージは保存
のみを担う。表に表示（show）は無い。層外向けの公開窓口ではなく、orchestrate
から利用する内部ステップ。
"""
