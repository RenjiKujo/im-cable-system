"""estimate_params 実行結果の要約（条件・最適化結果・適合度）DTO。

要約は「どんな条件で最適化したか」「どんな結果だったか」「どれほど適合したか」
を 1 つの :class:`EstimateParamsFitSummaryDto` で一括取得できるよう、責務ごとの
小 DTO へネストする。これら子 DTO は本要約専用のため、モジュールを分けずに
本ファイル内へ閉じて定義する。

NOTE: 本 DTO 群は「最適化の結果レポート」であり Itm モデルには依存しない汎用値
    オブジェクトのため、``generic.reporting`` に配置する。Itm 中間 DTO
    （``ItmDto.estimate_params_fit_summary``）と Output DTO の双方から、
    ``itm`` ステージ窓口を経由せずに参照できる。

責務の対応:
    - 条件: :class:`OptimizerSettingsDto` / :class:`ResidualObjectiveSettingsDto`
    - 結果: :class:`OptimizerResultDto` / :class:`FittedParameterReportDto`
    - 適合度: :class:`FitChannelMetricDto` と全体 RMS
    - ラベル: :class:`FittedModelLabelsDto`
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FittedModelLabelsDto:
    """出力ラベル用のモデル名一式。

    Attributes:
        im_primary: 一次側モデル名。
        im_excitation: 励磁モデル名。
        im_secondary_inner: 二次内側モデル名。単一かご時は None。
        im_secondary_outer: 二次（単一かごまたは外側）モデル名。
        im_friction_windage: 摩擦・風損モデル名（``NONE`` を含め常に存在する）。
        im_stray_load: 漂遊負荷損モデル名（``im_friction_windage`` と同様）。
        cable_conductor: ケーブル導体モデル名。ケーブル無し時は None。
    """

    im_primary: str
    im_excitation: str
    im_secondary_inner: str | None
    im_secondary_outer: str
    im_friction_windage: str
    im_stray_load: str
    cable_conductor: str | None


@dataclass(frozen=True)
class OptimizerSettingsDto:
    """最適化器の実行条件（``scipy.optimize.least_squares`` へ渡した設定）。

    Attributes:
        algorithm: 最適化アルゴリズム名（例 "least_squares"）。
        max_nfev: 最大関数評価回数。
        ftol: コスト収束判定許容値。
        xtol: ステップ収束判定許容値。
        gtol: 勾配収束判定許容値。
    """

    algorithm: str
    max_nfev: int
    ftol: float
    xtol: float
    gtol: float


@dataclass(frozen=True)
class ResidualObjectiveSettingsDto:
    """残差（目的関数）の構成条件。

    ``normalization_statistic`` / ``normalization_eps`` はスケール正規化
    （by_curve_scale 系）でのみ意味を持つが、設定値の記録として常に保持する。

    Attributes:
        current_weight: |I| チャネルの残差重み。
        power_weight: 出力電力チャネルの残差重み。
        power_factor_weight: 力率チャネルの残差重み。
        efficiency_weight: 効率チャネルの残差重み。
        normalization_method: 残差正規化方式名（例 "by_curve_scale"）。
        normalization_statistic: 正規化スケールの代表統計量名（例 "std"）。
        normalization_eps: 正規化スケールのゼロ割回避 eps。
        normalize_by_point_count: 評価点数で正規化したか。本エンジンは点数を
            slip 領域の重みとして扱うため常に False（設計判断の記録）。
    """

    current_weight: float
    power_weight: float
    power_factor_weight: float
    efficiency_weight: float
    normalization_method: str
    normalization_statistic: str
    normalization_eps: float
    normalize_by_point_count: bool


@dataclass(frozen=True)
class OptimizerResultDto:
    """最適化器の生結果サマリ。

    Attributes:
        success: 最適化の success フラグ。
        message: 最適化メッセージ。
        nfev: 関数評価回数。
        cost: cost（0.5 * sum(r^2)）。
    """

    success: bool
    message: str
    nfev: int
    cost: float


@dataclass(frozen=True)
class FitChannelMetricDto:
    """1 チャネル分の適合指標（同一単位の RMSE と Δ標準偏差）。

    Attributes:
        n_valid: 当該チャネルで観測（評価対象）だった格子点数。
        rmse: カタログ補間値との RMSE。
        std_delta: 有効点上の (pred-target) の標準偏差。
        unit: 物理単位（例 "A" / "W"）。無次元チャネルは "-"。
    """

    n_valid: int
    rmse: float
    std_delta: float
    unit: str | None


@dataclass(frozen=True)
class FittedParameterReportDto:
    """フィットした 1 パラメータの報告単位（初期値・境界・結果を併記）。

    Attributes:
        path: パラメータ path（表示名）。
        initial_value: 探索開始時の初期値。
        fitted_value: フィット後値（記述子と同じ物理単位）。
        lower_bound: 探索下限。
        upper_bound: 探索上限。
        unit: 単位（無次元は None）。
        is_fixed: 固定パラメータ（lower==upper）か。
        is_at_lower_bound: フィット後値が下限に張り付いているか（固定時は False）。
        is_at_upper_bound: フィット後値が上限に張り付いているか（固定時は False）。
    """

    path: str
    initial_value: float
    fitted_value: float
    lower_bound: float
    upper_bound: float
    unit: str | None
    is_fixed: bool
    is_at_lower_bound: bool
    is_at_upper_bound: bool


@dataclass(frozen=True)
class EstimateParamsFitSummaryDto:
    """パラメータ推定 1 本の要約（Itm に付与しテーブル出力に使う）。

    「条件 → 結果 → 適合度」を 1 オブジェクトから一括取得できる。

    Attributes:
        model_labels: 出力ラベル用のモデル名一式。
        optimizer_settings: 最適化器の実行条件。
        residual_objective_settings: 残差（目的関数）の構成条件。
        optimizer_result: 最適化器の生結果サマリ。
        overall_rmse_weighted_residual: 終点残差ベクトルの RMS
            （各要素は curve_residual_vector 内の正規化・重み付き後）。
        n_residual_elements: 上記残差ベクトル長。
        n_valid_curve_points: いずれかのチャネルが観測済みの格子点数（和集合）。
        line_current: |I| チャネルの適合指標 [A]。
        output_power: 出力電力実部チャネルの適合指標 [W]。
        power_factor: 力率チャネルの適合指標 [-]。
        im_efficiency: IM 効率チャネルの適合指標 [-]。
        fitted_parameters: フィット済みパラメータの報告単位列。
    """

    model_labels: FittedModelLabelsDto
    optimizer_settings: OptimizerSettingsDto
    residual_objective_settings: ResidualObjectiveSettingsDto
    optimizer_result: OptimizerResultDto
    overall_rmse_weighted_residual: float
    n_residual_elements: int
    n_valid_curve_points: int
    line_current: FitChannelMetricDto
    output_power: FitChannelMetricDto
    power_factor: FitChannelMetricDto
    im_efficiency: FitChannelMetricDto
    fitted_parameters: tuple[FittedParameterReportDto, ...]
