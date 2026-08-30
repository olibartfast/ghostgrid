# ghostgrid — Mission

## Why this exists

Developers who build agentic applications currently wire each model provider by hand: different
SDKs, different message formats, different vision encodings, and no shared story for composing
multiple agents into a workflow. ghostgrid exists to collapse that into **one gateway**: route
vision, text, and code across providers and workflow patterns through a single CLI and Python API.

## Who it is for

- **Primary audience:** developers building multimodal or agentic applications who want to switch
  providers and workflow topologies without rewriting their orchestration code.
- **Secondary audience:** operators who hand a coding task off to an external coding-agent CLI
  (`claude-code`, `codex`, `opencode`, `pi`) and want a single, credential-safe entry point.

## Product promise

- **One interface, many providers.** OpenAI, Anthropic (native), Google, Together, OpenRouter,
  Z.AI, Azure, Groq, Mistral, Cerebras — behind the same `Agent` shape and call path.
- **Composable workflows.** Six patterns (`sequential`, `parallel`, `conditional`, `iterative`,
  `moa`, `react`) are first-class, not bolted on.
- **Multimodal by default.** Text-only or image input on the same command; vision ReAct tools and
  a code-agent (filesystem + opt-in shell) mode share one loop.
- **Observable and inspectable.** Per-agent latency, correlation IDs, and structured JSON output;
  failures are reported, never swallowed.

## Success criteria

1. A runnable example for each workflow pattern works against at least two providers with no
   orchestration rewrite.
2. Every provider and workflow is reachable from the CLI **and** the Python API.
3. External agent backends join workflows as first-class participants (not just terminal handoffs)
   without losing interactive sessions.
4. The repository stays green under its own gate: `ruff` clean, `pylint ≥ 8.0`, full `pytest`
   suite passing, `act -j lint` passing.

## Non-goals (things ghostgrid is not)

- It is **not** a model server, a prompt library, or a hosted service.
- It is **not** a persistence layer — it holds no database and no state between runs.
- It does **not** try to be a workflow engine for arbitrary business processes; its scope is
  LLM/VLM agent orchestration.

## Tone

Technical, terse, and evidence-first. Documents and specs state what will be built, what is
explicitly deferred, and how completion is proven — never aspirational prose.
