"""make_table（supply_grid 系）の内部パッケージ。

供給電圧・周波数を軸にした slip 軸グリッド表示の表（DataFrame）を組む
（ForwardByCartesianGrid / EstimateParams 由来の出力）。層外向けの公開窓口
ではなく、orchestrate から利用する内部ステップ。
"""
