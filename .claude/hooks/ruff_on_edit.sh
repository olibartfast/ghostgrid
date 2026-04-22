#!/usr/bin/env bash
# .claude/hooks/ruff_on_edit.sh
#
# PostToolUse hook for Edit/Write/MultiEdit.
#
# Reads the tool payload from stdin, pulls the edited file path, and, if it's
# a Python file under src/ or tests/, runs:
#   ruff check --fix --exit-zero <file>
#   ruff format <file>
#
# Then runs a non-mutating `ruff check <file>` that DOES fail the hook if any
# unfixable issues remain. This is the single biggest source of recurring CI
# breakage — CI run #13 was literally titled
# "fix: resolve ruff lint errors (I001, F401, F841, C408) in tests".
#
# Exits:
#   0 → all good, continue
#   2 → block the tool and surface the ruff output back to Claude so it fixes it

set -euo pipefail

payload="$(cat)"

# Extract the file_path from the tool input. Works for Edit, Write, MultiEdit.
file_path="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tool = data.get("tool_input", {})
# Edit/Write use file_path; MultiEdit uses file_path too (single file, many edits).
fp = tool.get("file_path") or ""
print(fp)
' 2>/dev/null || true)"

# Nothing to lint — bail quietly.
[[ -z "$file_path" ]] && exit 0
[[ "$file_path" != *.py ]] && exit 0
[[ ! -f "$file_path" ]] && exit 0

# Only lint files that CI would lint.
case "$file_path" in
  src/*|tests/*|examples/*) ;;
  *) exit 0 ;;
esac

# ruff may not be installed in the sandbox yet — don't block the agent on that.
if ! command -v ruff >/dev/null 2>&1; then
  echo "[ruff_on_edit] ruff not installed; skipping (run 'pip install -e .[dev]')" >&2
  exit 0
fi

# 1. Autofix what can be autofixed, silently.
ruff check --fix --exit-zero "$file_path" >/dev/null
ruff format "$file_path" >/dev/null

# 2. Strict check — anything left blocks the turn and is reported back to Claude.
if ! ruff_out="$(ruff check --output-format=concise "$file_path" 2>&1)"; then
  {
    echo "ruff found issues in $file_path that require manual fixes:"
    echo
    echo "$ruff_out"
    echo
    echo "Consult .claude/skills/ci-guardian/SKILL.md for the common fixes"
    echo "(I001, F401, F841, C408, E501, UP*, B*, SIM*)."
  } >&2
  exit 2
fi

exit 0
