---
name: pj-commit-push
description: >-
  Creates one commit then pushes the current branch to origin. Does not open a PR.
  Use only when the user explicitly asks to commit and push or invokes pj-commit-push.
disable-model-invocation: true
---

# pj-commit-push

1. `pj-commit` と同じ手順でコミットする（未コミットが無ければスキップし、その旨を書く）
2. `git branch --show-current` を確認する。`main` への直接 push なら一度確認する
3. `git push -u origin <current_branch>` する。`--force` は使わない
4. PR は作らない。push 先と最新 hash を報告する

`.env` / `secrets/` / `.claude/settings.local.json` は stage しない。
