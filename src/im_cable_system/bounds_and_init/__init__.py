"""estimate_params 用の記述子探索境界・初期値 YAML 置き場。

IM / ケーブルそれぞれ ``im_descriptor_bounds_and_init.yaml`` /
``cable_descriptor_bounds_and_init.yaml`` を同梱する。``bounds`` は
探索上下限、``init`` は初期化方法（既定は midpoint）を表す。
読み込み・DTO 構築は ``im_cable_system.engine.shared.estimate_params_fit_spec`` が担う。
"""
