"""export_figure ステップ（Figure artifact のファイル保存）の内部パッケージ。

build と分離した I/O 専用ステップ。エクスポート可否の判定は orchestrator が
config フラグ（``dump.output.figures.enabled``）で行い、本パッケージは保存
のみを担う。表示（show）は display_figure に分離する。層外向けの公開窓口では
なく、orchestrate から利用する内部ステップ。
"""
