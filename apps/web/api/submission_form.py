"""multipart フォーム 1 件から 1 ジョブ分の ``JobInputs`` を取り出す。

``routes_jobs`` と同じ責務ツリー内の内部実装。公開窓口へは再エクスポートしない。

``form`` / ``mode`` / ``layout`` / ``settings`` はフォーム読み取りの全経路が同じ組で
必要とするため、関数引数で回さず ``SubmissionForm`` のフィールドに持たせている。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from starlette.datastructures import FormData, UploadFile

from apps.web.api.config_preset_loader import read_config_preset
from apps.web.api.input_preset_loader import read_input_preset
from apps.web.api.input_validation import (
    validate_estimate_params_csv,
    validate_uploaded_im_bounds,
    validate_uploaded_im_catalog,
)
from apps.web.runner_gateway import (
    EstimateParamsInputs,
    ForwardInputs,
    JobInputs,
    JobLayout,
    JobMode,
    RunnerGatewaySettings,
    save_input_file,
)


@dataclass(frozen=True)
class FieldBytes:
    """アップロード or プリセットから取り出した 1 フィールド分のファイル本体。"""

    filename: str
    content: bytes


class SubmissionForm:
    """multipart フォームから 1 ジョブ分の入力を取り出す読み取り専用ラッパー。"""

    def __init__(
        self,
        form: FormData,
        *,
        mode: JobMode,
        layout: JobLayout,
        settings: RunnerGatewaySettings,
    ) -> None:
        self._form = form
        self._mode = mode
        self._layout = layout
        self._settings = settings

    async def read_optional(self, field_name: str) -> FieldBytes | None:
        """アップロード or プリセットからバイト列を取り出す。

        ``form[field_name]``（アップロード）と ``form[f"{field_name}_preset"]``
        （プリセット名）の両方が指定された場合は、どちらが勝つかを黙って決めず
        400 にする。どちらも無ければ ``None``（呼び出し側が必須／既定値を判断する）。

        Raises:
            HTTPException: 両方指定は 400。未知のプリセット名も 400。
        """
        raw_upload = self._form.get(field_name)
        raw_preset = self._form.get(f"{field_name}_preset")
        # 判定と値の取り出しを別々に書くと型が絞れず assert が要る。
        # 絞り込み済みの値そのものを束ねて None 判定に寄せる。
        upload = raw_upload if isinstance(raw_upload, UploadFile) else None
        preset_name = (
            raw_preset.strip()
            if isinstance(raw_preset, str) and raw_preset.strip()
            else None
        )
        if upload is not None and preset_name is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{field_name} は"
                    "アップロードとプリセットを同時に指定できません。"
                ),
            )
        if upload is not None:
            return FieldBytes(
                filename=upload.filename or field_name,
                content=await upload.read(),
            )
        if preset_name is not None:
            try:
                filename, content = read_input_preset(
                    self._mode.value,
                    field_name,
                    preset_name,
                    repo_root=self._settings.repo_root,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
                ) from exc
            return FieldBytes(filename=filename, content=content)
        return None

    async def read_required(self, field_name: str) -> FieldBytes:
        """``read_optional`` の必須版。無ければ 400。"""
        result = await self.read_optional(field_name)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"必須の入力が不足しています: {field_name}",
            )
        return result

    async def save_optional(self, field_name: str, default_path: Path) -> Path:
        """アップロード・プリセット・同梱既定値のいずれかを解決する（契約検証なし）。"""
        result = await self.read_optional(field_name)
        if result is None:
            return default_path
        return save_input_file(
            self._layout, field_name, result.filename, result.content
        )

    async def resolve_config(self) -> tuple[str, dict[str, Any] | None]:
        """アップロードされた config.yaml、またはプリセット名から base_yaml_text を決める。"""
        overrides: dict[str, Any] | None = None
        overrides_raw = self._form.get("overrides_json")
        if isinstance(overrides_raw, str) and overrides_raw.strip():
            try:
                overrides = json.loads(overrides_raw)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"overrides_json が不正な JSON です: {exc}",
                ) from exc

        config_yaml_file = self._form.get("config_yaml")
        if isinstance(config_yaml_file, UploadFile):
            content = await config_yaml_file.read()
            return content.decode("utf-8"), overrides

        base_config_name = self._form.get("base_config")
        if isinstance(base_config_name, str) and base_config_name.strip():
            try:
                return (
                    read_config_preset(
                        self._mode.value,
                        base_config_name.strip(),
                        repo_root=self._settings.repo_root,
                    ),
                    overrides,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
                ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="base_config または config_yaml のいずれかが必要です。",
        )

    async def _resolve_im_bounds(self) -> Path:
        """アップロード or プリセットの IM bounds だけ契約検証する（同梱既定値は検証しない）。"""
        result = await self.read_optional("im_bounds")
        if result is None:
            return self._settings.im_bounds_and_init_default
        validate_uploaded_im_bounds(result.content.decode("utf-8"))
        return save_input_file(
            self._layout, "im_bounds", result.filename, result.content
        )

    async def _resolve_im_catalog(self) -> Path:
        """アップロード or プリセットの IM catalog だけ契約検証する（同梱既定値は検証しない）。"""
        result = await self.read_optional("im_catalog")
        if result is None:
            return self._settings.im_series_catalog_default
        validate_uploaded_im_catalog(result.content.decode("utf-8"))
        return save_input_file(
            self._layout, "im_catalog", result.filename, result.content
        )

    async def build_inputs(self) -> tuple[JobInputs, list[str]]:
        """mode に応じて ``JobInputs`` を組み立てる（警告があれば添える）。"""
        if self._mode is JobMode.ESTIMATE_PARAMS:
            return await self._build_estimate_params_inputs()
        return await self._build_forward_inputs()

    async def _build_estimate_params_inputs(
        self,
    ) -> tuple[JobInputs, list[str]]:
        input_field = await self.read_required("input")
        warnings = list(
            validate_estimate_params_csv(
                input_field.content, filename=input_field.filename
            )
        )
        input_path = save_input_file(
            self._layout, "input", input_field.filename, input_field.content
        )
        im_bounds_path = await self._resolve_im_bounds()
        cable_bounds_path = await self.save_optional(
            "cable_bounds", self._settings.cable_bounds_and_init_default
        )
        return (
            EstimateParamsInputs(
                input_csv_path=input_path,
                im_bounds_path=im_bounds_path,
                cable_bounds_path=cable_bounds_path,
            ),
            warnings,
        )

    async def _build_forward_inputs(self) -> tuple[JobInputs, list[str]]:
        series_field = await self.read_required("series_selection")
        axes_field = await self.read_required("axes")
        series_path = save_input_file(
            self._layout,
            "series_selection",
            series_field.filename,
            series_field.content,
        )
        axes_path = save_input_file(
            self._layout, "axes", axes_field.filename, axes_field.content
        )
        performance_curve_field = await self.read_optional("performance_curve")
        performance_curve_path = None
        if performance_curve_field is not None:
            performance_curve_path = save_input_file(
                self._layout,
                "performance_curve",
                performance_curve_field.filename,
                performance_curve_field.content,
            )
        im_catalog_path = await self._resolve_im_catalog()
        cable_catalog_path = await self.save_optional(
            "cable_catalog", self._settings.cable_series_catalog_default
        )
        return (
            ForwardInputs(
                series_selection_path=series_path,
                axes_path=axes_path,
                im_catalog_path=im_catalog_path,
                cable_catalog_path=cable_catalog_path,
                performance_curve_path=performance_curve_path,
            ),
            [],
        )
