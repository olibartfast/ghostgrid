# Feature Validation — Model-API Capture Adapter (Phase 2a)

## Automated

- [ ] `ruff check src/ tests/ && ruff format --check src/ tests/` exits 0
- [ ] `pylint src/ghostgrid/ --fail-under=8.0` passes (score ≥ 8.0)
- [ ] No pylint R0801 duplicate-code fires across modules
- [ ] `pytest tests/test_backends.py -q` passes **unchanged**
- [ ] `pytest tests/test_capture.py -q` passes: token rejection (`401`), unknown path (`404`),
      header redaction, streamed + non-streamed recording for all three dialects, upstream non-2xx
      surfaced in `BackendResult.error`
- [ ] Each assembler fixture yields the expected `text` and `tool_calls`
- [ ] `pytest tests/ -q -x` (full regression) passes on Python 3.10, 3.11, 3.12
- [ ] `pyproject.toml` runtime dependencies unchanged (`requests`, `Pillow` only)
- [ ] `act -j lint` passes

## Manual

- [ ] `ghostgrid run --agent-backend claude-code --backend-capture --prompt "..."` opens the normal
      interactive session; streaming feels unchanged; on exit, JSON with non-empty `content` and
      ordered `tool_events` is printed
- [ ] Same walkthrough for `codex` and `opencode`
- [ ] `--agent-backend pi --backend-capture` exits non-zero with a JSON error (until Open Question 1
      is resolved)
- [ ] Without `--backend-capture`, all four backends behave exactly as before
- [ ] The launched subprocess env contains no real provider key — only the session token
- [ ] `--capture-out trace.jsonl` contains no `Authorization` / `x-api-key` / key-or-token headers
- [ ] The `opencode` temp config is removed after the session, including on Ctrl-C; no file is
      written under `$HOME`

## Definition of Done

- [ ] Group 0 findings recorded in the wiring table in `requirements.md`
- [ ] `BackendResult` and `BackendAdapter` shapes unchanged
- [ ] Spec, code, `docs/backend-adapters.md`, `tech-stack.md` and `roadmap.md` agree
