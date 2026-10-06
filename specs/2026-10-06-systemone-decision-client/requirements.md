# Feature Requirements — System One Decision Client

## Goal

Give ghostgrid a client for **decision models**: models that answer typed questions about a
state by scoring the options supplied, instead of generating text. The API is TypeSafe's
System One format (`POST /v1/systemone`), now also served by `llama-server` (llama.cpp
PR #29818) and by Laya's `laya-serve`. One client therefore reaches hosted Jev and self-hosted
open checkpoints by changing only the base URL.

This is the first, library-and-CLI slice. Using decisions inside workflows (gating `run_bash`,
routing in `conditional`) is the next phase and depends on measured confidence cutoffs from the
`agentic-ai-playground` `decision-v1` benchmark.

## In Scope

- Dataclasses in `models.py`: `DecisionQuestion`, `DecisionAnswer`, `DecisionResult`.
- A `decisions.py` module that validates questions, builds the request, sends it, and normalizes
  the response:
  - `choice`: two or more options, as a name→description map or a list of names.
  - `score`: 2 to 10 ordered levels, lowest first.
  - `noul`: a yes/no question with no options.
  - Optional `model` (router mode) and `images` (paths or URLs; image-capable models only).
- `run_decision(...) -> DecisionResult` that never raises on transport or HTTP failure; it
  returns a result with `error` set, matching `run_agent`.
- A `ghostgrid decide` CLI subcommand that reads questions from a JSON file in the API's own
  `questions` shape and prints a JSON result.
- `SYSTEMONE_URL` (base URL, default `http://127.0.0.1:8080`) and `SYSTEMONE_API_KEY`
  (optional bearer token) environment variables. `SYSTEMONE_API_KEY` joins
  `CREDENTIAL_ENV_VARS`, so it is redacted from `run_bash` and backend subprocesses.

## Out of Scope

- Any workflow change. `run_bash`, `conditional`, and `react` behave exactly as before.
- Batching several states per request.
- A fixed default confidence cutoff. Cutoffs are model-specific and unmeasured.
- Shipping or downloading models.

## Decisions

- **No new runtime dependency.** The client reuses `requests` through the existing
  `_request_with_retry`, so retry and backoff behave like every other provider call.
- **Separate from `run_agent`.** A decision request is not a chat completion: it has no messages,
  no `max_tokens`, and no text to normalize. Folding it into `providers.py` dispatch would force a
  fake prompt and a fake content string.
- **No `Authorization` header without a key.** A local `llama-server` needs none; sending
  `Bearer ` with an empty token would be noise at best.
- **Bearer authentication for hosted endpoints is assumed, not verified.** It matches
  `laya-serve`'s documented `LAYA_API_KEY` behavior; TypeSafe's header has not been checked
  against their docs. The key is read from one variable so a different header is a one-line change.
- **Client-side question validation.** Mistakes such as a one-option `choice` or an eleven-level
  `score` fail before any network call, with a message naming the question.
- **`DecisionAnswer.value` is the answer itself**: the chosen option name for `choice`, the
  expected level for `score`, and the probability of yes for `noul`. `confidence` is the server's
  field when it sends one and `None` otherwise; the client does not invent a confidence.

## Constraints and Context

- Two standing CI constraints: no duplicated ≥ 6 similar lines across modules (pylint R0801) and
  a `pylint` score ≥ 8.0 on `src/ghostgrid/`.
- `CREDENTIAL_ENV_VARS` redaction must cover the new key for every subprocess path.
- Response field names follow the llama.cpp announcement's example response. They were not
  checked against a live server in this phase.
