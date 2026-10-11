"""
Data models (dataclasses) for the ghostgrid.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Agent:
    """Configuration for a single LLM or VLM agent."""

    model: str
    endpoint: str
    api_key: str
    provider: str = "openai"
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class AgentResult:
    """Result from executing a single agent call."""

    agent_id: str
    model: str
    provider: str
    content: str
    raw_response: dict
    latency_ms: float
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class InferenceConfig:
    """Shared inference parameters passed through the call stack."""

    image_paths: list[str] | None
    detail: str
    max_tokens: int
    resize: bool
    target_size: tuple[int, int]
    stream: bool = False


@dataclass
class Tool:
    """Definition of a ReAct tool."""

    name: str
    description: str
    parameters: str  # JSON schema hint shown to the agent
    fn: Callable  # fn(agent, config: InferenceConfig, **kwargs) -> str


@dataclass
class DecisionQuestion:
    """One typed question for a System One decision model."""

    name: str
    type: str  # "choice" | "score" | "noul"
    instructions: str
    criteria: dict[str, str | None] | list[str] | None = None


@dataclass
class DecisionAnswer:
    """A decision model's answer to one question."""

    name: str
    type: str
    value: str | float  # chosen option (choice), expected level (score), or P(yes) (noul)
    probabilities: dict[str, float]
    confidence: float | None = None


@dataclass
class DecisionResult:
    """Result of one System One request."""

    model: str | None
    answers: dict[str, DecisionAnswer]
    latency_ms: float
    raw_response: dict
    input_tokens: int | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class BackendResult:
    """Structured result from an external coding-agent backend adapter."""

    content: str
    error: str | None
    exit_code: int | None
    latency_ms: float
    tool_events: list[dict]
    structured: bool


@dataclass
class BackendAdapter:
    """Dispatch contract for an external coding-agent backend."""

    name: str
    supports_structured: bool
    run: Callable[[str | None, str | None, dict[str, str] | None], BackendResult]
