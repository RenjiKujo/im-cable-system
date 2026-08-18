---
name: pj-push-pr
description: >-
  Pushes an already-committed branch and creates a GitHub pull request. Does not commit.
  Use when the user asks to push and open a PR for existing commits.
disable-model-invocation: true
---

# pj-push-pr

1. **レビューの締め**（`.cursor/rules/consistency_check.mdc` の節 2）。PR 作成は作業単位の
   区切りなので、ここが諮問のタイミングになる。未レビューなら推奨と理由を添えて諮り、
   レビュー済みなら **要修正** が残っていないか確認する
2. `git status` を見る。未コミット変更があればコミットせず、ユーザーに確認して止まる
3. `git diff origin/main...HEAD` と `git log --oneline origin/main..HEAD` を見て PR 本文を書く
4. `git push -u origin <current_branch>` する。`--force` は使わない
5. `gh pr create` する。タイトルは日本語。ベースは `main`。判断できなければ確認して止まる
6. PR URL を返す

## PR 本文テンプレ

```markdown
## 概要


## 変更内容


## テスト
- [ ] `.venv_path` の python で `pytest -m "not slow" -q`
- [ ] `ruff check src tests`
- [ ] `basedpyright`
```
