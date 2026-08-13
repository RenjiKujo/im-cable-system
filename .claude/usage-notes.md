# Claude Code 利用量メモ（人間用）

エージェントは読まない（`permissions.deny`）。CLAUDE.md から参照しない。
仕様は変わる。食い違ったら公式: https://claude.ai/settings/usage / https://code.claude.com/docs/en/costs

## 課金

Pro はサブスクのみ。枠切れでも自動従量はしない。上限は **5h セッション** と **週次**。
credits は自分でオンにしたときだけ追加課金。claude.ai と Claude Code は同じ枠。

残りは `/usage`。会話のコンテキスト % はプラン枠ではない。`/cost` は API 換算で請求額ではない。

## 抑える

1. 終わったら `/clear`。続きは `/rename` → `/resume`
2. 普段 Sonnet / effort `high`。Fable は Plan のみ。`/model` は **s（セッションのみ）**。Enter すると既定が変わる
3. Fable で Plan → 方針をファイルへ → `/clear` → Sonnet で実装。同じ会話でモデルを跨がない
4. プロンプトは狭く。パスで指す。巨大ログを貼らない
5. 区切りは `/clear` の方が `/compact` より安い

## このマシン

- `~/.claude/settings.json`: sonnet / high
- 権限は `.claude/settings.json`。hook・agents・skills の正本は `.cursor/`
- Claude から起動してよいスキルは `/pj-update-design-doc` のみ
- レビューは Opus（完了・PR 前）。docs 同期は Sonnet
