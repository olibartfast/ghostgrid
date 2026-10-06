"""Client for System One decision models (`POST /v1/systemone`).

A decision model scores the options you supply instead of generating text. The same request
shape is served by TypeSafe's hosted Jev, llama.cpp's `llama-server`, and Laya's `laya-serve`.
"""

import json
import logging
import mimetypes
import os
import time
from typing import Any

import requests

from ghostgrid.config import DEFAULT_SYSTEMONE_URL, SYSTEMONE_API_KEY_ENV, SYSTEMONE_URL_ENV
from ghostgrid.image import encode_image, is_url
from ghostgrid.models import DecisionAnswer, DecisionQuestion, DecisionResult
from ghostgrid.providers import DEFAULT_BACKOFF_FACTOR, DEFAULT_RETRIES, _request_with_retry

logger = logging.getLogger(__name__)

SYSTEMONE_PATH = "/v1/systemone"
QUESTION_TYPES = ("choice", "score", "noul")
SCORE_LEVELS = (2, 10)


def validate_question(question: DecisionQuestion) -> None:
    """Raise ValueError if a question cannot be a valid System One question."""
    where = f"question '{question.name}'"
    if question.type not in QUESTION_TYPES:
        raise ValueError(f"{where}: type must be one of {list(QUESTION_TYPES)}, got '{question.type}'")
    if not question.instructions:
        raise ValueError(f"{where}: instructions are required")
    criteria = question.criteria
    if question.type == "noul":
        if criteria:
            raise ValueError(f"{where}: a noul question takes no criteria")
    elif question.type == "choice":
        if not isinstance(criteria, (dict, list)) or len(criteria) < 2:
            raise ValueError(f"{where}: a choice question needs at least two options")
    else:
        low, high = SCORE_LEVELS
        if not isinstance(criteria, list) or not low <= len(criteria) <= high:
            raise ValueError(f"{where}: a score question needs a list of {low} to {high} levels, lowest first")


def questions_from_dict(data: dict[str, dict]) -> list[DecisionQuestion]:
    """Build questions from the API's own `questions` mapping (name -> spec)."""
    questions = [
        DecisionQuestion(
            name=name,
            type=spec.get("type", ""),
            instructions=spec.get("instructions", ""),
            criteria=spec.get("criteria"),
        )
        for name, spec in data.items()
    ]
    if not questions:
        raise ValueError("at least one question is required")
    for question in questions:
        validate_question(question)
    return questions


def load_questions(path: str) -> list[DecisionQuestion]:
    """Load questions from a JSON file shaped like the request's `questions` field."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object mapping question names to questions")
    return questions_from_dict(data)


def systemone_url(base: str | None = None) -> str:
    """Resolve the endpoint from an explicit URL, $SYSTEMONE_URL, or the local default."""
    url = (base or os.getenv(SYSTEMONE_URL_ENV) or DEFAULT_SYSTEMONE_URL).rstrip("/")
    return url if url.endswith(SYSTEMONE_PATH) else url + SYSTEMONE_PATH


def _image_ref(path: str) -> str:
    if is_url(path):
        return path
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mime};base64,{encode_image(path)}"


def build_systemone_payload(
    state: Any,
    questions: list[DecisionQuestion],
    *,
    model: str | None = None,
    images: list[str] | None = None,
) -> dict:
    """Build a `/v1/systemone` request body. `state` may be text or any JSON value."""
    for question in questions:
        validate_question(question)
    payload: dict[str, Any] = {"state": state, "questions": {}}
    for question in questions:
        spec: dict[str, Any] = {"type": question.type, "instructions": question.instructions}
        if question.criteria:
            spec["criteria"] = question.criteria
        payload["questions"][question.name] = spec
    if model:
        payload["model"] = model
    if images:
        payload["images"] = [_image_ref(path) for path in images]
    return payload


def parse_systemone_response(response: dict) -> dict[str, DecisionAnswer]:
    """Normalize the `answers` object of a `/v1/systemone` response."""
    answers = {}
    for name, raw in response["answers"].items():
        qtype = raw["type"]
        if qtype == "choice":
            value: str | float = raw["choice"]
        elif qtype == "score":
            value = float(raw["score"])
        else:
            value = float(raw["noul"])
        probabilities = {str(k): float(v) for k, v in raw.get("probabilities", {}).items()}
        confidence = raw.get("confidence")
        answers[name] = DecisionAnswer(
            name=name,
            type=qtype,
            value=value,
            probabilities=probabilities,
            confidence=None if confidence is None else float(confidence),
        )
    return answers


def run_decision(  # pylint: disable=too-many-arguments,too-many-locals
    state: Any,
    questions: list[DecisionQuestion],
    *,
    url: str | None = None,
    model: str | None = None,
    images: list[str] | None = None,
    api_key: str | None = None,
    timeout: int = 60,
    retries: int = DEFAULT_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> DecisionResult:
    """Ask a decision model the questions about `state`. Failures are returned, not raised."""
    payload = build_systemone_payload(state, questions, model=model, images=images)
    endpoint = systemone_url(url)
    key = api_key if api_key is not None else os.getenv(SYSTEMONE_API_KEY_ENV)
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    t0 = time.time()
    try:
        response = _request_with_retry(endpoint, headers, payload, timeout, retries, backoff_factor, "System One")
        answers = parse_systemone_response(response)
    except (RuntimeError, requests.exceptions.RequestException, KeyError, TypeError, ValueError) as exc:
        latency_ms = (time.time() - t0) * 1000
        logger.error("System One request to %s failed: %s", endpoint, exc)
        return DecisionResult(model=model, answers={}, latency_ms=latency_ms, raw_response={}, error=str(exc))

    latency_ms = (time.time() - t0) * 1000
    logger.info("System One %s → %.0fms, %d answers", response.get("model", model), latency_ms, len(answers))
    return DecisionResult(
        model=response.get("model", model),
        answers=answers,
        latency_ms=latency_ms,
        raw_response=response,
        input_tokens=response.get("usage", {}).get("input_tokens"),
    )


def decision_result_to_dict(result: DecisionResult) -> dict:
    """The single place a DecisionResult becomes JSON."""
    return {
        "model": result.model,
        "success": result.success,
        "error": result.error,
        "latency_ms": round(result.latency_ms, 1),
        "input_tokens": result.input_tokens,
        "answers": {
            name: {
                "type": answer.type,
                "value": answer.value,
                "confidence": answer.confidence,
                "probabilities": answer.probabilities,
            }
            for name, answer in result.answers.items()
        },
    }
