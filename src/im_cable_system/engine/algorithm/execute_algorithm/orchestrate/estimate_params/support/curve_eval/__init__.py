"""カタログ対シミュレーションのカーブ評価（軸2: ステップ間共有の公開窓口）。

性能カタログ（目標）とシミュレーション結果（Itm）を突き合わせる
「比較データ抽出・残差・グリッド補間・残差正規化」をまとめた estimate_params
専用部品。fit_parameters（残差評価＝目的関数）・build_summary（RMSE 等）の
**2 経路が** :func:`extract_curve_fit_comparison_data` **を共有入口として利用する**。
どちらかのステップ配下ではなく ``support`` 配下に置く（依存方向の逆転を避ける）。

公開要素:
    - ``CurveFitComparisonData`` / ``extract_curve_fit_comparison_data``:
      カタログ目標とシミュ予測の共通比較データ（fit / summary の共有入口）。
    - ``compute_residual_vector``: fit の目的関数となる残差ベクトル。

NOTE: Output（詳細 CSV・図表）は本窓口を **利用しない**。CSV / YAML レポートは
    ``output_algorithm.make_report``、図表は ``output_algorithm.make_figure`` に
    出力向けの派生ロジックを持つ。観測点（ケーブル入力 / IM 入力 / IM 二次）や
    行整形を利用側ごとに調整できるようにし、output → execute の依存を
    持たせないための分離。
シミュ側 (|I|, P, PF, η) の抽出も共有部品にせず、:mod:`curve_comparison_data`
内で ItmDto から直接取り出す。RMSE / Δ標準偏差などの要約専用指標は利用元の
``build_summary`` 配下に private helper として置く（本窓口には公開しない）。
残差スケール正規化 strategy は下位窓口 :mod:`residual_normalization` を参照する。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.curve_comparison_data import (  # noqa: E501
    CurveFitComparisonData,
    extract_curve_fit_comparison_data,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.curve_residual_vector import (  # noqa: E501
    compute_residual_vector,
)

__all__: list[str] = [
    "CurveFitComparisonData",
    "compute_residual_vector",
    "extract_curve_fit_comparison_data",
]
