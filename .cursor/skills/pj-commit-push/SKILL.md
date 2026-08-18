---
name: pj-commit-push
description: >-
  Creates one commit then pushes the current branch to origin. Does not open a PR.
  Use only when the user explicitly asks to commit and push or invokes pj-commit-push.
disable-model-invocation: true
---

# pj-commit-push

1. **レビューの締め**（`.cursor/rules/consistency_check.mdc` の節 2）。未レビューなら推奨と
   理由を添えて諮り、レビュー済みなら **要修正** が残っていないか確認する。
   コミットする変更が無いときも、push 対象の変更についてこの確認を行う
2. `pj-commit` の手順 2 以降でコミットする（未コミットが無ければスキップし、その旨を書く）
3. `git branch --show-current` を確認する。`main` への直接 push なら一度確認する
4. `git push -u origin <current_branch>` する。`--force` は使わない
5. PR は作らない。push 先と最新 hash を報告する

`.env` / `secrets/` / `.claude/settings.local.json` は stage しない。
