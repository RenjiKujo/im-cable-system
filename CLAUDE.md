# im-cable-system

誘導電動機（IM）＋ケーブル系の等価回路シミュレーション／パラメータ推定エンジン。
Cursor が本体。`.cursor/` が正本。このファイルは Claude Code 用の入口。
詳細は起動時に読まない。必要なときだけ Read する。

## 基本原則

- 記述が食い違ったら、**正本宣言のある側を正**とする。正本が不明なものは推測で直さず確認する。
  各 architecture 文書は冒頭の「この文書が正本である範囲」ブロックを見てから読む。
- **読んだ範囲だけを評価する。** 部分的にしか読んでいないファイル・ディレクトリを
  「問題なし」「健全」と報告しない。未読・部分読みなら「未確認」と明示する。

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

コミット・push・PR・**staging** はユーザーが明示したときだけ。
それ以外は `git commit` / `git push` / `git add` しない
（`git add` はユーザーの未コミット変更を巻き込むため。diff を見せるだけなら不要）。
実装後は `git status` と `git diff --stat` を出して止まる。
`git mv` / `git rm` は結果が index に載るが、rename 追跡に必要なためそのままでよい。
手順スキルの正本は `.cursor/skills/`。Git / テスト手順はここからは起動しない。
docs 同期だけ `/pj-update-design-doc` を許可する（`.claude/skills/` から正本への symlink）。

## エージェント

正本は `.cursor/agents/`（`.claude/agents/` は symlink）。3 体とも報告のみで、直さない。

| エージェント | 役割 | 起動タイミング |
|---|---|---|
| `implementation-reviewer` | 差分を docs に照らしてレビュー | タスク完了時・PR 作成前 |
| `docs-consistency-checker` | docs 側を実装に照らして検査 | PR 前・大きな docs リファクタ後 |
| `design-doc-writer` | コードを読んで docs を書く | docs 更新が必要なとき |

いずれも**起動を提案する**。実行はユーザーの承認による
（環境によっては明示要求がないとエージェントを起動できない。その場合は提案にとどめ、
起動できなかった事実を報告に書く）。毎タスク・小さな編集のたびには呼ばない。

モデルは各 `.cursor/agents/*.md` の frontmatter が正本（現状: reviewer / writer は opus、
consistency-checker は sonnet）。設計判断を伴うものは opus、機械的な照合が主体のものは
sonnet、という基準。合わなければ frontmatter を変える。

## docs 整合性チェック

機械チェックはエージェント不要で即時実行できる。docs を編集したら回す。

```bash
.venv/bin/python scripts/check_docs_consistency.py
```

検出するのは 4 種（リンク切れ・パス実在・ディレクトリツリー整合・識別子実在）。
`design-doc-writer` は Bash を持たないため、**その実行後は必ず呼び出し側がこれを回す**。
意味的な矛盾（陳腐化した設計判断・正本と再掲のドリフト）はスクリプトでは取れないため、
`docs-consistency-checker` が担当する（`docs/conventions/` は対象外）。
