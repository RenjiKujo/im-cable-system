"""display_figure ステップ（Figure artifact の画面表示）の内部パッケージ。

build と分離した I/O 専用ステップ。表示可否の判定は orchestrator が config
フラグ（``calculation.output.figures.show``）で行い、本パッケージは渡された
Figure の表示のみを担う（保存は export_figure、生成・加工は make_figure）。
層外向けの公開窓口ではなく、orchestrate から利用する内部ステップ。
"""
