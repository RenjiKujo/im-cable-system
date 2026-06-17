"""目標パフォーマンスカタログと Itm 結果の正規化・重み付き残差ベクトル。

比較データの抽出は :mod:`curve_comparison_data` の共有入口を用いる。
残差スケール正規化は :mod:`residual_normalization` の strategy を用いる。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)

from .curve_comparison_data import extract_curve_fit_comparison_data
from .residual_normalization import (
    IResidualNormalizationStrategy,
)


def compute_residual_vector(
    catalogs: ImPerformanceCurveCatalogDtos,
    itm: ItmDto,
    weights: tuple[float, float, float, float],
    normalization_strategy: IResidualNormalizationStrategy,
) -> np.ndarray:
    """カタログ目標値と Itm 結果の正規化・重み付き残差ベクトルを返す。

    入力の参照軸直積の各点について、一致する供給条件のカタログ行があれば
    スリップで補間した目標 (|I|, P, PF, η) とシミュ結果を突き合わせる。
    カタログが無い点は評価対象外（旧 NaN マスク相当）。

    各目標系列はカタログの観測マスク ``*_series_mask`` を補間元から除外して
    補間済み（:mod:`curve_grid_sampling`）であり、未観測点は ``NaN`` になる。
    本関数では **チャネルごとに独立した有効点マスク**
    ``valid_c = isfinite(target_c)`` を作り、各チャネルの正規化に渡す。
    したがって、あるチャネルだけ未観測でも他チャネルは評価される。

    NOTE:
        値スケールはチャネルごとに ``/ scale`` で正規化するが、**評価点数では
        正規化しない（mean 化しない）**。これは意図的な設計である。
        ``least_squares`` の cost は ``0.5 * sum(r_i^2)`` であり、評価点数が
        そのまま目的関数上の領域重みとして機能する。重要でない slip 領域は
        カタログ側で点数を減らすことで寄与を下げ、重要な領域は点数を増やして
        寄与を上げる運用を想定している。チャネル間の重要度は ``weights`` で
        別途制御する（点数＝領域重み、weights＝チャネル重みの役割分担）。
        このため ``1/sqrt(n)`` などの点数正規化は **行わない**。

    Args:
        catalogs: 目標とする性能カーブカタログ。
        itm: シミュレーション結果を含む中間 DTO。
        weights: (|I|, P, PF, η) の各残差に掛ける重み。
        normalization_strategy: 1 チャネル分の残差正規化 strategy（必須）。
            Config からの解決は呼び出し側
            （:class:`ResidualNormalizationStrategyFactory`）の責務とする。

    Returns:
        重み付き後に連結した残差ベクトル（float64）。評価不能時はスカラー
        `[1.0]`、いずれのチャネルにも有効点が無い場合は `[0.0]`。

    Raises:
        ValueError: 参照軸に slip / frequency / input_line_voltage が揃わない場合。
    """
    comparison = extract_curve_fit_comparison_data(catalogs, itm)
    if comparison is None:
        return np.array([1.0])

    if not (
        np.any(comparison.valid_i)
        or np.any(comparison.valid_p)
        or np.any(comparison.valid_pf)
        or np.any(comparison.valid_eta)
    ):
        return np.array([0.0])

    normalizer = normalization_strategy
    err_i = normalizer.normalize(
        comparison.target_i, comparison.pred_i, comparison.valid_i
    )
    err_p = normalizer.normalize(
        comparison.target_p, comparison.pred_p, comparison.valid_p
    )
    err_pf = normalizer.normalize(
        comparison.target_pf, comparison.pred_pf, comparison.valid_pf
    )
    err_eta = normalizer.normalize(
        comparison.target_eta, comparison.pred_eta, comparison.valid_eta
    )

    w_i, w_p, w_pf, w_eta = weights
    out = np.concatenate(
        [
            w_i * err_i,
            w_p * err_p,
            w_pf * err_pf,
            w_eta * err_eta,
        ]
    )
    return out.astype(np.float64)
