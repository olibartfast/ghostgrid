# ghostgrid — Agent & Contributor Instructions

This file is the **single source of truth** for coding conventions, tooling, and rules.
All other AI agent config files (`CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) defer to this file.

---

## Project overview

- **Package**: `ghostgrid` (Python ≥ 3.10)
- **Source root**: `src/ghostgrid/`
- **CLI entry point**: `ghostgrid` (maps to `ghostgrid.cli:main`)
- **GitHub repo**: `https://github.com/olibartfast/ghostgrid`

---

## Development setup

```bash
pip install -e ".[dev,video]"   # install with all dev + video deps
pytest tests/                   # run tests
ruff check src/ tests/          # lint
ruff format src/ tests/         # format
pylint src/ghostgrid/ --fail-under=8.0   # static analysis
mypy src/ || true               # type check (soft fail)
```

---

## Code quality rules

### Linting tools

| Tool | Purpose | Config |
|------|---------|--------|
| `ruff` | Fast lint + format | `[tool.ruff]` in `pyproject.toml` |
| `pylint` | Deep static analysis, min score 8.0 | `[tool.pylint]` in `pyproject.toml` |
| `mypy` | Type checking (soft fail) | `[tool.mypy]` in `pyproject.toml` |

### Never introduce duplicate code (pylint R0801)

Pylint R0801 (`duplicate-code`) fires when ≥ 6 similar lines appear across two or more modules.
**Always extract shared logic into a helper** instead of repeating it.

Common patterns that have triggered R0801 in this codebase and how to fix them:

| Pattern | Shared location |
|---------|----------------|
| Per-agent result dict `{agent_id, model, provider, latency_ms, success, error}` | Extract a `_result_to_dict(r)` helper in `ghostgrid/workflows/_utils.py` |
| `run_agent(agent, ..., image_paths, detail, max_tokens, resize, target_size)` call signature | Pass through as `**kwargs` or use a shared `_call_agent` wrapper |
| `cv2.VideoCapture` open + guard block (`contextlib.suppress` + `cap.isOpened()`) | Centralise in `ghostgrid/video.py` and import from there |

### Other conventions

- Line length: 120 characters (enforced by ruff + pylint).
- Python style: ruff `select = ["E", "F", "I", "UP", "B", "C4", "SIM"]`.
- Do **not** add docstrings, comments, or type annotations to code you did not change.
- Do **not** add error handling for scenarios that cannot happen.
- Do **not** create helper abstractions for one-off operations.

---

## Repository structure

```
src/ghostgrid/          # main package
  workflows/            # sequential, parallel, moa, react, iterative, conditional, monitoring
  tools/                # builtin ReAct tools + parsing helpers
  providers.py          # provider dispatch + run_agent
  models.py             # Agent, AgentResult, Tool, AlertEvent dataclasses
  config.py             # env/config helpers + system prompts
  cli.py                # argparse CLI
  image.py              # image encoding + resize helpers
  video.py              # OpenCV frame extraction helpers
tests/                  # pytest suite (mirrors src layout)
examples/               # runnable example scripts
docs/                   # markdown documentation
```

---

## CI

The CI pipeline (`.github/workflows/ci.yml`) runs:

1. **lint** job: `ruff` check + format, then `pylint --fail-under=8.0`
2. **test** job (needs lint): mypy, pytest with coverage across Python 3.10/3.11/3.12
3. **build** job: `hatch build`
