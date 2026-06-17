"""make_figure（supply_grid 系）の内部パッケージ。

供給電圧・周波数 (f, V) を軸にした性能曲線 Figure 群を組む
（ForwardByCartesianGrid / EstimateParams 由来の出力）。横軸の意味ごとに
サブパッケージへ分割する（``slip_axis``: slip 横軸 / ``output_ratio_axis``:
出力比横軸）。

直下のモジュールは横軸に依存しない共有部品で、各ビルダーから利用する:

- ``_unit_helpers``: 単位付き DTO → ndarray 取り出し。
- ``series``: ``OutputDto.result`` からの生量系列派生と (f, V) スライス。
- ``catalog``: 参照カタログの正規化と供給条件マッチ。
- ``ratios``: 銘板値に基づく出力比・電流比の算出。
- ``plotting_common``: 多軸描画・統合凡例・A4 レイアウト。

層外向けの公開窓口ではなく、orchestrate から利用する内部ステップ。
"""
