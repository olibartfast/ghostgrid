"""Workflows package for text, vision, and multimodal execution patterns."""

from multimodal_agent_gateway.workflows.conditional import run_conditional
from multimodal_agent_gateway.workflows.iterative import run_iterative
from multimodal_agent_gateway.workflows.moa import run_moa
from multimodal_agent_gateway.workflows.monitoring import (
    run_continuous_monitoring,
    run_monitoring,
    run_monitoring_cycle,
)
from multimodal_agent_gateway.workflows.parallel import run_parallel
from multimodal_agent_gateway.workflows.react import run_react
from multimodal_agent_gateway.workflows.sequential import run_sequential

# Workflow registry for CLI dispatch
WORKFLOW_REGISTRY = {
    "sequential": run_sequential,
    "parallel": run_parallel,
    "conditional": run_conditional,
    "iterative": run_iterative,
    "moa": run_moa,
    "react": run_react,
}

__all__ = [
    "run_sequential",
    "run_parallel",
    "run_conditional",
    "run_iterative",
    "run_moa",
    "run_react",
    "run_monitoring",
    "run_monitoring_cycle",
    "run_continuous_monitoring",
    "WORKFLOW_REGISTRY",
]
