"""候補軸ごとのモデル種別語彙・必須軸ラベル。

これは engine の入出力ファイル契約の**写し**である。``apps/`` は engine を
import しない方針（docs/apps/web/0_overview.md）のため、種別タプルと軸
ラベルをここに持つ。写しが engine から離れたら
``tests/test_apps/test_web/engine_contract/test_engine_contract_drift.py`` が落ちる。

種別語彙を全軸ぶん持つのは投入時プリフライトのためである。engine 側は
モデル種別名を str のまま扱い、未知の名前は bounds YAML 引きの ``KeyError``
になる（``docs/architecture/algorithm/input/3_design_principles.md``）。
``KeyError`` は runner の exit 1 ＝ ``error_kind="unexpected"`` へ落ちるので、
利用者のタイポがそのまま「想定外エラー」として出る。ここで先に 422 へ
翻訳するために語彙が要る。
"""

from __future__ import annotations

IM_PRIMARY_KINDS: tuple[str, ...] = (
    "BASIC",
    "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
    "CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1",
)
IM_EXCITATION_KINDS: tuple[str, ...] = (
    "BASIC",
    "SLIP_DEPENDENT_SATURATION_V1",
    "CURRENT_DEPENDENT_SATURATION_V1",
)
IM_SECONDARY_KINDS: tuple[str, ...] = (
    "BASIC",
    "SLIP_DEPENDENT_SKIN_EFFECT_V1",
    "CURRENT_DEPENDENT_SKIN_EFFECT_V1",
    "CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1",
    "CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1",
)
IM_FRICTION_WINDAGE_KINDS: tuple[str, ...] = ("NONE", "CONSTANT_V1")
IM_STRAY_LOAD_KINDS: tuple[str, ...] = (
    "NONE",
    "CURRENT_DEPENDENT_QUADRATIC_V1",
)

# 導体軸だけ ``NONE`` が Enum メンバではなく、「その組合せはケーブル無し」を
# 表す特別値である（engine 側 ``cartesian_product`` の docstring）。
# したがって Enum の写し＋``NONE`` が候補として合法。
CABLE_CONDUCTOR_NONE_TOKEN = "NONE"
CABLE_CONDUCTOR_KINDS: tuple[str, ...] = (
    "BASIC",
    "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1",
    "CURRENT_DEPENDENT_SKIN_EFFECT_V1",
    CABLE_CONDUCTOR_NONE_TOKEN,
)

# 軸ラベル → その軸で合法な種別。キー集合は engine の
# ``unified_input_parser._CANDIDATE_AXIS_LABELS`` と一致する。
CANDIDATE_AXIS_KINDS: dict[str, tuple[str, ...]] = {
    "im_primary": IM_PRIMARY_KINDS,
    "im_excitation": IM_EXCITATION_KINDS,
    "im_secondary(single)": IM_SECONDARY_KINDS,
    "im_secondary(double_inner)": IM_SECONDARY_KINDS,
    "im_secondary(double_outer)": IM_SECONDARY_KINDS,
    "im_friction_windage": IM_FRICTION_WINDAGE_KINDS,
    "im_stray_load": IM_STRAY_LOAD_KINDS,
    "cable_conductor_model": CABLE_CONDUCTOR_KINDS,
}

REQUIRED_CANDIDATE_AXIS_LABELS: tuple[str, ...] = (
    "im_friction_windage",
    "im_stray_load",
)

CANDIDATE_BLOCK_HEADER = "model_candidate_axis"
