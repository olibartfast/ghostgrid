# Decision Models

A **decision model** answers typed questions about a *state* by scoring the options you give it,
instead of generating text. The answer is always one of your options, with a probability attached,
and comes from one forward pass with no output tokens.

ghostgrid speaks the **System One** API (`POST /v1/systemone`) introduced with TypeSafe's Jev. The
same contract is served by:

| Server | Where it runs | Notes |
| --- | --- | --- |
| `llama-server` (llama.cpp PR #29818 and later) | self-hosted | GGUF decision models; router mode serves several by name |
| `laya-serve` | self-hosted | Laya checkpoints; unauthenticated unless `LAYA_API_KEY` is set |
| TypeSafe Jev | hosted | the state leaves your machine |

Spec: [`specs/2026-10-06-systemone-decision-client/`](../specs/2026-10-06-systemone-decision-client/).

## Question types

| Type | `criteria` | Answer `value` |
| --- | --- | --- |
| `choice` | two or more options, as `{"name": "description"}` or `["name", ...]` | the chosen option name |
| `score` | 2 to 10 levels, lowest first | the expected level (may fall between two) |
| `noul` | none | the probability of yes |

Describe every `choice` option. The llama.cpp announcement reports a small model misrouting a
ticket with bare labels and routing it correctly once each option was described.

## CLI

```bash
ghostgrid decide \
    --state "Proposed shell command: git push origin main" \
    --questions examples/decision_questions.json \
    --url http://127.0.0.1:8080 \
    --model ggml-org/Julia-1-GGUF
```

- `--state` or `--state-file` (a `.json` file is sent as a JSON value, anything else as text).
- `--url` accepts a server root or the full `/v1/systemone` endpoint. Default: `$SYSTEMONE_URL`,
  then `http://127.0.0.1:8080`.
- `--model` selects a model on a router-mode server; a single-model server ignores it.
- `--images` attaches images for image-capable models (OpenJev, Clef). Local files are sent as data
  URLs.

Output is JSON with `success`, `model`, `latency_ms`, `input_tokens`, and per-question `value`,
`confidence`, and `probabilities`. A failed request prints the error and exits 1.

## Python

```python
from ghostgrid import load_questions, run_decision

result = run_decision(
    "Proposed shell command: rm -rf ~/.ssh",
    load_questions("examples/decision_questions.json"),
    url="http://127.0.0.1:8080",
)
if result.success:
    gate = result.answers["gate"]
    print(gate.value, gate.confidence)
```

`run_decision` never raises on transport, HTTP, or malformed-response failures; it returns a
`DecisionResult` with `error` set, like `run_agent`. Invalid questions raise `ValueError` before any
request is sent.

## Authentication

`SYSTEMONE_API_KEY`, when set, is sent as `Authorization: Bearer <key>`. Without it no
`Authorization` header is sent, which is right for a local `llama-server`. The bearer scheme
matches `laya-serve`; it has not been verified against TypeSafe's hosted API.

`SYSTEMONE_API_KEY` is in `CREDENTIAL_ENV_VARS`, so it is redacted from `run_bash` and external
backend subprocesses like every provider key.

## Confidence is per model

The `confidence` field is the server's, and is `None` when the server sends none (as for `noul`
answers in llama.cpp's example). It does not transfer between models: the llama.cpp announcement
shows one vague ticket at 0.25 confidence with Julia-1 and 0.80 with Kev-4B. Measure a cutoff for
each model on your own decisions before acting on one; the `agentic-ai-playground` `decision-v1`
benchmark exists for that.

## Not yet

Decisions are not wired into any workflow. The roadmap's next phases are an opt-in gate for
`run_bash` (D2) and a decision router for the `conditional` workflow (D3).
