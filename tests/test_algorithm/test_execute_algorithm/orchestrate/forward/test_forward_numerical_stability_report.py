"""forward 実行で build/simulate 双方のクランプが ItmDto に集約される e2e テスト。

:class:`DirectForwardExecutionOrchestrator` の ``execute`` は build_model と
simulate を同一の ``numerical_stability_scope`` で包む。本テストは、その
スコープ内で発火したクランプ（数値安定化イベント）が
``ItmDto.numerical_stability_report`` に集約されること、特に **build_model
専用イベントと simulate 専用イベントの両方**が載ることを e2e で固定する。

入力 fixture（``single_cage_input_im_cable_system_dto``）の slip 配列は ``0.0``
を含むため、二次イミタンス変換（build_model）と電圧電流・トルク計算
（simulate）の双方でクランプが発火する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.direct_forward_execution_orchestrator import (  # noqa: E501
    DirectForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.numerical_stability import event_codes

# build_model 専用に発火するイベント（二次イミタンス変換の slip 極小マスク）。
# 二次イミタンス変換はモデル構築段階でのみ呼ばれ、simulate では呼ばれない。
_BUILD_ONLY_EVENT_CODES = frozenset(
    {
        event_codes.SLIP_NEAR_ZERO_SECONDARY_LOAD_IMM,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_TOTAL_IMM,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_SKIN_EFFECT_LOAD,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_SKIN_EFFECT_TOTAL,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_LEAKAGE_SAT_LOAD,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_LEAKAGE_SAT_TOTAL,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_SKIN_LEAKAGE_SAT_LOAD,
        event_codes.SLIP_NEAR_ZERO_SECONDARY_SKIN_LEAKAGE_SAT_TOTAL,
    }
)

# simulate 専用に発火するイベント（電圧電流計算・特性値計算）。
# オーム/キルヒホッフ・相線変換・トルク/力率はシミュレーション段階でのみ呼ばれ、
# build_model では呼ばれない。
_SIMULATE_ONLY_EVENT_CODES = frozenset(
    {
        event_codes.OHMS_LAW_CURRENT_IMPEDANCE_INPUT_EXTREME,
        event_codes.OHMS_LAW_CURRENT_ADMITTANCE_INPUT_EXTREME,
        event_codes.OHMS_LAW_VOLTAGE_IMPEDANCE_INPUT_EXTREME,
        event_codes.OHMS_LAW_VOLTAGE_ADMITTANCE_INPUT_EXTREME,
        event_codes.KIRCHHOFF_VOLTAGE_EXTREME_INPUT,
        event_codes.KIRCHHOFF_CURRENT_EXTREME_INPUT,
        event_codes.VOLTAGE_EXTREME_SMALL,
        event_codes.VOLTAGE_EXTREME_LARGE,
        event_codes.CURRENT_EXTREME_SMALL,
        event_codes.CURRENT_EXTREME_LARGE,
        event_codes.OMEGA_NEAR_ZERO_TORQUE,
        event_codes.APPARENT_POWER_NEAR_ZERO_POWER_FACTOR,
    }
)


class TestForwardNumericalStabilityReport:
    """forward 実行が build/simulate のクランプを report に集約するか検証する。"""

    def test_report_aggregates_build_and_simulate_clamps(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dto,
    ) -> None:
        """build_model と simulate の双方のクランプが report に集約される。

        slip=0.0 を含む入力を Direct 実行し、``numerical_stability_report`` に
        build_model 専用イベントと simulate 専用イベントの両方が
        含まれることを検証する。個別イベントの増減に左右されないよう、
        各「専用イベント集合」との積が非空であることのみを固定する。
        """
        orchestrator = DirectForwardExecutionOrchestrator.create(
            config=config,
            logger=logger,
        )
        itm = orchestrator.execute(
            input_dto=single_cage_input_im_cable_system_dto
        )

        report = itm.numerical_stability_report
        assert report is not None
        assert not report.is_empty()
        assert all(count > 0 for _, count in report.event_counts)

        codes = {code for code, _ in report.event_counts}
        build_hits = codes & _BUILD_ONLY_EVENT_CODES
        simulate_hits = codes & _SIMULATE_ONLY_EVENT_CODES
        assert build_hits, (
            "build_model 由来の数値安定化イベントが report に集約されていません: "
            f"codes={sorted(codes)}"
        )
        assert simulate_hits, (
            "simulate 由来の数値安定化イベントが report に集約されていません: "
            f"codes={sorted(codes)}"
        )
