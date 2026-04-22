"""Tests for provider payload construction."""

from ghostgrid.models import InferenceConfig
from ghostgrid.providers import create_payload


def test_create_payload_supports_text_only_requests():
    """Text-only runs should emit a valid chat payload with no image blocks."""
    payload = create_payload(
        prompt="Explain mixture-of-experts routing.",
        model="nemotron",
        config=InferenceConfig(image_paths=None, detail="low", max_tokens=200, resize=False, target_size=(512, 512)),
    )

    assert payload["model"] == "nemotron"
    assert payload["messages"] == [
        {"role": "user", "content": [{"type": "text", "text": "Explain mixture-of-experts routing."}]}
    ]
