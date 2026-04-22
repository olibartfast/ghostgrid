"""
Parallel workflow: All agents process input simultaneously.

Input ──► [Agent-1] ─┐
Input ──► [Agent-2] ─┤──► [Aggregator] ──► final
Input ──► [Agent-3] ─┘
"""

import concurrent.futures

from ghostgrid.models import Agent, InferenceConfig
from ghostgrid.providers import run_agent
from ghostgrid.workflows._utils import _result_to_dict


def run_parallel(agents: list[Agent], prompt: str, config: InferenceConfig) -> dict:
    """
    Execute all agents concurrently and select the best response.

    Results are collected once all branches complete.
    The best response is selected by content length.
    """
    if len(agents) < 2:
        raise ValueError("parallel workflow requires at least 2 agents")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(run_agent, a, prompt, config): a for a in agents}
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    successful = [r for r in results if r.success]
    if not successful:
        raise RuntimeError(f"All parallel agents failed: {[r.error for r in results]}")

    best = max(successful, key=lambda r: len(r.content))

    return {
        "workflow": "parallel",
        "selected_agent_id": best.agent_id,
        "selected_model": best.model,
        "selected_provider": best.provider,
        "content": best.content,
        "agents": [_result_to_dict(r) for r in results],
    }
