# im-cable-system

誘導電動機（IM）＋ケーブル系の等価回路シミュレーション／パラメータ推定エンジン。
Cursor が本体。`.cursor/` が正本。このファイルは Claude Code 用の入口。
詳細は起動時に読まない。必要なときだけ Read する。

## Python 実行環境

正本: `.cursor/rules/virtual_env.mdc`。シェルを使う前に Read して従う。

## 設計思想

実装・設計変更の前に該当を Read する。ここに要約しない。

- 俯瞰・目次: `docs/README.md`
- 層・ディレクトリ: `docs/architecture/0_component.md`
- 設計原則: `docs/conventions/2_design_principles.md`
- 層・import: `docs/conventions/3_layering_and_imports.md`
- テスト: `docs/conventions/5_testing.md`
- 数値ガード: `docs/conventions/4_numerical_robustness.md`

## コード規約（ruff / pyright でカバーできないもの）

整形・lint・型の機械項目は `ruff.toml` と `pyproject.toml` の pyright に従う。
人手ルールは `docs/conventions/1_code_style.md`。Python を触る前に Read する。
機械強制とドキュメントの役割分担は `docs/conventions/README.md` の正本マップが正本。
機械強制できる値を docs へ再掲しない。

## Git

コミット・push・PR はユーザーが明示したときだけ。それ以外は `git commit` / `git push` しない。
実装後は `git status` と `git diff --stat` を出して止まる。
手順スキルの正本は `.cursor/skills/`。Git / テスト手順はここからは起動しない。
docs 同期だけ `/pj-update-design-doc` を許可する（`.claude/skills/` から正本への symlink）。

## 実装レビュー

正本は `.cursor/agents/`。タスク完了時と PR 作成前は `implementation-reviewer` を起動する。
レビューは直さず報告のみ。小さな編集のたびに呼ばない。
docs の機械同期は `design-doc-writer`（Sonnet）。
