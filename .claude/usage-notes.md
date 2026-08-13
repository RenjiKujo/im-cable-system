# Claude Code 利用量メモ（人間用）

Claude / Cursor Agent は読まない。
`.claude/settings.json` と `~/.claude/settings.json` の `permissions.deny` で
`Read(.claude/usage-notes.md)` を禁止している。CLAUDE.md や `.claude/rules/` から
参照しないこと。

個人の Pro 運用メモ。課金・枠の仕様は変わるので、食い違ったら公式を優先する。

- プラン枠: https://claude.ai/settings/usage
- 公式: https://code.claude.com/docs/en/costs

## 課金の前提

- Pro 本体は月額サブスクのみ。枠を使い切っても **自動では従量課金されない**（待たされる）。
- 上限は **5時間セッション** と **週次**。included の月次上限は無い。
- 追加課金は **Usage credits を自分でオンにしたときだけ**。オフなら追加請求なし。
- claude.ai チャットと Claude Code は同じ枠。

## 調べる

| 見たいもの | 方法 |
|---|---|
| 5h / 週次の残り・リセット | `/usage`、または https://claude.ai/settings/usage |
| 作業中に常時 | Claude Code の statusline（`rate_limits`）。未設定なら後で足す |
| 今の会話の埋まり | プロンプト横のバー、`/context`。これは **プラン枠ではない** |
| セッションの $ 概算 | `/cost`。API 換算。Pro の請求額ではない |
| Usage credits の今月 | Settings > Usage の credits 欄。オフなら無視 |

「そろそろ上限」= `/usage` の 5h / Week バー。コンテキスト % を見ない。

## 抑える（効く順）

1. タスクが終わったら `/clear`。無関係な履歴を残さない。続きは `/rename` → `/resume`。
2. 普段は Sonnet。Fable は Plan のときだけ。`/model` は **s（このセッションのみ）**。Enter すると既定が上書きされる。
3. 設計は Fable + Plan → 方針をファイルに残す → `/clear` → Sonnet で実装。同じ長い会話で Fable→Sonnet しない。
4. Effort は普段 `high`。Fable の Plan だけその場で `/effort xhigh`。`max` / ultracode は使わない。
5. プロンプトを狭くする。ファイルはパスで指す。巨大ログを貼らない。
6. 使わない MCP / claude.ai connectors は切る（`disableClaudeAiConnectors`）。
7. 区切りで `/compact`。auto-compact 待ちより自分で区切る。compact 自体もリクエストなので、終わった作業は `/clear` の方が安い。

## このマシンの設定

- 個人: `~/.claude/settings.json`  
  `model: sonnet`, `effortLevel: high`, `alwaysThinkingEnabled: false`,
  `autoCompactEnabled: true`, `disableClaudeAiConnectors: true`
- このリポジトリ: `.claude/settings.json`（権限のみ。`.env` 拒否、`git push` / `pip install` は確認）

## やらなくてよいこと

- `MAX_THINKING_TOKENS` を設定する（Sonnet 5 / Fable では effort が本命）
- 月次トークン上限を settings に書く（項目が無い）
- このメモを CLAUDE.md に `@` で取り込む（毎ターンの固定コストになる）
