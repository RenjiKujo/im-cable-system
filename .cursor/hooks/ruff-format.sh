#!/usr/bin/env bash
# Python 編集直後に、そのファイルだけ ruff format / check --fix する。
# 正本: .cursor/hooks/ （Cursor が本体）。Claude Code の PostToolUse からも同じスクリプトを呼ぶ。
# Cursor (afterFileEdit) と Claude Code (PostToolUse) の JSON を stdin から読む。
# 失敗しても編集自体は止めない（常に exit 0）。

set +e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 0

INPUT="$(cat)"

FILE_PATH="$(python3 -c '
import json, sys
raw = sys.stdin.read().strip()
if not raw:
    sys.exit(0)
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)
tool = data.get("tool_input") or {}
path = (
    tool.get("file_path")
    or tool.get("path")
    or data.get("file_path")
    or data.get("filePath")
    or data.get("path")
    or ""
)
if path:
    print(path)
' <<<"$INPUT")"

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi
if [[ "$FILE_PATH" != /* ]]; then
  FILE_PATH="$ROOT/$FILE_PATH"
fi
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

VENV_LINE="$(grep -m1 -v '^[[:space:]]*$' "$ROOT/.venv_path" 2>/dev/null || true)"
if [[ -z "$VENV_LINE" ]]; then
  echo "ruff-format.sh: .venv_path が無い。整形をスキップ" >&2
  exit 0
fi
if [[ "$VENV_LINE" != /* ]]; then
  VENV_DIR="$ROOT/$VENV_LINE"
else
  VENV_DIR="$VENV_LINE"
fi

if [[ -x "$VENV_DIR/bin/ruff" ]]; then
  RUFF="$VENV_DIR/bin/ruff"
elif [[ -x "$VENV_DIR/Scripts/ruff.exe" ]]; then
  RUFF="$VENV_DIR/Scripts/ruff.exe"
else
  echo "ruff-format.sh: venv に ruff が無い。整形をスキップ" >&2
  exit 0
fi

"$RUFF" format --config "$ROOT/ruff.toml" "$FILE_PATH" >/dev/null 2>&1
"$RUFF" check --fix --config "$ROOT/ruff.toml" "$FILE_PATH" >/dev/null 2>&1
exit 0
