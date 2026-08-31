"""リクエスト／レスポンス DTO。

境界での例外として ``pydantic.BaseModel`` を継承する
（docs/apps/web/0_overview.md の「外部フレームワークの基底クラス継承」）。

応答スキーマの多くは ``model_config = ConfigDict(from_attributes=True)`` を持つ。
これにより FastAPI の
``response_model`` が ``store.JobRecord`` / ``runner_gateway.ArtifactInfo`` /
``engine_contract.FittedCatalogView`` のようなドメイン DTO（dataclass）から
同名フィールドを自動で詰め替える。ルート側は
``ResponseModel.model_validate(dto)`` を呼ぶだけでよく、手書きの
``_to_xxx`` 変換関数が要らない。ネストしたフィールド（``NameplateResponse`` の
``power`` など）が dataclass インスタンスを受け取る場合、そのネスト先の
モデルにも同じ ``from_attributes=True`` が要る（辞書を受け取るだけの
``ModelLabelsResponse`` は不要）。
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)


class JobSubmitResponse(BaseModel):
    """投入直後（202）のレスポンス。"""

    job_id: str
    status: str
    warnings: list[str] = []


class JobDetailResponse(BaseModel):
    """ジョブ 1 件の状態・時刻・終了コード・エラー。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    mode: str
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    exit_code: int | None
    error_kind: str | None
    error_message: str | None
    timezone: str

    @field_serializer("created_at", "started_at", "finished_at")
    def serialize_job_times(self, value: datetime | None) -> str | None:
        """UTC オフセットを ``+00:00`` で出す（``Z`` 省略形にしない）。"""
        if value is None:
            return None
        return value.isoformat()


class JobListResponse(BaseModel):
    """ジョブ一覧。"""

    jobs: list[JobDetailResponse]


class ArtifactResponse(BaseModel):
    """成果物 1 件の走査結果。"""

    model_config = ConfigDict(from_attributes=True)

    kind: str
    rel_path: str
    size_bytes: int
    modified_at: datetime

    @field_validator("modified_at", mode="before")
    @classmethod
    def _modified_at_from_epoch_seconds(cls, value: object) -> object:
        """``ArtifactInfo.modified_at`` は epoch 秒（float）なので UTC の datetime へ直す。"""
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return value


class ArtifactListResponse(BaseModel):
    """成果物一覧。"""

    artifacts: list[ArtifactResponse]


class ConfigPresetResponse(BaseModel):
    """config プリセット 1 件（名前・説明・YAML 全文）。"""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    yaml_text: str


class ConfigPresetListResponse(BaseModel):
    """config プリセット一覧。"""

    presets: list[ConfigPresetResponse]


class InputPresetResponse(BaseModel):
    """入力ファイルプリセット 1 件（名前・説明・ファイル全文）。"""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    text: str


class InputPresetListResponse(BaseModel):
    """入力ファイルプリセット一覧（field ごと）。"""

    presets_by_field: dict[str, list[InputPresetResponse]]


class QuantityResponse(BaseModel):
    """名板量 1 件。"""

    model_config = ConfigDict(from_attributes=True)

    value: float
    unit: str


class NameplateResponse(BaseModel):
    """推定結果 YAML の名板。"""

    model_config = ConfigDict(from_attributes=True)

    power: QuantityResponse
    current: QuantityResponse


class ModelLabelsResponse(BaseModel):
    """推定結果のモデルラベル（7 キー）。"""

    im_primary: str
    im_excitation: str
    im_secondary_inner: str
    im_secondary_outer: str
    im_friction_windage: str
    im_stray_load: str
    cable_conductor: str


class FittedParameterResponse(BaseModel):
    """推定パラメータ 1 件。"""

    model_config = ConfigDict(from_attributes=True)

    path: str
    value: float
    unit: str | None
    initial_value: float | None
    lower_bound: float | None
    upper_bound: float | None
    bound_status: str


class FitMetricsResponse(BaseModel):
    """適合指標。"""

    model_config = ConfigDict(from_attributes=True)

    optimizer_success: bool
    least_squares_cost: float
    overall_rmse_weighted_residual: float
    n_residual_elements: int
    n_valid_curve_points: int


class FitSummaryResponse(BaseModel):
    """``report_model_*.yaml`` から表示用に写した推定結果サマリ。"""

    model_config = ConfigDict(from_attributes=True)

    name: str
    nameplate: NameplateResponse
    model_labels: ModelLabelsResponse
    fitted_parameters: list[FittedParameterResponse]
    fit_metrics: FitMetricsResponse
    # FittedCatalogView 側の実体名。応答には出さず report_rel_path の算出にだけ使う。
    source_filename: str = Field(exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def report_rel_path(self) -> str:
        return f"reports/{self.source_filename}"


class FitSummaryListResponse(BaseModel):
    """1 ジョブ分の推定結果サマリ一覧。"""

    summaries: list[FitSummaryResponse]
