# Backend adapters — specification & roadmap

Status: decision (pending implementation).

## Problem

`ghostgrid/backends.py` is currently a terminal handoff: `open_backend_session()`
launches an external coding-agent CLI (`claude-code`, `codex`, `opencode`, `pi`) via
`subprocess.run` and returns only its exit code. `cli.py` short-circuits `--agent-backend`
with `sys.exit(...)`, so external agents never participate in workflows and return no
structured content.

This doc specifies how external agents become first-class workflow participants **without**
losing the current interactive-handoff behavior.

## Decision

Keep `subprocess` as the default transport. Introduce a capability-dispatch adapter layer:
subprocess for all four backends, plus an ACP adapter **only** where a backend natively
speaks ACP. Do not migrate the whole surface to ACP.

## Findings (verified against agentclientprotocol.com)

| Backend | ACP support | Transport to use |
|---------|-------------|------------------|
| `opencode` | native | ACP (later); subprocess as fallback |
| `claude-code` | adapter only (Zed `claude-agent-acp`) | subprocess; optional Claude Agent SDK later |
| `codex` | adapter only (Zed `codex-acp`) | subprocess |
| `pi` | adapter only (third-party `pi-acp`) | subprocess |

- Only `opencode` natively speaks ACP. The other three would require third-party adapter
  binaries, which reintroduces `subprocess` for a different binary *plus* a protocol layer
  this repo owns — no structural win over the current `_BACKEND_CMDS` launch.
- A first-party Python SDK exists (`agent-client-protocol`: Pydantic models, async base
  classes, JSON-RPC plumbing). Protocol is at v2-draft with v1 stable, so it is still moving.
- Credential redaction (`sanitize_env`) remains required for **every** transport, because ACP
  is also a subprocess we hand a credential-bearing environment to.

## Contract (spec)

No implementation here — only the shapes the adapters must satisfy.

### `BackendResult`

A structured result returned by every adapter:

- `content: str` — agent output; empty for exit-code-only transports.
- `error: str | None`
- `exit_code: int | None` — `None` when the transport exposes none (e.g. ACP).
- `latency_ms: float`
- `tool_events: list[dict]` — empty for subprocess; populated by ACP.
- `structured: bool` — `True` when `content` is meaningful vs. exit-code-only.

### `BackendAdapter`

- `name: str` — one of `BACKEND_CHOICES`.
- `supports_structured: bool`
- `run(prompt: str | None, *, cwd: str | None, env: dict[str, str] | None) -> BackendResult`

### Registry

`BACKEND_ADAPTERS: dict[str, BackendAdapter]` keyed by `BACKEND_CHOICES`. `open_backend_session`
remains the public entry point for interactive handoff and returns the adapter's `exit_code`
(raises if the adapter has no exit code).

Mapping to `AgentResult` (Phase 4 only): `agent_id = backend name`, `model = backend name`,
`provider = "backend"`.

## Roadmap

Delivery order and per-phase status live in `specs/roadmap.md`; the Phase 1 packet is
`specs/2026-08-30-backend-subprocess-adapter/`. This page owns the *what/why* (contract + findings);
the roadmap owns the *when*.

## Verification

Full gate before any commit: `ruff check/format`, `pylint --fail-under=8.0`, `pytest -q -x`,
then `act -j lint`.
