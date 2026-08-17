"""slip 軸図（左）と出力比軸図（右）を 1 枚へ横並び合成するスクリプト。

README へ「slip 横軸（左）」「出力比横軸（右）」を 1 枚で並べて載せるための
合成器。指定ディレクトリにある ``fig_slip_axis_*.png`` と
``fig_output_ratio_axis_*.png`` のうち、``--name-contains`` を含む最新の
PNG を読み込み、高さを揃えて左右に連結し保存する。

ForwardByCartesianGrid・EstimateParams のどちらの出力にも使える。
EstimateParams のように 1 回の実行で複数候補の図が出る場合は、
``--name-contains`` で候補（例: ``_2_2_2_0_0_0``）を 1 つに絞る。

合成のみを行い、図そのものはパイプライン（runner）が生成した PNG を入力と
する。入力 CSV・config を差し替えて runner を実行し直せば、本スクリプトの
再実行だけで README 図を更新できる。

使い方::

    .venv/bin/python scripts/combine_axis_figures.py \\
        --figures-dir examples/outputs/forward_by_cartesian_grid/figures \\
        --output docs/assets/forward_basic01_vs_currentdependent03.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from im_cable_system.engine.shared.config import Config, Logger

# README 表示向けの合成後の横幅 [px]（GitHub 表示の軽量化）。
_TARGET_WIDTH_PX = 1600

# 左右の図の間に挟む余白 [px]。
_GAP_PX = 24


def _repo_root() -> Path:
    """リポジトリルート（``scripts/`` の親）。"""
    return Path(__file__).resolve().parents[1]


def _default_figures_dir() -> Path:
    """デモ実行の Forward 図出力ディレクトリ。"""
    return (
        _repo_root()
        / "examples"
        / "outputs"
        / "forward_by_cartesian_grid"
        / "figures"
    )


def _default_output_path() -> Path:
    """合成図の保存先（README 参照パス）。"""
    return (
        _repo_root()
        / "docs"
        / "assets"
        / "forward_basic01_vs_currentdependent03.png"
    )


def _latest_matching_png(figures_dir: Path, *needles: str) -> Path:
    """``needles`` をすべて名前に含む最新の PNG を返す。

    Args:
        figures_dir: PNG を探索するディレクトリ。
        needles: ファイル名にすべて含まれるべき部分文字列。

    Returns:
        Path: 条件に合う最新（更新時刻が最大）の PNG パス。

    Raises:
        FileNotFoundError: 条件に合う PNG が存在しない場合。
    """
    candidates = [
        png
        for png in figures_dir.glob("*.png")
        if all(needle in png.name for needle in needles)
    ]
    if not candidates:
        raise FileNotFoundError(
            f"条件に合う PNG が見つかりません: needles={needles!r}, "
            f"dir={figures_dir}"
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _combine_side_by_side(left: Path, right: Path, dst: Path) -> None:
    """2 つの PNG を高さを揃えて左右に連結し ``dst`` へ保存する。

    Args:
        left: 左側に配置する PNG（slip 横軸）。
        right: 右側に配置する PNG（出力比横軸）。
        dst: 合成図の保存先。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    with (
        Image.open(left) as left_image,
        Image.open(right) as right_image,
    ):
        left_rgba = left_image.convert("RGBA")
        right_rgba = right_image.convert("RGBA")
        height = max(left_rgba.height, right_rgba.height)
        left_resized = _resize_to_height(left_rgba, height)
        right_resized = _resize_to_height(right_rgba, height)
        total_width = left_resized.width + _GAP_PX + right_resized.width
        canvas = Image.new("RGBA", (total_width, height), (255, 255, 255, 255))
        canvas.paste(left_resized, (0, 0))
        canvas.paste(right_resized, (left_resized.width + _GAP_PX, 0))
        merged = _downscale_to_width(canvas, _TARGET_WIDTH_PX)
        merged.convert("RGB").save(dst, optimize=True)


def _resize_to_height(image: Image.Image, height_px: int) -> Image.Image:
    """アスペクト比を保ったまま指定の高さへ拡縮する。"""
    if image.height == height_px:
        return image
    width_px = round(image.width * height_px / image.height)
    return image.resize((width_px, height_px), Image.LANCZOS)


def _downscale_to_width(image: Image.Image, width_px: int) -> Image.Image:
    """指定の横幅以下へ縮小する（拡大はしない）。"""
    if image.width <= width_px:
        return image
    height_px = round(image.height * width_px / image.width)
    return image.resize((width_px, height_px), Image.LANCZOS)


def _parse_args() -> argparse.Namespace:
    """コマンドライン引数を解釈する。"""
    parser = argparse.ArgumentParser(
        description=("slip 軸図（左）と出力比軸図（右）を 1 枚に合成する。"),
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=_default_figures_dir(),
        help="入力 PNG が置かれたディレクトリ。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_output_path(),
        help="合成図の保存先パス。",
    )
    parser.add_argument(
        "--name-contains",
        type=str,
        default="",
        help=(
            "対象 PNG をさらに絞り込む部分文字列（候補識別など）。"
            "複数候補がある EstimateParams では必須に近い。"
        ),
    )
    return parser.parse_args()


def main() -> int:
    """slip 軸図（左）と出力比軸図（右）を合成して保存する。"""
    args = _parse_args()
    logger = Logger.create(Config.create(config_file_path=None))
    figures_dir = args.figures_dir
    name_filter = args.name_contains
    slip_png = _latest_matching_png(
        figures_dir,
        "fig_slip_axis_",
        name_filter,
    )
    output_ratio_png = _latest_matching_png(
        figures_dir,
        "fig_output_ratio_axis_",
        name_filter,
    )
    _combine_side_by_side(slip_png, output_ratio_png, args.output)
    logger.info("combined README figure saved: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
