# Feature Requirements — Model-API Capture Adapter (Phase 2a)

## Goal

Give every external backend (`claude-code`, `codex`, `opencode`, `pi`) a structured
`BackendResult` — `content` plus `tool_events` — **without** a per-vendor protocol layer, by
recording the backend's model calls at the one interface every harness must use: the model API.

The launched CLI is pointed at a local, in-process recording proxy (base URL + per-session token).
The proxy forwards each call to the real upstream, records request and response, and the adapter
turns the recording into a `BackendResult`. The CLI itself runs unmodified and stays interactive.

Background: *The ultimate guide to multi-harness RL* (Hugging Face, 2026-09-24) — a harness owns its
loop, so the only externally guaranteed observation point is the stream of model requests and
responses. This packet applies that idea to observation, not training.

## In Scope

- `ghostgrid/capture.py`: a stdlib (`http.server.ThreadingHTTPServer`) recording reverse proxy,
  bound to `127.0.0.1` on an ephemeral port, started and stopped around one backend session.
- Three request dialects, detected by path:
  - Anthropic Messages — `POST /v1/messages` (`claude-code`, `pi` when configured that way)
  - OpenAI Responses — `POST /v1/responses` (`codex`)
  - OpenAI Chat Completions — `POST /v1/chat/completions` (`opencode`, `pi`)
- **Pass-through, no translation.** Each call is forwarded to the upstream of the *same* dialect
  (`api.anthropic.com`, `api.openai.com`, or an override). Streaming (SSE) responses are teed: bytes
  go to the client as they arrive and are recorded alongside.
- Per-dialect **assemblers** that rebuild, from a recorded (possibly streamed) response, the final
  assistant text and the tool calls (`name`, `arguments`).
- A capture adapter (`supports_structured=True`) per backend, registered beside the subprocess
  adapters, that wires the CLI to the proxy, runs it via the existing subprocess path, and returns a
  `BackendResult` built from the recording.
- CLI opt-in: `ghostgrid run --agent-backend <b> --backend-capture [--capture-out trace.jsonl]`.
  Default behavior (no flag) is unchanged.

## Out of Scope

- Translating between dialects (e.g. serving a Responses client from a Chat Completions upstream).
- Token ids, log probabilities, and anything training-grade. Hosted APIs do not return them; this is
  observation-grade capture only.
- Rollout-graph reconstruction (prefix-linking retries, subagents, compaction into branches). Calls
  are recorded as one flat, ordered list. Deferred.
- Gemini / `google-generative-ai` dialect — no current backend needs it.
- Non-interactive (headless) backend invocation and joining `parallel`/`moa`/`react` — Phase 4.
- Subscription / OAuth logins (Claude Pro/Max, ChatGPT sign-in). Capture requires API-key auth.

## Decisions

- **Stdlib only.** `http.server` + `threading` for the listener, `requests` (already a runtime
  dependency) for upstream calls. No new runtime dependency — consistent with `tech-stack.md`.
- **The proxy holds the real key; the backend never does.** The subprocess env is still built by
  `sanitize_env` (credentials stripped); the only credential injected is a per-session token
  (`secrets.token_urlsafe(32)`). The proxy rejects any other token with `401` and injects the real
  key from ghostgrid's own environment on the upstream call. This *strengthens* the existing
  credential isolation rather than relaxing it.
- **One proxy per backend session.** Simpler than a shared multi-session proxy; concurrency is the
  caller's (Phase 4) concern.
- **Tee, don't buffer.** Unlike the article's proxy, which never streams to the engine and replays a
  stream, ghostgrid tees the upstream stream. Interactive latency is unchanged and the proxy needs no
  per-dialect SSE *writer* — only a per-dialect *reader* (assembler), used after the fact.
- **Recorded data is redacted.** `Authorization`, `x-api-key`, and any header whose name contains
  `key` or `token` are dropped before a call is stored or written to `--capture-out`.
- **`BackendResult` mapping.**
  - `content` = assembled assistant text of the last model call that produced text.
  - `tool_events` = one dict per call, in order:
    `{"type": "model_call", "seq", "dialect", "model", "status", "latency_ms", "streamed",
    "usage", "tool_calls": [{"name", "arguments"}]}`.
  - `exit_code` = subprocess return code; `structured=True`.
  - `error` = set when any recorded call has a non-2xx status or an unparseable body; the run is
    not aborted.
- **Per-backend wiring** (verify each in Group 0 against the installed CLI version):

  | Backend | Wiring | Notes |
  |---------|--------|-------|
  | `claude-code` | env `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY=<token>` | An existing OAuth login may take precedence — Group 0 confirms. |
  | `codex` | env `OPENAI_BASE_URL=<proxy>/v1`, `OPENAI_API_KEY=<token>` | Built-in `openai` provider honors `OPENAI_BASE_URL`. |
  | `opencode` | env `OPENCODE_CONFIG=<tmp>.json` with `provider.<id>.options.baseURL` / `apiKey` | Temp file, deleted after the session; user config untouched. |
  | `pi` | `~/.pi/agent/models.json` custom provider (`baseUrl`, `api`, `apiKey`) | **No documented override of the agent dir.** Writing into `$HOME` is not acceptable; `pi` capture stays unsupported until an override is found (Open Question 1). |

- **Unsupported capture is explicit.** `--backend-capture` with a backend that has no capture wiring
  exits non-zero with a JSON error; it never silently falls back to exit-code-only.

## Open Questions

1. `pi`: is there an env var or flag to load `models.json` from a non-home path? If not, `pi` keeps
   subprocess-only.
2. `claude-code`: does `ANTHROPIC_API_KEY` override a stored OAuth session, or is
   `ANTHROPIC_AUTH_TOKEN` needed? Pin the behavior in Group 0 and in the wiring table.
3. Should `ACP for opencode` (Phase 2) still ship once capture works for `opencode`? Proposed: keep
   it deferred; ACP adds tool *results* and permission events that capture cannot see, so revisit
   only if a consumer needs those.

## Constraints and Context

- `docs/backend-adapters.md` stays the canonical contract; this packet adds a second transport for
  `supports_structured=True` and does not change `BackendResult` or `BackendAdapter`.
- `open_backend_session` keeps its signature and default behavior; `tests/test_backends.py` passes
  unchanged.
- Standing CI constraints: no duplicated ≥ 6 similar lines across modules (pylint R0801); `pylint`
  ≥ 8.0 on `src/ghostgrid/`. Per-dialect assemblers share one SSE-line parser; per-backend wiring is
  a table of small builders, not four copies of setup code.
- Python ≥ 3.10 (CI matrix 3.10–3.12).
