---
name: pj-commit
description: >-
  Stages selected files and creates one git commit. Does not push.
  Use only when the user explicitly asks to commit or invokes pj-commit.
disable-model-invocation: true
---

# pj-commit

未コミット差分からコミットを 1 つ作る。push しない。

1. **レビューの締め**（`.cursor/rules/consistency_check.mdc` の節 2）。コミットは作業単位の
   区切りなので、ここが諮問のタイミングになる。
   - この変更をまだレビューに掛けていなければ、推奨と理由を添えてユーザーに諮る
   - 既にレビュー済みなら、報告の **要修正** が残っていないか確認する。
     直すか、直さない理由を書き残すかのどちらかを済ませてからコミットする
   - レビューを見送るのはユーザーの判断でよい。その事実を報告に 1 行書く
2. `git status`、`git diff HEAD`、`git log --oneline -10` を取る
3. 含めるファイルだけ `git add` する。`git add -A` は使わない
4. `.env` / `secrets/` / `.claude/settings.local.json` は stage しない
5. `--no-verify` / `--no-gpg-sign` は使わない
6. メッセージは日本語、HEREDOC、why を 1–2 文。既存の commit log の粒度に合わせる
7. ユーザーがメッセージ案を出していればそれをヒントにする
8. コミット後に hash・変更ファイル数・`git status` を出して終わる
