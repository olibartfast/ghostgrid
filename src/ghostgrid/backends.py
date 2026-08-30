"""Agent backend dispatch — opens interactive sessions with external coding-agent CLIs."""

import logging
import os
import subprocess
import time
from collections.abc import Callable

from ghostgrid.config import CREDENTIAL_ENV_VARS
from ghostgrid.models import BackendAdapter, BackendResult

logger = logging.getLogger(__name__)

_BACKEND_CMDS: dict[str, Callable[[str | None], list[str]]] = {
    "claude-code": lambda p: ["claude", p] if p else ["claude"],
    "codex": lambda p: ["codex", p] if p else ["codex"],
    "opencode": lambda p: ["opencode", p] if p else ["opencode"],
    "pi": lambda p: ["pi", p] if p else ["pi"],
}

BACKEND_CHOICES: list[str] = list(_BACKEND_CMDS)


def sanitize_env(extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a copy of os.environ with credential env vars redacted.

    Extra env vars from *extra_env* are layered on top (and are NOT redacted).
    """
    env = {k: v for k, v in os.environ.items() if k not in CREDENTIAL_ENV_VARS}
    if extra_env:
        env.update(extra_env)
    return env


def _run_subprocess_backend(
    cmd_builder: Callable[[str | None], list[str]],
    prompt: str | None,
    cwd: str | None,
    env: dict[str, str] | None,
) -> BackendResult:
    """Run one external coding-agent CLI and capture the outcome."""
    start = time.time()
    result = subprocess.run(cmd_builder(prompt), cwd=cwd, env=env, check=False)
    return BackendResult(
        content="",
        error=None,
        exit_code=result.returncode,
        latency_ms=(time.time() - start) * 1000,
        tool_events=[],
        structured=False,
    )


def _subprocess_backend_adapter(backend: str, cmd_builder: Callable[[str | None], list[str]]) -> BackendAdapter:
    """Build an exit-code-only subprocess adapter for a backend."""
    return BackendAdapter(
        name=backend,
        supports_structured=False,
        run=lambda prompt, cwd=None, env=None: _run_subprocess_backend(cmd_builder, prompt, cwd, env),
    )


BACKEND_ADAPTERS: dict[str, BackendAdapter] = {
    backend: _subprocess_backend_adapter(backend, cmd_builder) for backend, cmd_builder in _BACKEND_CMDS.items()
}


def open_backend_session(
    backend: str,
    prompt: str | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    sanitize: bool = True,
) -> int:
    """Launch an interactive coding-agent session and return its exit code.

    When *sanitize* is True (default), credential environment variables are
    stripped from the inherited environment. Pass explicit credentials via *env*.
    """
    if backend not in _BACKEND_CMDS:
        raise ValueError(f"Unknown agent backend: {backend!r}")
    merged_env = sanitize_env(env) if sanitize else ({**os.environ, **env} if env else None)
    logger.info("Launching %s backend session", backend)
    result = BACKEND_ADAPTERS[backend].run(prompt, cwd=cwd, env=merged_env)
    return result.exit_code
