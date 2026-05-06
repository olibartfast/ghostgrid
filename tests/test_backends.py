"""Tests for agent backend session dispatch."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from ghostgrid.backends import BACKEND_CHOICES, open_backend_session
from ghostgrid.cli import main


def _make_proc(returncode=0):
    m = MagicMock()
    m.returncode = returncode
    return m


def test_backend_choices_contains_all_four():
    assert set(BACKEND_CHOICES) == {"claude-code", "codex", "opencode", "pi"}


def test_open_backend_session_unknown_raises():
    with pytest.raises(ValueError, match="Unknown agent backend"):
        open_backend_session("nonexistent", "hello")


@pytest.mark.parametrize(
    "backend,prompt,expected_cmd",
    [
        ("claude-code", "fix bug", ["claude", "fix bug"]),
        ("codex", "add types", ["codex", "add types"]),
        ("opencode", "refactor", ["opencode", "refactor"]),
        ("pi", "explain this", ["pi", "explain this"]),
        ("claude-code", None, ["claude"]),
        ("pi", None, ["pi"]),
    ],
)
def test_open_backend_session_builds_correct_cmd(backend, prompt, expected_cmd):
    with patch("ghostgrid.backends.subprocess.run", return_value=_make_proc()) as mock_run:
        open_backend_session(backend, prompt)

    mock_run.assert_called_once_with(expected_cmd, cwd=None, check=False)


def test_open_backend_session_inherits_stdio():
    with patch("ghostgrid.backends.subprocess.run", return_value=_make_proc()) as mock_run:
        open_backend_session("claude-code", "test")

    _, kwargs = mock_run.call_args
    assert "capture_output" not in kwargs
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs


def test_open_backend_session_returns_exit_code():
    with patch("ghostgrid.backends.subprocess.run", return_value=_make_proc(returncode=2)):
        assert open_backend_session("pi", "test") == 2


def test_open_backend_session_passes_cwd():
    with patch("ghostgrid.backends.subprocess.run", return_value=_make_proc()) as mock_run:
        open_backend_session("codex", "test", cwd="/tmp/project")

    _, kwargs = mock_run.call_args
    assert kwargs["cwd"] == "/tmp/project"


def test_cli_agent_backend_opens_session_and_exits(monkeypatch):
    monkeypatch.setattr("ghostgrid.cli.open_backend_session", lambda b, p, **kw: 0)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ghostgrid", "run", "--agent-backend", "claude-code", "--prompt", "fix the bug"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_cli_agent_backend_propagates_nonzero_exit(monkeypatch):
    monkeypatch.setattr("ghostgrid.cli.open_backend_session", lambda b, p, **kw: 2)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ghostgrid", "run", "--agent-backend", "codex", "--prompt", "hello"],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


def test_cli_agent_backend_missing_binary_returns_json_error(monkeypatch, capsys):
    import json

    def _fail(b, p, **kw):
        raise FileNotFoundError("claude: command not found")

    monkeypatch.setattr("ghostgrid.cli.open_backend_session", _fail)
    monkeypatch.setattr(
        sys,
        "argv",
        ["ghostgrid", "run", "--agent-backend", "claude-code", "--prompt", "hello"],
    )

    with pytest.raises(SystemExit):
        main()

    out = json.loads(capsys.readouterr().out)
    assert "error" in out
