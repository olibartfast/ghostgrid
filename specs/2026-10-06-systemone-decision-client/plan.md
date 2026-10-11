# Feature Plan — System One Decision Client

1. Add `DecisionQuestion`, `DecisionAnswer`, and `DecisionResult` to `models.py`, beside
   `AgentResult`.
2. Add `SYSTEMONE_URL_ENV`, `SYSTEMONE_API_KEY_ENV`, and `DEFAULT_SYSTEMONE_URL` to `config.py`,
   and add the key variable to `CREDENTIAL_ENV_VARS`.
3. Write `decisions.py`:
   - `validate_question`, `questions_from_dict`, `load_questions`
   - `systemone_url` (accepts a base URL or the full endpoint)
   - `build_systemone_payload`, `parse_systemone_response`
   - `run_decision`, which wraps `_request_with_retry` and converts failures into
     `DecisionResult.error`
4. Add the `decide` subcommand to `cli.py` and a `decision_result_to_dict` serializer in
   `decisions.py`, the single place a `DecisionResult` becomes JSON.
5. Export the public names from `ghostgrid/__init__.py`.
6. Tests in `tests/test_decisions.py` (validation, payload, parsing, HTTP via `requests.post`
   mock, error path) and CLI tests in `tests/test_cli.py`; extend `tests/test_config.py` for
   redaction.
7. Document in `docs/decision-models.md` and add a short README section.

## Next phase (specified, not implemented)

**Decision gate for `run_bash`.** An opt-in `--shell-gate MODEL --shell-gate-cutoff X` asks a
`choice` question (`allow`/`ask`/`deny`) before each command. Below the cutoff, or on `ask`, the
command is refused with a message the agent can see; `deny` always refuses. This needs a cutoff
measured per model by `decision-v1` first, which is why it is not in this slice.
