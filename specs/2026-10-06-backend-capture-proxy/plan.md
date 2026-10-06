# Feature Plan — Model-API Capture Adapter (Phase 2a)

Each group is independently implementable and verifiable. Commit by task group.

## Group 0 — Wiring verification (no code merged)

1. For each backend, run the installed CLI against a throwaway local listener that logs method,
   path and headers, using the wiring in `requirements.md`. Record in the wiring table: the exact
   env vars / config keys honored, the path hit, the dialect, and whether the call streams.
2. Resolve Open Questions 1 and 2. Update `requirements.md` before Group 3.

## Group 1 — Proxy core (`ghostgrid/capture.py`)

3. `CaptureSession` dataclass: `token`, `base_url`, `calls: list[dict]`, `start()`, `stop()`;
   usable as a context manager.
4. Request handler: token check (`401` otherwise), dialect detection by path (`404` for anything
   else), forward via `requests` with the real key injected, tee the response (stream or not) to the
   client while recording status, latency, request body, response bytes.
5. Header redaction helper, applied before anything is stored.

## Group 2 — Assemblers

6. One shared SSE-line parser (`event:` / `data:` framing → list of JSON events).
7. Three assemblers — Anthropic Messages, OpenAI Responses, OpenAI Chat Completions — each mapping
   a recorded call (streamed or not) to `{"text", "tool_calls", "model", "usage"}`. Assemblers are
   a dict keyed by dialect; dialect-specific code is only the event-to-field mapping.
8. `calls_to_backend_result(calls, exit_code, latency_ms) -> BackendResult` per the mapping in
   `requirements.md`.

## Group 3 — Adapters and CLI

9. `_CAPTURE_WIRING: dict[str, Callable[[CaptureSession], dict[str, str]]]` returning the extra env
   (and writing the temp config file for `opencode`). Only verified backends get an entry.
10. `_capture_backend_adapter(backend, cmd_builder, wiring)` factory → `supports_structured=True`
    adapter that opens a `CaptureSession`, layers the wiring env over the sanitized env, reuses
    `_run_subprocess_backend`, and builds the result from the recording.
11. `CAPTURE_ADAPTERS` registry; `cli.py` adds `--backend-capture` and `--capture-out`. With the
    flag, the CLI prints the `BackendResult` as JSON (via `_result_to_dict`-style serialization,
    not a fork) after the interactive session ends and exits with the backend's exit code.

## Group 4 — Tests

12. `tests/test_capture.py`: proxy against a local fake upstream — token rejection, dialect routing,
    header redaction, streamed and non-streamed recording, upstream non-2xx surfaced as `error`.
13. Assembler fixtures: one recorded non-streamed and one streamed response per dialect (synthetic,
    hand-written — no recorded real traffic in the repo), each with a tool call.
14. Adapter test with a fake CLI (a small Python script that calls the proxy) for each wired backend.

## Group 5 — Docs and gate

15. `docs/backend-adapters.md`: add the capture transport, the wiring table, and its limits.
    `specs/tech-stack.md`: note capture as the structured path; ACP stays `opencode`-only.
    `README.md`: one short `--backend-capture` section.
16. Full gate: `ruff check/format`, `pylint --fail-under=8.0`, `pytest -q -x`, `act -j lint`.

## Standing constraints (apply to every group)

- No duplicated block of ≥ 6 similar lines across modules (pylint R0801).
- `pylint src/ghostgrid/ --fail-under=8.0` stays green.
- No new runtime dependency.
