# Feature Plan — Backend Subprocess Adapter (Phase 1)

Each group is independently implementable and verifiable. Commit by task group.

## Group 1 — Result and adapter shapes

1. Add `BackendResult` and `BackendAdapter` shapes to `models.py` (per
   `docs/backend-adapters.md`), including the `supports_structured` field and the
   `run(prompt, *, cwd, env) -> BackendResult` signature.
2. Add a `_subprocess_backend_adapter(backend, cmd_builder)` factory (shared) that builds a
   subprocess adapter with `supports_structured=False` for a given backend and command builder.

## Group 2 — Registry and handoff

3. Build `BACKEND_ADAPTERS: dict[str, BackendAdapter]` keyed by `BACKEND_CHOICES`, using the shared
   factory so the four backend branches do not repeat ≥ 6 similar lines (R0801).
4. Rewrite `open_backend_session` to look up the adapter, run it, and return its `exit_code`,
   preserving the exact signature and the `sanitize_env` path.

## Group 3 — Verification

5. Confirm `tests/test_backends.py` passes unchanged (behavior is identical).
6. Run the full gate: `ruff check/format`, `pylint --fail-under=8.0`, `pytest -q -x`, then
   `act -j lint`.

## Standing constraints (apply to every group)

- No duplicated block of ≥ 6 similar lines across modules (pylint R0801) — shared command/env
  logic lives in one helper.
- `pylint src/ghostgrid/ --fail-under=8.0` stays green.
