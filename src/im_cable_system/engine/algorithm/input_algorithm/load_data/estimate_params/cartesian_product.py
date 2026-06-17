"""候補軸（一次・励磁・二次・ケーブル導体）の直積展開（Loader 内ユース）。

統合 TSV ``model_candidate_axis`` で与えられた候補モデルから、
:class:`EstimateParamsInputLoadedData` を 1 件構築するための
1 要素（モデル種別の組み合わせ）を順に yield する。

軸の選び方:
    - ``im_secondary(single)`` 候補があるときは単一かご run を生成する
      （``primary × excitation × secondary_single × [cable]``）。
    - ``im_secondary(double_inner)`` と ``im_secondary(double_outer)``
      が両方指定されているときは二重かご run を生成する
      （``primary × excitation × secondary_double_inner ×
      secondary_double_outer × [cable]``）。
    - 単一かご run と二重かご run の両方が指定されていれば、両方を
      順に yield する（単一かご run → 二重かご run の順）。
    - ``include_cable=True`` かつケーブル導体候補がある場合のみ導体軸を
      直積に含める。
    - 導体候補値 ``"NONE"`` は「その組合せはケーブル無し」を表す特別値
      として扱い、``EstimateParamsModelCombo.cable_conductor`` に
      ``None`` を入れて yield する。``cable_conductor_index`` は
      他候補と同じ 1-based の列番号で埋め、命名の一意化に使う。
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from dataclasses import dataclass

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ConductorModelType,
    ImExcitationModelType,
    ImPrimaryModelType,
    ImSecondaryModelType,
)


@dataclass(frozen=True)
class EstimateParamsModelCombo:
    """1 直積要素（Loader 内で per-combo の初期化に用いる）。

    Attributes:
        primary: 一次モデル種別。
        excitation: 励磁モデル種別。
        secondary_inner: 二重かご時の内側二次モデル種別。単一かご時は ``None``。
        secondary_outer: 二次（単一かごまたは外側）モデル種別。
        cable_conductor: ケーブル導体モデル種別。ケーブル無しのときは ``None``。
        primary_index: 統合 TSV ``im_primary`` 行の採用列番号（1-based）。
        excitation_index: 同 ``im_excitation`` 行。
        secondary_single_index: 同 ``im_secondary(single)`` 行。二重かご run の
            ときは ``0``。
        secondary_double_outer_index: 同 ``im_secondary(double_outer)`` 行。
            単一かご run のときは ``0``。
        secondary_double_inner_index: 同 ``im_secondary(double_inner)`` 行。
            単一かご run のときは ``0``。
        cable_conductor_index: 同 ``cable_conductor_model`` 行。ケーブル無し
            のときは ``0``。

    Note:
        ``*_index`` は命名（``ImCableSystemName`` / ``ImSeriesName`` /
        ``CableSeriesName``）の一意化に用いる。``iter_model_combos`` が
        正しい値を埋める。直接インスタンス化する単体テスト用にデフォルト
        ``0`` を許容する。
    """

    primary: ImPrimaryModelType
    excitation: ImExcitationModelType
    secondary_inner: ImSecondaryModelType | None
    secondary_outer: ImSecondaryModelType
    cable_conductor: ConductorModelType | None
    primary_index: int = 0
    excitation_index: int = 0
    secondary_single_index: int = 0
    secondary_double_outer_index: int = 0
    secondary_double_inner_index: int = 0
    cable_conductor_index: int = 0


def _build_cable_axis(
    candidate_cable_conductor: tuple[str, ...],
) -> tuple[ConductorModelType | None, ...]:
    """候補文字列列から、ケーブル無し候補 ``"NONE"`` を ``None`` に写した軸を作る。

    Args:
        candidate_cable_conductor: 統合 TSV の ``cable_conductor_model`` 行に
            並ぶ候補文字列（空セルは除外済み）。

    Returns:
        tuple[ConductorModelType | None, ...]: 各要素は ``ConductorModelType``
            または ``None``（``"NONE"`` のとき）。
    """
    axis: list[ConductorModelType | None] = []
    for token in candidate_cable_conductor:
        if token.upper() == "NONE":
            axis.append(None)
        else:
            axis.append(ConductorModelType(token))
    return tuple(axis)


def _cable_choices(
    cable_axis: tuple[ConductorModelType | None, ...],
    use_cable_axis: bool,
) -> tuple[tuple[int, ConductorModelType | None], ...]:
    """ケーブル軸の ``(1-based index, 値)`` 列を返す（無効時は ``(0, None)``）。"""
    if use_cable_axis:
        return tuple((i, c) for i, c in enumerate(cable_axis, start=1))
    return ((0, None),)


def _iter_single_cage_combos(
    *,
    primary_axis: tuple[ImPrimaryModelType, ...],
    excitation_axis: tuple[ImExcitationModelType, ...],
    secondary_single_axis: tuple[ImSecondaryModelType, ...],
    cable_axis: tuple[ConductorModelType | None, ...],
    use_cable_axis: bool,
) -> Iterator[EstimateParamsModelCombo]:
    """単一かご run の直積を yield する。

    ``secondary_single_axis`` が空のときは何も yield しない。
    """
    if not secondary_single_axis:
        return
    for (i_p, p), (i_e, e), (i_ss, ss), (i_c, c) in itertools.product(
        enumerate(primary_axis, start=1),
        enumerate(excitation_axis, start=1),
        enumerate(secondary_single_axis, start=1),
        _cable_choices(cable_axis, use_cable_axis),
    ):
        yield EstimateParamsModelCombo(
            primary=p,
            excitation=e,
            secondary_inner=None,
            secondary_outer=ss,
            cable_conductor=c,
            primary_index=i_p,
            excitation_index=i_e,
            secondary_single_index=i_ss,
            secondary_double_outer_index=0,
            secondary_double_inner_index=0,
            cable_conductor_index=i_c,
        )


def _iter_double_cage_combos(
    *,
    primary_axis: tuple[ImPrimaryModelType, ...],
    excitation_axis: tuple[ImExcitationModelType, ...],
    secondary_double_inner_axis: tuple[ImSecondaryModelType, ...],
    secondary_double_outer_axis: tuple[ImSecondaryModelType, ...],
    cable_axis: tuple[ConductorModelType | None, ...],
    use_cable_axis: bool,
) -> Iterator[EstimateParamsModelCombo]:
    """二重かご run の直積を yield する。

    ``secondary_double_inner_axis`` と ``secondary_double_outer_axis`` が
    両方非空のときに限り yield する。
    """
    if not secondary_double_inner_axis or not secondary_double_outer_axis:
        return
    for (
        (i_p, p),
        (i_e, e),
        (i_sdi, sdi),
        (i_sdo, sdo),
        (i_c, c),
    ) in itertools.product(
        enumerate(primary_axis, start=1),
        enumerate(excitation_axis, start=1),
        enumerate(secondary_double_inner_axis, start=1),
        enumerate(secondary_double_outer_axis, start=1),
        _cable_choices(cable_axis, use_cable_axis),
    ):
        yield EstimateParamsModelCombo(
            primary=p,
            excitation=e,
            secondary_inner=sdi,
            secondary_outer=sdo,
            cable_conductor=c,
            primary_index=i_p,
            excitation_index=i_e,
            secondary_single_index=0,
            secondary_double_outer_index=i_sdo,
            secondary_double_inner_index=i_sdi,
            cable_conductor_index=i_c,
        )


def iter_model_combos(
    parsed: EstimateParamsParsedTables,
    include_cable: bool,
) -> Iterator[EstimateParamsModelCombo]:
    """候補軸の直積を回し、1 組み合わせずつ yield する。

    単一かご run（``secondary_single`` 由来）と二重かご run
    （``secondary_double_inner × secondary_double_outer`` 由来）は
    別々に展開され、単一かご run → 二重かご run の順で yield される。
    一方のみが指定されている TSV では当該 run のみが生成される。

    Args:
        parsed: 統合 TSV パース結果。
        include_cable: ``True`` のときケーブル導体軸を直積に含める。
            ``False`` でもケーブル導体候補が無ければ自動的にスキップする。

    Yields:
        EstimateParamsModelCombo: 直積 1 要素。単一かご run の要素は
            ``secondary_inner is None``、二重かご run の要素は
            ``secondary_inner is not None``。
    """
    primary_axis = tuple(
        ImPrimaryModelType(v) for v in parsed.candidate_primary
    )
    excitation_axis = tuple(
        ImExcitationModelType(v) for v in parsed.candidate_excitation
    )
    secondary_single_axis = tuple(
        ImSecondaryModelType(v) for v in parsed.candidate_secondary_single
    )
    secondary_double_inner_axis = tuple(
        ImSecondaryModelType(v) for v in parsed.candidate_secondary_double_inner
    )
    secondary_double_outer_axis = tuple(
        ImSecondaryModelType(v) for v in parsed.candidate_secondary_double_outer
    )
    cable_axis = _build_cable_axis(parsed.candidate_cable_conductor)
    use_cable_axis = include_cable and len(cable_axis) > 0

    yield from _iter_single_cage_combos(
        primary_axis=primary_axis,
        excitation_axis=excitation_axis,
        secondary_single_axis=secondary_single_axis,
        cable_axis=cable_axis,
        use_cable_axis=use_cable_axis,
    )
    yield from _iter_double_cage_combos(
        primary_axis=primary_axis,
        excitation_axis=excitation_axis,
        secondary_double_inner_axis=secondary_double_inner_axis,
        secondary_double_outer_axis=secondary_double_outer_axis,
        cable_axis=cable_axis,
        use_cable_axis=use_cable_axis,
    )
