"""Tests for CLI helpers."""

import json
import sys

import pytest

from multimodal_agent_gateway import cli
from multimodal_agent_gateway.cli import build_agents


def test_build_agents_uses_provider_specific_default_endpoints(monkeypatch):
    """Each provider should resolve to its own default endpoint."""
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-test")

    agents = build_agents(
        models=["gpt-5.2", "gemini-2.5-flash"],
        providers=["openai", "google"],
        endpoints=[],
    )

    assert agents[0].endpoint == "https://api.openai.com/v1/chat/completions"
    assert agents[1].endpoint == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def test_build_agents_rejects_azure_without_endpoint(monkeypatch):
    """Azure deployments need an explicit resource-specific endpoint."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-test")

    with pytest.raises(RuntimeError, match="requires an explicit --endpoint"):
        build_agents(models=["gpt-5.2"], providers=["azure"], endpoints=[])


def test_main_allows_text_only_run(monkeypatch, capsys):
    """The run command should work without --images for text-only LLM calls."""
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test")
    monkeypatch.setattr(
        cli,
        "WORKFLOW_REGISTRY",
        {
            "sequential": lambda agents, **kwargs: {
                "workflow": "sequential",
                "content": "ok",
                "image_paths": kwargs["image_paths"],
            }
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["agent-gateway", "run", "--prompt", "Hello", "--model", "gpt-5.2", "--workflow", "sequential"],
    )

    cli.main()

    output = json.loads(capsys.readouterr().out)
    assert output["content"] == "ok"
    assert output["image_paths"] == []
