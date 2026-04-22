<!-- GitHub Copilot workspace instructions -->
<!-- Primary source of truth: AGENTS.md (project root) — read that file for full conventions. -->

See [AGENTS.md](../AGENTS.md) for all coding conventions, linting rules, and project structure.

Key points:
- Package is `ghostgrid`, source root `src/ghostgrid/`
- Linting: `ruff` + `pylint --fail-under=8.0` (CI will fail below 8.0)
- **Never duplicate ≥ 6 similar lines across modules** — extract shared helpers to avoid pylint R0801
- Line length: 120; Python ≥ 3.10
