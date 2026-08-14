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
`git mv` / `git rm` は rename 追跡に必要なため index に載ってよい。
手順スキルの正本は `.cursor/skills/`。Git / テストの**手順**をここに書かない
（下記「整合性チェック」の締め処理だけは例外。手順ではなく必須の確認のため）。
docs 同期だけ `/pj-update-design-doc` を許可する（`.claude/skills/` から正本への symlink）。

## エージェント

正本は `.cursor/agents/`（`.claude/agents/` は symlink）。3 体とも報告のみで、直さない。
モデルは各 frontmatter が正本（設計判断は opus、機械的な照合は sonnet）。

| エージェント | 見るもの | 諮るタイミング |
|---|---|---|
| `implementation-reviewer` | 差分 → docs（層・公開窓口・DTO / Factory 契約・数値ガード） | `src/` を編集したターンの締め |
| `docs-consistency-checker` | docs → 実装（陳腐化した設計判断・正本と再掲のドリフト） | `docs/` を編集したターンの締め |
| `design-doc-writer` | コードを読んで docs を書く | docs 更新が必要なとき |

**実行はユーザーの承認による。** 環境によっては起動できないので、その場合は提案に
とどめ、起動できなかった事実を報告に書く。

## 整合性チェック

**正本: `.cursor/rules/consistency_check.mdc`**（`docs/` か `src/` を編集したターンの
締め方。機械チェックの実行と、レビューエージェントを諮る手順）。編集する前に Read して従う。

CI で確認するテストは `tests/` に一本化する。`tests/test_docs/` の外に整合性
チェック用のスクリプトを置かない（二重管理はそれ自体が drift 源になる）。

### テストの更新義務

**実装・docs を変えたら、対応するテストも同じ変更で更新する。**
テストを消して通さない。落ちたまま報告を終えない。
`model_equations/` は `TestModelEquationsCoverage` がテスト自身の更新漏れも検出する。

### 自動修正はしない

「docs とコードのどちらが正しいか」の判断を要するため（`design-doc-writer` の
「思想を変えない。警告する」と同じ理由）。`design-doc-writer` は Bash を持たないので、
その実行後は呼び出し側が上記 pytest を回す。
