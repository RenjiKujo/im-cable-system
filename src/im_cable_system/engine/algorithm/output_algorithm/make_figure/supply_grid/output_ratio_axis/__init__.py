"""make_figure（supply_grid / 出力比横軸）の内部パッケージ。

供給電圧・周波数を (f, V) サブプロット軸、出力比 [%] を横軸とした性能曲線
Figure を組む（ForwardByCartesianGrid / EstimateParams 由来の出力）。系列派生・
カタログ整形・定格比算出は親パッケージ ``supply_grid`` の共有モジュールを
利用する。層外向けの公開窓口ではなく、orchestrate から利用する内部ステップ。
"""
