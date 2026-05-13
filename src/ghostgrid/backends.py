"""Agent backend dispatch — opens interactive sessions with external coding-agent CLIs."""

import os
import subprocess
from collections.abc import Callable

_BACKEND_CMDS: dict[str, Callable[[str | None], list[str]]] = {
    "claude-code": lambda p: ["claude", p] if p else ["claude"],
    "codex": lambda p: ["codex", p] if p else ["codex"],
    "opencode": lambda p: ["opencode", p] if p else ["opencode"],
    "pi": lambda p: ["pi", p] if p else ["pi"],
}

BACKEND_CHOICES: list[str] = list(_BACKEND_CMDS)


def open_backend_session(
    backend: str,
    prompt: str | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> int:
    """Launch an interactive coding-agent session and return its exit code.

    When `env` is given, it is layered on top of the parent environment so the
    spawned CLI sees both inherited variables (PATH, HOME, …) and caller-injected
    credentials.
    """
    if backend not in _BACKEND_CMDS:
        raise ValueError(f"Unknown agent backend: {backend!r}")
    merged_env = {**os.environ, **env} if env else None
    result = subprocess.run(_BACKEND_CMDS[backend](prompt), cwd=cwd, env=merged_env, check=False)
    return result.returncode
