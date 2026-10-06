# Feature Validation — System One Decision Client

## Automated

Executed 2026-10-06 in a cloud sandbox (Python 3, no Docker daemon, no model server):

- [x] `ruff check src/ tests/ && ruff format --check src/ tests/` exits 0
- [x] `pylint src/ghostgrid/ --fail-under=8.0` passes at 9.99, with no R0801
- [x] `python3 -m pytest tests/ -q -x` passes: 106 tests, the 80 existing ones unchanged
- [x] `mypy src/ || true`: the new module's only advisory is the missing `requests` stubs that
      `providers.py` already reports
- [ ] `act -j lint` — **not run**: no Docker daemon in the sandbox. This change adds no
      dependency and does not touch `.github/workflows/`, which is what `act` guards; run it
      before merging.

End-to-end against a local stub server speaking the announced response shape:

- [x] `ghostgrid decide` posts to `/v1/systemone`, forwards `--model`, sends
      `Authorization: Bearer` only when `SYSTEMONE_API_KEY` is set, and prints the answers
- [x] An unreachable URL prints a JSON error and exits 1 after the standard retries

## Manual

- [ ] `ghostgrid decide` against a local `llama-server` with Julia-1 returns `answers` and
      `output_tokens == 0`
- [ ] The same call with `--model` in router mode selects the named model
- [x] Against an unreachable URL the command prints a JSON error and exits non-zero (stub run
      above)
- [x] `SYSTEMONE_API_KEY` is in `CREDENTIAL_ENV_VARS`, the set `run_bash` and backends strip
      (unit test); not separately observed inside a live `run_bash` call

## Definition of Done

- [ ] Spec, code, roadmap, docs, and README agree
- [ ] No workflow behavior changed
