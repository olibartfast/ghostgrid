#!/usr/bin/env bash
# .claude/hooks/block_secrets.sh
#
# PreToolUse hook for Bash.
#
# ghostgrid handles a lot of provider API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY,
# TOGETHER_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY,
# CEREBRAS_API_KEY, AZURE_OPENAI_API_KEY). If any of these leak into a commit,
# it's not a CI failure — it's a security incident that also takes a while to
# unwind. This hook pre-empts that by scanning:
#
#   1. the command itself (e.g. `echo OPENAI_API_KEY=sk-... > .env` → deny)
#   2. the staging area if the command is `git commit` (scan git diff --cached)
#
# Blocks by exiting 2 with an explanatory message.

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

[[ -z "$command" ]] && exit 0

# Patterns for likely secrets. Keep this tight to avoid false positives on
# things like the literal string "OPENAI_API_KEY" in docs/examples.
#
# We match "KEY=<something that isn't empty or obviously a placeholder>"
# and the common prefixes for real keys.
SECRET_RE='(OPENAI_API_KEY|ANTHROPIC_API_KEY|TOGETHER_API_KEY|GOOGLE_API_KEY|GROQ_API_KEY|MISTRAL_API_KEY|CEREBRAS_API_KEY|AZURE_OPENAI_API_KEY)[[:space:]]*=[[:space:]]*["'\'']?(sk-[A-Za-z0-9_-]{10,}|sk-ant-[A-Za-z0-9_-]{10,}|AIza[A-Za-z0-9_-]{20,}|tgp_[A-Za-z0-9_-]{10,}|gsk_[A-Za-z0-9_-]{10,})'

# 1. Scan the command string itself.
if printf '%s' "$command" | grep -qE "$SECRET_RE"; then
  {
    echo "[block_secrets] refused: command appears to contain a live API key."
    echo "Use a .env file (gitignored) or the shell environment, never inline."
  } >&2
  exit 2
fi

# 2. For `git commit` specifically, scan what's staged.
if [[ "$command" == *"git commit"* ]] && command -v git >/dev/null 2>&1; then
  if staged="$(git diff --cached 2>/dev/null)"; then
    if printf '%s' "$staged" | grep -qE "$SECRET_RE"; then
      {
        echo "[block_secrets] refused: staged changes contain a live API key."
        echo "Run:  git restore --staged <file>  and scrub before re-staging."
      } >&2
      exit 2
    fi
    # Also catch .env being committed, which is the more common accident.
    if git diff --cached --name-only 2>/dev/null | grep -qE '(^|/)\.env$'; then
      {
        echo "[block_secrets] refused: .env is staged for commit."
        echo "Add '.env' to .gitignore and run: git rm --cached .env"
      } >&2
      exit 2
    fi
  fi
fi

exit 0
