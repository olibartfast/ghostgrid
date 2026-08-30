# ghostgrid — Technical Boundaries

Every feature must respect these boundaries. Read this before planning any feature.

## Language and runtime

- **Python ≥ 3.10** (CI matrix: 3.10, 3.11, 3.12).
- Package name `ghostgrid`; source root `src/ghostgrid/`; CLI entry point `ghostgrid`
  (`ghostgrid.cli:main`).
- Line length **120** characters.

## Dependencies

- **Runtime (only these):** `requests>=2.28.0`, `Pillow>=9.0.0`.
  - No hard `cv2` import at module level (vision is served through provider APIs and the
    `neuriplo_detect` HTTP tool, not a bundled OpenCV pipeline).
- **Dev:** `pytest`, `pytest-cov`, `pytest-mock`, `ruff`, `pylint`, `mypy`.
- **Build:** `hatchling`; version read from `VERSION` (single source of truth).

## Quality gates (what CI actually fails on)

1. `ruff check src/ tests/` and `ruff format --check src/ tests/` clean
   (`select = ["E","F","I","UP","B","C4","SIM"]`).
2. `pylint src/ghostgrid/ --fail-under=8.0`.
3. **No duplicated block of ≥ 6 similar lines across modules (pylint R0801).** Shared logic goes
   to `ghostgrid/workflows/_utils.py` (e.g. `_result_to_dict`) or is passed through as `**kwargs`.
4. `mypy src/` — soft fail (advisory, not blocking).
5. `pytest tests/ -q -x` green.
6. `act -j lint` green before every push (container-accurate lint job).

The one local gate command is:

```bash
ruff check src/ tests/ && ruff format --check src/ tests/ && \
pylint src/ghostgrid/ --fail-under=8.0 && pytest tests/ -q -x && act -j lint
```

## Architecture

- **Data models:** dataclasses in `models.py` — `Agent`, `AgentResult`, `InferenceConfig`, `Tool`.
- **Provider dispatch:** `providers.py` (`run_agent`, `create_payload`, `send_request`,
  `stream_request`, `normalize_response`).
- **Workflows:** `workflows/` — `sequential`, `parallel`, `conditional`, `iterative`, `moa`,
  `react`, with shared helpers in `workflows/_utils.py`.
- **Tools:** `tools/builtin.py` + `tools/parsing.py` — vision tools and code-agent filesystem
  tools behind a `register_tool`/`unregister_tool` registry.
- **External backends:** `backends.py` — dispatch to external coding-agent CLIs.

## External agent backends (routing decision)

- `claude-code`, `codex`, `opencode`, `pi` are dispatched through an adapter contract in
  `backends.py`. See `docs/backend-adapters.md`.
- **`subprocess` is the default transport for all four.**
- **ACP is adopted only for `opencode`** (the sole backend with native ACP). The other three have
  only third-party ACP adapters — do **not** introduce ACP for them.
- Credential redaction (`sanitize_env`) is required for **every** transport, including ACP.

## Explicit non-choices

- **No ORM / database.** ghostgrid holds no persistent state.
- **No ACP for `claude-code`, `codex`, or `pi`.** Subprocess only.
- **No client-side/web framework.** This is a CLI + library, not a web app.
- **No bundled vision stack** (no hard `cv2` dependency at import time).
- **No new runtime dependency without approval.** Every addition is a roadmap decision, not a
  convenience.

## Conventions

- Tests mirror the `src/` layout under `tests/`.
- Do not add docstrings, comments, or type annotations to code you did not change.
- Do not add error handling for scenarios that cannot happen.
- Do not create helper abstractions for one-off operations.
