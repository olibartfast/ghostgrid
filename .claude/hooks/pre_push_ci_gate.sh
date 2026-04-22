#!/usr/bin/env bash
# .claude/hooks/pre_push_ci_gate.sh
#
# PreToolUse hook for Bash. If Claude is about to run `git push`, we first run
# the exact same gate that .github/workflows/ci.yml runs, on the host. If it
# fails, we block the push and hand the output back to Claude.
#
# This turns the slow loop (push → wait 30-60s → CI red → fix → repeat) into
# an instant one, which is the whole point of this kit.
#
# The commands here MUST stay in sync with .github/workflows/ci.yml.

set -euo pipefail

payload="$(cat)"

command="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(data.get("tool_input", {}).get("command", ""))
' 2>/dev/null || true)"

# Only intercept `git push`. Leave everything else alone.
case "$command" in
  *"git push"*) ;;
  *) exit 0 ;;
esac

# Skip the gate entirely if the user explicitly opts out. Respect their choice.
if [[ "$command" == *"--no-verify"* ]] || [[ "${GHOSTGRID_SKIP_CI_GATE:-}" == "1" ]]; then
  echo "[pre_push_ci_gate] opt-out detected; skipping local CI gate" >&2
  exit 0
fi

echo "[pre_push_ci_gate] running local CI gate before push..." >&2

fail() {
  {
    echo
    echo "============================================================"
    echo "  LOCAL CI GATE FAILED — push blocked"
    echo "============================================================"
    echo "$1"
    echo
    echo "Fix the above, then retry the push."
    echo "To bypass (not recommended): GHOSTGRID_SKIP_CI_GATE=1 git push ..."
    echo "or:                          git push --no-verify ..."
  } >&2
  exit 2
}

# Mirrors the lint job in ci.yml.
if command -v ruff >/dev/null 2>&1; then
  if ! ruff_out="$(ruff check src/ tests/ --output-format=concise 2>&1)"; then
    fail "ruff check failed:
$ruff_out"
  fi
  if ! fmt_out="$(ruff format --check src/ tests/ 2>&1)"; then
    fail "ruff format --check failed (run 'ruff format src/ tests/'):
$fmt_out"
  fi
else
  echo "[pre_push_ci_gate] warning: ruff not installed, skipping ruff stage" >&2
fi

# Mirrors pylint --fail-under=8.0 from ci.yml. This is the one that caught
# OpenCV no-member and R0801 duplicate-code in the past.
if command -v pylint >/dev/null 2>&1; then
  if ! pl_out="$(pylint src/ghostgrid/ --fail-under=8.0 2>&1)"; then
    fail "pylint --fail-under=8.0 failed:
$pl_out

See .claude/skills/ci-guardian/SKILL.md §R0801 and §OpenCV for catalogued fixes."
  fi
else
  echo "[pre_push_ci_gate] warning: pylint not installed, skipping pylint stage" >&2
fi

# Mirrors pytest from ci.yml. Fast path only (no coverage, no --slow).
if command -v pytest >/dev/null 2>&1; then
  if ! pt_out="$(pytest tests/ -q --no-header -x 2>&1)"; then
    fail "pytest failed:
$pt_out"
  fi
else
  echo "[pre_push_ci_gate] warning: pytest not installed, skipping test stage" >&2
fi

echo "[pre_push_ci_gate] OK — local CI gate passed, allowing push" >&2
exit 0
