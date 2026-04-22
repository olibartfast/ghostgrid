# ghostgrid — Gemini instructions

Primary source of truth: **[AGENTS.md](./AGENTS.md)** — read that file before making changes.

Key points:
- Package is `ghostgrid`, source root `src/ghostgrid/`
- Linting: `ruff` + `pylint --fail-under=8.0` (CI will fail below 8.0)
- **Never duplicate ≥ 6 similar lines across modules** — extract shared helpers to avoid pylint R0801
- Line length: 120; Python ≥ 3.10
