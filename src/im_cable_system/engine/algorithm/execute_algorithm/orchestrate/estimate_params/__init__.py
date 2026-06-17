"""IM ケーブルシステム パラメータ推定オーケストレーター用パッケージ。

等価回路パラメータをパフォーマンスカーブにフィットさせる
IEstimateParamsExecutionOrchestrator のインターフェースおよび
その実装をこのパッケージ配下に配置する。
目標曲線は ``InputDto.im_pc_catalogs`` に設定する。

実装（EstimateParamsOrchestrator）では最適化ループ内で forward の
プライベート段階メソッドのみを呼ぶ協調を行う。理由は実装モジュールの
モジュールドックストリングを参照。

コンポーネントは2軸で整理する。

- **軸1（ステップ）**: ``collect_descriptors``（記述子収集。IM はかご重数分岐
  ストラテジを ``im/`` に、ケーブルは ``cable/`` に分離）/ ``fit_parameters``
  （残差評価＋最適化）/ ``apply_fitted_input``（フィット結果の DTO 反映）/
  ``build_summary``（要約構築）… ``execute`` の実行フローに対応する。
- **軸2（共有）**: ``support``（複数ステップが共有する横断部品）。
  記述子 DTO は ``support/descriptor``、カタログ対シミュレーションの
  残差・指標・補間・正規化は ``support/curve_eval`` に集約する。

配置の理由は
``docs/algorithm/execute/2_component.md`` を参照。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.estimate_params_execution_orchestrator import (  # noqa: E501
    EstimateParamsOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.i_estimate_params_execution_orchestrator import (  # noqa: E501
    IEstimateParamsExecutionOrchestrator,
)

__all__: list[str] = [
    "IEstimateParamsExecutionOrchestrator",
    "EstimateParamsOrchestrator",
]
