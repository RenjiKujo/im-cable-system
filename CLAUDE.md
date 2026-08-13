# im-cable-system

誘導電動機（IM）＋ケーブル系の等価回路シミュレーション／パラメータ推定エンジン。
詳細は起動時に読まない。必要なときだけ Read する。

## Python 実行環境

1. ルートの `.venv_path` を読む（先頭の非空行。相対パスはルート基準）。
2. ある → その venv の `bin/python` / `bin/pip` 等（Windows は `Scripts\`）だけ使う。
3. 無い／壊れている → activate も作成もせず、報告して確認を待つ。
4. 禁止: venv 新規作成、素の `python`/`pip`、`pip install --user`、グローバル領域、`.venv` の推測。

## 設計思想

実装・設計変更の前に該当を Read する。ここに要約しない。

- 俯瞰: `docs/overview.md`
- 層・ディレクトリ: `docs/architecture/0_component.md`
- 設計原則: `docs/rules/design_principles.md`
- 層・import: `docs/rules/layering_and_imports.md`
- テスト: `docs/rules/testing.md`
- 数値ガード: `docs/rules/numerical_robustness.md`

## コード規約（ruff / pyright でカバーできないもの）

整形・lint・型の機械項目は `ruff.toml` と `pyproject.toml` の pyright に従う。
人手ルールは `docs/rules/coding_style.md`。Python を触る前に Read する。

## 実装レビュー

- 依存は `pipeline → processor → algorithm → domain → shared` のみか
- 境界超え import は公開窓口経由か
- 数値ガード（`eps` / `max_mag`）を新設していないか
- テストは公開窓口からか（内部テストなら docstring に明記）
- コメント・型を消していないか
