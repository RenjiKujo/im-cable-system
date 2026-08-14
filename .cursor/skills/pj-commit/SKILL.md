---
name: pj-commit
description: >-
  Stages selected files and creates one git commit. Does not push.
  Use only when the user explicitly asks to commit or invokes pj-commit.
disable-model-invocation: true
---

# pj-commit

未コミット差分からコミットを 1 つ作る。push しない。

1. `git status`、`git diff HEAD`、`git log --oneline -10` を取る
2. 含めるファイルだけ `git add` する。`git add -A` は使わない
3. `.env` / `secrets/` / `.claude/settings.local.json` は stage しない
4. `--no-verify` / `--no-gpg-sign` は使わない
5. メッセージは日本語、HEREDOC、why を 1–2 文。既存の commit log の粒度に合わせる
6. ユーザーがメッセージ案を出していればそれをヒントにする
7. コミット後に hash・変更ファイル数・`git status` を出して終わる
