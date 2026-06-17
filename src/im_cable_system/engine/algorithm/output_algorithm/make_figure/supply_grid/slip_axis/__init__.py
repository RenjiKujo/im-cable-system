"""make_figure（supply_grid / slip 横軸）の内部パッケージ。

供給電圧・周波数を (f, V) サブプロット軸、slip を横軸とした性能曲線 Figure を
組む（ForwardByCartesianGrid / EstimateParams 由来の出力）。系列派生・カタログ
整形・描画ヘルパは親パッケージ ``supply_grid`` の共有モジュールを利用する。
層外向けの公開窓口ではなく、orchestrate から利用する内部ステップ。
"""
