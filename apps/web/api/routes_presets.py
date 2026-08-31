"""config プリセット一覧・入力ファイルプリセット一覧。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from apps.web.api.config_preset_loader import list_config_presets
from apps.web.api.dependencies import Settings
from apps.web.api.input_preset_loader import list_input_presets
from apps.web.api.schemas import (
    ConfigPresetListResponse,
    ConfigPresetResponse,
    InputPresetListResponse,
    InputPresetResponse,
)

router = APIRouter()


@router.get("/api/config-presets", response_model=ConfigPresetListResponse)
async def get_config_presets(
    mode: str, settings: Settings
) -> ConfigPresetListResponse:
    """サーバ同梱の config プリセット名と YAML 全文を返す。未知 mode は 400。"""
    try:
        presets = list_config_presets(mode, repo_root=settings.repo_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return ConfigPresetListResponse(
        presets=[ConfigPresetResponse.model_validate(p) for p in presets]
    )


@router.get("/api/input-presets", response_model=InputPresetListResponse)
async def get_input_presets(
    mode: str, settings: Settings
) -> InputPresetListResponse:
    """サーバ同梱の入力ファイルプリセットを field ごとに返す。未知 mode は 400。"""
    try:
        presets_by_field = list_input_presets(
            mode, repo_root=settings.repo_root
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return InputPresetListResponse(
        presets_by_field={
            field: [InputPresetResponse.model_validate(p) for p in presets]
            for field, presets in presets_by_field.items()
        }
    )
