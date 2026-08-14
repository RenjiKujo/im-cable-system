# hooks（このディレクトリはメモだけ）

Claude Code はここを読まない。登録は `.claude/settings.json` の `hooks`。
Cursor 側の登録は `.cursor/hooks.json`。

## 登録内容

| イベント | 実行するもの | Claude | Cursor |
|---|---|---|---|
| 編集直後（`PostToolUse` / `afterFileEdit`） | `.cursor/hooks/ruff-format.sh` | ✅ | ✅ |

`ruff-format.sh` の正本は `.cursor/hooks/`。両者の stdin JSON 形式の違いは
スクリプト側で吸収しているため、1 本を共用できる。
`.venv` が無い環境では何もせず終了する。

## 整合性チェックを hook に載せない理由

`pytest tests/test_docs/`（docs↔実装）と `basedpyright`（型）は **hook で自動化せず、
人が起動する**方針とした。手順の正本は `.cursor/rules/consistency_check.mdc`。

- **落ちても自動修正できない。** docs とコードのどちらが正かの判断が要るため、
  検出しても人の判断待ちになる。自動発火の利点が小さい。
- **作業途中の中間状態で偽の失敗が出る。** docs を先に書いて実装が後追いの局面では、
  毎ターン赤くなって意味を失う。
- `basedpyright` は約 30 秒かかり、毎ターン実行には重い。

最終ゲートは CI（`test` / `typecheck` ジョブ）が担う。
