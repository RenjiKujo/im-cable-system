"""make_table ステップ（OutputDto → 表 DataFrame）の内部パッケージ。

表示系ごとにサブパッケージを分ける（supply_grid: 供給電圧・周波数の
slip 軸グリッド / operating_points: 運転点ごとの index 時系列）。共通契約は
``i_table_builder.ITableBuilder``。build のみを担い保存（I/O）は行わない。
層外向けの公開窓口ではなく、orchestrate から利用する内部ステップ。
"""
