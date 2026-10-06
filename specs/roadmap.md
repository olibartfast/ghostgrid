# ghostgrid — Roadmap

The smallest sensible delivery order, split into thin, independently reviewable phases. Status is
visible per phase. The two standing CI constraints apply to **every** phase below: no duplicated
block of ≥ 6 similar lines across modules (pylint R0801) and a `pylint` score ≥ 8.0 on
`src/ghostgrid/`.

## Delivered (shipped)

| Phase | Status |
|-------|--------|
| Core inference + provider dispatch (`openai`, `anthropic`, `google`, `together`, `azure`, `groq`, `mistral`, `cerebras`, `openrouter`, `zai`) | ✅ shipped |
| Six workflow patterns (`sequential`, `parallel`, `conditional`, `iterative`, `moa`, `react`) | ✅ shipped |
| Vision ReAct tools (`describe`, `detect_objects`, `read_text`, `analyze_region`, `count_objects`) | ✅ shipped |
| `neuriplo_detect` grounded detection tool (typed boxes/scores via `NEURIPLO_DETECT_URL`) | ✅ shipped |
| Code-agent mode (filesystem tools + opt-in `run_bash`) | ✅ shipped |
| External agent backend handoff (`claude-code`, `codex`, `opencode`, `pi` via subprocess) | ✅ shipped |
| Observability (per-agent latency, correlation IDs, structured JSON) | ✅ shipped |
| Retry/backoff, SSE streaming, tool plugins, structured logging, credential isolation | ✅ shipped |

## Next — backend adapters (in progress)

Source of truth: `docs/backend-adapters.md`. Goal: make external agents first-class workflow
participants **without** losing the interactive-handoff behavior. Each phase carries the two
standing CI constraints.

### Phase 1 — Subprocess adapter refactor (zero behavior change)

Status: **shipped** → `specs/2026-08-30-backend-subprocess-adapter/`

Move the current `subprocess.run` handoff behind the `BackendAdapter` contract. Keep
`sanitize_env` and the per-backend command mapping. `open_backend_session(backend, prompt, cwd,
env, sanitize)` keeps its exact signature and behavior; `tests/test_backends.py` must pass
unchanged. Extract the per-backend command builder and env handling into shared helpers so the
four backend branches do not repeat ≥ 6 similar lines (R0801).

### Phase 2 — ACP adapter for `opencode` (structured)

Status: **not started**

Add `agent-client-protocol` to `dependencies`; implement a `supports_structured=True` adapter for
`opencode` only, speaking JSON-RPC over stdio. Map content/tool events into `BackendResult`.
Subprocess stays as the fallback. Credential redaction still applies; framing/redaction shared with
the subprocess adapter lives in one helper (R0801).

### Phase 3 — Optional vendor adapters

Status: **not started**

`claude-code` Claude Agent SDK adapter only if structured output is actually needed; otherwise stay
on subprocess. `codex`, `pi` stay on subprocess (no ACP). Every adapter lands on the same
`BackendResult`; new transports are additive and never fork the subprocess path.

### Phase 4 — Workflow integration

Status: **not started**

Route `--agent-backend` through the same result-normalization path the workflows use, so a
structured backend can join `parallel`/`moa`/`react` via the `AgentResult` mapping. Keep
interactive handoff when `supports_structured=False`. Reuse `_result_to_dict` in
`workflows/_utils.py` as the single place a result becomes a JSON dict — do not fork it.

## Next — decision models (in progress)

Source of truth: `docs/decision-models.md`. Goal: let ghostgrid ask small typed questions
(`choice`, `score`, `noul`) of a decision model over the System One `/v1/systemone` API, served
by `llama-server`, `laya-serve`, or hosted Jev. Each phase carries the two standing CI
constraints.

### Phase D1 — Decision client and `decide` CLI

Status: **in progress** → `specs/2026-10-06-systemone-decision-client/`

`decisions.py`, decision dataclasses in `models.py`, and `ghostgrid decide`. No runtime
dependency added; reuses `_request_with_retry`. `SYSTEMONE_API_KEY` joins `CREDENTIAL_ENV_VARS`.
No workflow behavior changes.

### Phase D2 — Opt-in shell gate

Status: **not started** — blocked on measured cutoffs from `agentic-ai-playground`
`benchmarks/decision-v1`.

Ask an `allow`/`ask`/`deny` question before each `run_bash` command when the user opts in with a
model and a cutoff. Refuse on `deny`, on `ask`, and below the cutoff.

### Phase D3 — Decision router for `conditional`

Status: **not started**

Let the `conditional` workflow route with a `choice` question instead of a chat-model router,
mapping categories to options with descriptions.

## Deferred

- Anything not listed above is deferred until a roadmap phase names it. A new runtime dependency,
  a new workflow pattern, or a new backend transport is a roadmap decision first, code second.
