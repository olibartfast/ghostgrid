# Feature Requirements — Backend Subprocess Adapter (Phase 1)

## Goal

Move the current `subprocess.run` backend handoff in `src/ghostgrid/backends.py` behind the
`BackendAdapter` contract defined in `docs/backend-adapters.md`, with **zero observable behavior
change**.

## In Scope

- A `BackendAdapter` shape with `name`, `supports_structured`, and
  `run(prompt, *, cwd, env) -> BackendResult` for each of `claude-code`, `codex`, `opencode`, `pi`.
- A `BackendResult` shape with `content`, `error`, `exit_code`, `latency_ms`, `tool_events`,
  `structured`.
- A `BACKEND_ADAPTERS` registry keyed by `BACKEND_CHOICES`.
- `open_backend_session(backend, prompt, cwd, env, sanitize)` keeps its exact signature and returns
  the adapter's `exit_code`.
- `sanitize_env` and the per-backend command mapping (`_BACKEND_CMDS`) are preserved.

## Out of Scope

- ACP transport for any backend (Phase 2).
- `supports_structured=True` for any backend in this phase — all four are
  `supports_structured=False`, exit-code-only subprocess adapters.
- Workflow integration of backends via `AgentResult` (Phase 4).
- Any change to `cli.py`'s `--agent-backend` short-circuit behavior.

## Decisions

- **Keep `subprocess` as the transport.** No protocol layer is introduced in this phase; the only
  goal is to put the existing launch behind the contract.
- **Extract shared command/env helpers** rather than repeating the per-backend `subprocess.run`
  boilerplate four times. This satisfies the R0801 constraint (no duplicated ≥ 6-line block) and
  gives later phases one place to hang framing/redaction logic.
- **`BackendResult.exit_code` is `None` when a transport exposes none** — subprocess adapters always
  set it; this leaves room for ACP (Phase 2) without changing the shape.
- **Shapes live in `models.py`** — `BackendResult` and `BackendAdapter` are dataclasses in
  `models.py`, beside `AgentResult` (which `BackendResult` maps into in Phase 4). `backends.py`
  keeps dispatch, the `_subprocess_backend_adapter` factory, and the `BACKEND_ADAPTERS` registry.
- **`BackendAdapter` is a dataclass** — fields `name: str`, `supports_structured: bool`, and
  `run: Callable[[str | None, str | None, dict[str, str] | None], BackendResult]`. This matches the
  `models.py` dataclass convention and keeps the factory trivial.
- **`run()` receives a pre-merged, pre-sanitized env** — `sanitize_env` and the `sanitize` flag are
  `open_backend_session`'s concern. The adapter's `run(prompt, *, cwd, env)` is handed a fully
  resolved `env` (a dict, or `None` to inherit the parent) and must pass it through to
  `subprocess.run(..., env=env)` unchanged.
- **Subprocess result field defaults** — the subprocess adapter sets `content=""`, `error=None`,
  `tool_events=[]`, `structured=False`, `exit_code=returncode`, and `latency_ms` measured around
  `subprocess.run` (behavior-neutral: `open_backend_session` still returns only `exit_code`).
- **`structured` mirrors `supports_structured`** — `BackendResult.structured` must equal the
  adapter's `supports_structured` (`False` for all four in this phase).

## Constraints and Context

- `docs/backend-adapters.md` is the canonical contract; this packet is its Phase 1 realization.
- Two standing CI constraints: no duplicated ≥ 6 similar lines across modules (pylint R0801) and a
  `pylint` score ≥ 8.0 on `src/ghostgrid/`.
- Credential redaction (`sanitize_env`) must remain in force for every transport.
- `tests/test_backends.py` must pass **unchanged** — this phase changes structure, not behavior.
