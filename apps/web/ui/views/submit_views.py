"""Submit Job ページ（``pages/1_Submit_Job.py``）の描画関数群とフィールド定義。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

_CSV_PREVIEW_LINES = 40


@dataclass(frozen=True)
class InputFieldSpec:
    """1 入力フィールド分の UI 定義。フィールドの追加漏れを型で弾くため dataclass で持つ。"""

    field: str
    label: str
    upload_types: list[str]
    content_type: str
    allow_none: bool


ESTIMATE_PARAMS_FIELDS: tuple[InputFieldSpec, ...] = (
    InputFieldSpec(
        field="input",
        label="input（必須）",
        upload_types=["csv", "tsv"],
        content_type="text/csv",
        allow_none=False,
    ),
    InputFieldSpec(
        field="im_bounds",
        label="im_bounds",
        upload_types=["yaml", "yml"],
        content_type="application/x-yaml",
        allow_none=False,
    ),
    InputFieldSpec(
        field="cable_bounds",
        label="cable_bounds",
        upload_types=["yaml", "yml"],
        content_type="application/x-yaml",
        allow_none=False,
    ),
)

FORWARD_FIELDS: tuple[InputFieldSpec, ...] = (
    InputFieldSpec(
        field="series_selection",
        label="series_selection（必須）",
        upload_types=["csv", "tsv"],
        content_type="text/csv",
        allow_none=False,
    ),
    InputFieldSpec(
        field="axes",
        label="axes（必須）",
        upload_types=["csv", "tsv"],
        content_type="text/csv",
        allow_none=False,
    ),
    InputFieldSpec(
        field="performance_curve",
        label="performance_curve（任意。カタログ曲線との重ね描き用）",
        upload_types=["csv", "tsv"],
        content_type="text/csv",
        allow_none=True,
    ),
    InputFieldSpec(
        field="im_catalog",
        label="im_catalog",
        upload_types=["yaml", "yml"],
        content_type="application/x-yaml",
        allow_none=False,
    ),
    InputFieldSpec(
        field="cable_catalog",
        label="cable_catalog",
        upload_types=["yaml", "yml"],
        content_type="application/x-yaml",
        allow_none=False,
    ),
)


def render_preset_preview(text: str, *, is_yaml: bool) -> None:
    if is_yaml:
        st.code(text, language="yaml")
        return
    lines = text.splitlines()
    if len(lines) > _CSV_PREVIEW_LINES:
        st.code("\n".join(lines[:_CSV_PREVIEW_LINES]), language="text")
        st.caption(f"…（全 {len(lines)} 行）")
    else:
        st.code(text, language="text")


def render_input_file_field(
    *,
    mode: str,
    spec: InputFieldSpec,
    presets: list[dict[str, Any]],
    files: dict[str, tuple[str, bytes, str]],
    data: dict[str, str],
) -> None:
    """1 入力フィールド分の「プリセット選択 / アップロード」UI。

    既定はプリセット選択・先頭プリセット。``allow_none`` のときだけ
    「使わない」を選択肢に加え、それを既定にする。
    """
    is_yaml = "yaml" in spec.upload_types or "yml" in spec.upload_types
    options = ["プリセット選択", "アップロード"]
    if spec.allow_none:
        options = ["使わない", *options]
    source = st.radio(spec.label, options, key=f"{mode}-{spec.field}-source")

    if source == "使わない":
        return

    if source == "プリセット選択":
        if not presets:
            st.warning(f"{spec.field} のプリセットがありません。")
            return
        selected = st.selectbox(
            f"{spec.field} プリセット",
            presets,
            format_func=lambda p: f"{p['name']} — {p['description']}",
            key=f"{mode}-{spec.field}-preset",
        )
        data[f"{spec.field}_preset"] = selected["name"]
        with st.expander("プリセットの中身"):
            render_preset_preview(selected["text"], is_yaml=is_yaml)
        return

    uploaded = st.file_uploader(
        spec.label, type=spec.upload_types, key=f"{mode}-{spec.field}-upload"
    )
    if uploaded is not None:
        files[spec.field] = (
            uploaded.name,
            uploaded.getvalue(),
            spec.content_type,
        )
