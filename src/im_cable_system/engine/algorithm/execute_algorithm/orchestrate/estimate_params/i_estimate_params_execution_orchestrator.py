"""IM ケーブルシステム パラメータ推定実行オーケストレーターのインターフェース。

親 IExecuteAlgorithmsOrchestrator（``execute`` のみを契約）を継承する。
execute(input_dto) では input_dto.im_pc_catalogs を
パフォーマンス目標として用い、等価回路パラメータをフィットした上で、
forward オーケストレーターに委譲して ItmDto を確定させる。
forward の手順（build_model → simulate → validate_itm_dto）は
:class:`IForwardExecutionOrchestrator` 側の契約であり、本 IF では
``execute`` のみを契約とする（追加メソッドは持たない）。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.i_execute_algorithms_orchestrator import (  # noqa: E501
    IExecuteAlgorithmsOrchestrator,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class IEstimateParamsExecutionOrchestrator(
    IExecuteAlgorithmsOrchestrator[InputDto, ItmDto]
):
    """IM ケーブルシステム パラメータ推定実行オーケストレーターのインターフェース。

    パフォーマンスカーブ（slip vs |I|, P, PF, η）に等価回路の出力をフィットさせ、
    一次 R/L・励磁 R/L・二次 R/L・ケーブル R/L およびスリップ依存・電流依存モデルの
    係数などを推定する。目標曲線は ``InputDto.im_pc_catalogs``
    に設定する（None の場合は execute 時にエラー）。

    Note:
        具象実装はフィット中の残差評価では forward オーケストレーターの
        ``execute_without_validation`` を、フィット確定後の検証込み計算では
        ``execute`` を呼ぶ（計算時間短縮のため検証をループ外に寄せる）。
        いずれも forward の公開メソッド（IF 契約）であり、private を直接は
        叩かない。詳細は実装モジュールのドキュメントを参照。
    """
