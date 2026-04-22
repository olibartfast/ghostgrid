"""Shared helpers for workflow modules."""

from ghostgrid.models import AgentResult


def _result_to_dict(r: AgentResult) -> dict:
    return {
        "agent_id": r.agent_id,
        "model": r.model,
        "provider": r.provider,
        "latency_ms": round(r.latency_ms, 1),
        "success": r.success,
        "error": r.error,
    }
