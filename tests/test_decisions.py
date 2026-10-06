"""Tests for the System One decision-model client."""

import json
from unittest.mock import MagicMock

import pytest
import requests

from ghostgrid.decisions import (
    build_systemone_payload,
    decision_result_to_dict,
    load_questions,
    parse_systemone_response,
    questions_from_dict,
    run_decision,
    systemone_url,
    validate_question,
)
from ghostgrid.models import DecisionQuestion

# Response body from the llama.cpp decision-models announcement (values rounded).
LLAMA_CPP_EXAMPLE = {
    "model": "ggml-org/Kev-4B-GGUF",
    "answers": {
        "route": {
            "type": "choice",
            "choice": "billing",
            "probabilities": {"billing": 0.9049, "shipping": 0.0275, "technical": 0.0676},
            "confidence": 0.8574,
        },
        "angry": {"type": "noul", "noul": 0.8208},
        "urgency": {
            "type": "score",
            "score": 2.2821,
            "legend": {"0": "can wait", "1": "this week", "2": "today", "3": "right now"},
            "probabilities": {"0": 0.036, "1": 0.1937, "2": 0.2225, "3": 0.5478},
            "confidence": 0.2821,
        },
    },
    "usage": {"input_tokens": 130, "output_tokens": 0},
}

QUESTIONS = {
    "route": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": {"billing": "payments", "shipping": "delivery", "technical": "bugs"},
    },
    "angry": {"type": "noul", "instructions": "Is the customer angry?"},
    "urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["can wait", "this week", "today"]},
}


def _response(status: int, body: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status
    response.json.return_value = body
    response.text = json.dumps(body)
    return response


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("question", "message"),
    [
        (DecisionQuestion("q", "pick", "x"), "type must be one of"),
        (DecisionQuestion("q", "choice", ""), "instructions are required"),
        (DecisionQuestion("q", "choice", "x", {"only": None}), "at least two options"),
        (DecisionQuestion("q", "score", "x", ["low"]), "2 to 10 levels"),
        (DecisionQuestion("q", "score", "x", [str(i) for i in range(11)]), "2 to 10 levels"),
        (DecisionQuestion("q", "score", "x", {"a": None, "b": None}), "2 to 10 levels"),
        (DecisionQuestion("q", "noul", "x", ["yes", "no"]), "takes no criteria"),
    ],
)
def test_validate_question_rejects(question, message):
    with pytest.raises(ValueError, match=message):
        validate_question(question)


def test_validate_question_accepts_choice_list_and_dict():
    validate_question(DecisionQuestion("q", "choice", "x", ["a", "b"]))
    validate_question(DecisionQuestion("q", "choice", "x", {"a": "first", "b": None}))


def test_questions_from_dict_requires_one_question():
    with pytest.raises(ValueError, match="at least one question"):
        questions_from_dict({})


def test_load_questions_rejects_non_object(tmp_path):
    path = tmp_path / "q.json"
    path.write_text("[]")
    with pytest.raises(ValueError, match="expected a JSON object"):
        load_questions(str(path))


# ---------------------------------------------------------------------------
# Request building
# ---------------------------------------------------------------------------


def test_systemone_url_resolution(monkeypatch):
    monkeypatch.delenv("SYSTEMONE_URL", raising=False)
    assert systemone_url() == "http://127.0.0.1:8080/v1/systemone"
    assert systemone_url("http://host:9000/") == "http://host:9000/v1/systemone"
    assert systemone_url("https://api.example/v1/systemone") == "https://api.example/v1/systemone"
    monkeypatch.setenv("SYSTEMONE_URL", "http://tunnel:8080")
    assert systemone_url() == "http://tunnel:8080/v1/systemone"


def test_build_payload_matches_api_shape():
    payload = build_systemone_payload({"ticket": 42}, questions_from_dict(QUESTIONS), model="m")
    assert payload["state"] == {"ticket": 42}
    assert payload["model"] == "m"
    assert payload["questions"] == QUESTIONS
    assert "images" not in payload


def test_build_payload_omits_model_and_encodes_local_images(tmp_path):
    from PIL import Image

    img = tmp_path / "doc.png"
    Image.new("RGB", (4, 4)).save(img)
    payload = build_systemone_payload(
        "s", questions_from_dict({"angry": QUESTIONS["angry"]}), images=[str(img), "https://x/y.jpg"]
    )
    assert "model" not in payload
    assert payload["images"][0].startswith("data:image/png;base64,")
    assert payload["images"][1] == "https://x/y.jpg"


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def test_parse_llama_cpp_example_response():
    answers = parse_systemone_response(LLAMA_CPP_EXAMPLE)
    assert answers["route"].value == "billing"
    assert answers["route"].confidence == pytest.approx(0.8574)
    assert answers["angry"].value == pytest.approx(0.8208)
    assert answers["angry"].confidence is None
    assert answers["urgency"].value == pytest.approx(2.2821)
    assert answers["urgency"].probabilities["3"] == pytest.approx(0.5478)


# ---------------------------------------------------------------------------
# run_decision
# ---------------------------------------------------------------------------


def test_run_decision_success_without_key_sends_no_auth(monkeypatch):
    monkeypatch.delenv("SYSTEMONE_API_KEY", raising=False)
    post = MagicMock(return_value=_response(200, LLAMA_CPP_EXAMPLE))
    monkeypatch.setattr("ghostgrid.providers.requests.post", post)

    result = run_decision("s", questions_from_dict(QUESTIONS), url="http://127.0.0.1:8080")

    assert result.success
    assert result.model == "ggml-org/Kev-4B-GGUF"
    assert result.input_tokens == 130
    url = post.call_args.args[0]
    assert url == "http://127.0.0.1:8080/v1/systemone"
    assert "Authorization" not in post.call_args.kwargs["headers"]


def test_run_decision_uses_env_key(monkeypatch):
    monkeypatch.setenv("SYSTEMONE_API_KEY", "sk-test")
    post = MagicMock(return_value=_response(200, LLAMA_CPP_EXAMPLE))
    monkeypatch.setattr("ghostgrid.providers.requests.post", post)

    run_decision("s", questions_from_dict(QUESTIONS))

    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer sk-test"


def test_run_decision_returns_error_on_http_failure(monkeypatch):
    post = MagicMock(return_value=_response(401, {"error": "unauthorized"}))
    monkeypatch.setattr("ghostgrid.providers.requests.post", post)

    result = run_decision("s", questions_from_dict(QUESTIONS), url="http://h", retries=0)

    assert not result.success
    assert "401" in result.error
    assert result.answers == {}


def test_run_decision_returns_error_on_connection_failure(monkeypatch):
    post = MagicMock(side_effect=requests.exceptions.ConnectionError("refused"))
    monkeypatch.setattr("ghostgrid.providers.requests.post", post)

    result = run_decision("s", questions_from_dict(QUESTIONS), url="http://h", retries=0)

    assert not result.success


def test_run_decision_returns_error_on_malformed_body(monkeypatch):
    post = MagicMock(return_value=_response(200, {"unexpected": True}))
    monkeypatch.setattr("ghostgrid.providers.requests.post", post)

    result = run_decision("s", questions_from_dict(QUESTIONS), url="http://h")

    assert not result.success


def test_decision_result_to_dict(monkeypatch):
    post = MagicMock(return_value=_response(200, LLAMA_CPP_EXAMPLE))
    monkeypatch.setattr("ghostgrid.providers.requests.post", post)

    output = decision_result_to_dict(run_decision("s", questions_from_dict(QUESTIONS)))

    assert output["success"] is True
    assert output["answers"]["route"]["value"] == "billing"
    json.dumps(output)


def test_credential_env_vars_include_systemone_key():
    from ghostgrid.config import CREDENTIAL_ENV_VARS

    assert "SYSTEMONE_API_KEY" in CREDENTIAL_ENV_VARS


def test_shipped_example_questions_are_valid():
    from pathlib import Path

    example = Path(__file__).resolve().parent.parent / "examples" / "decision_questions.json"
    names = [q.name for q in load_questions(str(example))]
    assert names == ["gate", "touches_credentials", "blast_radius"]
