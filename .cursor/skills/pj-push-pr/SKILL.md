---
name: pj-push-pr
description: >-
  Pushes an already-committed branch and creates a GitHub pull request. Does not commit.
  Use when the user asks to push and open a PR for existing commits.
disable-model-invocation: true
---

# pj-push-pr

1. `git status` を見る。未コミット変更があればコミットせず、ユーザーに確認して止まる
2. `git diff origin/main...HEAD` と `git log --oneline origin/main..HEAD` を見て PR 本文を書く
3. `git push -u origin <current_branch>` する。`--force` は使わない
4. `gh pr create` する。タイトルは日本語。ベースは `main`。判断できなければ確認して止まる
5. PR URL を返す

## PR 本文テンプレ

```markdown
## 概要


## 変更内容


## テスト
- [ ] `.venv_path` の python で `pytest -m "not slow" -q`
- [ ] `ruff check src tests`
- [ ] `basedpyright`
```
