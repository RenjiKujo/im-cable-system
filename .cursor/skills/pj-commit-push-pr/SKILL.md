---
name: pj-commit-push-pr
description: >-
  Commits, pushes, and creates a GitHub pull request with gh.
  Use only when the user explicitly asks to commit, push, and open a PR.
disable-model-invocation: true
---

# pj-commit-push-pr

1. **レビューの締め**（`.cursor/rules/consistency_check.mdc` の節 2）。PR 作成は作業単位の
   区切りなので、未レビューなら推奨と理由を添えて諮り、レビュー済みなら **要修正** が
   残っていないか確認する
2. 未コミットがあれば `pj-commit` の手順 2 以降でコミットする
3. `git push -u origin <current_branch>` する。`--force` は使わない
4. `gh pr create` で PR を作る。対話プロンプトは使わない
   - タイトルは日本語
   - ベースは `main`。判断できなければユーザーに確認して止まる
   - 本文は次の固定テンプレ
5. PR URL を返す

`gh` が無い・認証できないならそこで止まり、代替手順を書かない。

## PR 本文テンプレ

```markdown
## 概要


## 変更内容


## テスト
- [ ] `.venv_path` の python で `pytest -m "not slow" -q`
- [ ] `ruff check src tests`
- [ ] `basedpyright`
```
