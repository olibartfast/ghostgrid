"""Agent backend dispatch — opens interactive sessions with external coding-agent CLIs."""

import subprocess
from collections.abc import Callable

_BACKEND_CMDS: dict[str, Callable[[str | None], list[str]]] = {
    "claude-code": lambda p: ["claude", p] if p else ["claude"],
    "codex": lambda p: ["codex", p] if p else ["codex"],
    "opencode": lambda p: ["opencode", p] if p else ["opencode"],
    "pi": lambda p: ["pi", p] if p else ["pi"],
}

BACKEND_CHOICES: list[str] = list(_BACKEND_CMDS)


def open_backend_session(backend: str, prompt: str | None = None, cwd: str | None = None) -> int:
    """Launch an interactive coding-agent session and return its exit code."""
    if backend not in _BACKEND_CMDS:
        raise ValueError(f"Unknown agent backend: {backend!r}")
    result = subprocess.run(_BACKEND_CMDS[backend](prompt), cwd=cwd, check=False)
    return result.returncode
