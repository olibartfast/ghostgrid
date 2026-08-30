# Feature Validation — Backend Subprocess Adapter (Phase 1)

## Automated

- [ ] `ruff check src/ tests/ && ruff format --check src/ tests/` exits 0
- [ ] `pylint src/ghostgrid/ --fail-under=8.0` passes (score ≥ 8.0)
- [ ] No pylint R0801 duplicate-code fires across modules
- [ ] `pytest tests/test_backends.py -q` passes **unchanged** (no test edits required)
- [ ] `pytest tests/ -q -x` (full regression) passes
- [ ] `mypy src/ || true` introduces no new advisory errors
- [ ] `act -j lint` passes

## Manual

- [ ] `ghostgrid run --agent-backend claude-code --prompt "..."` still opens an interactive
      session and inherits the terminal
- [ ] Same walkthrough for `codex`, `opencode`, and `pi`
- [ ] Unknown backend (`--agent-backend nope`) still reports the error as JSON and exits non-zero
- [ ] Credential env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …) are still redacted from the
      launched subprocess environment (verify `sanitize_env` path)

## Definition of Done

- [ ] `open_backend_session` signature and behavior are unchanged from `tests/test_backends.py`'s
      expectations
- [ ] The four backend branches share one command/env helper (no ≥ 6-line duplication)
- [ ] Spec, code, roadmap, and changelog agree (this packet matches `roadmap.md` Phase 1)
