# Rules

## Source Of Truth

- `AGENTS.md` is the canonical hand-edited contract.
- `ROLES.md` points at `~/ROLES.md` and records harness mapping only.
- `MILESTONES.md` owns sequencing.
- `HERMES.md` owns Hermes boundaries and runbook guidance.

## Generated Surfaces

- Use `workflow sync` for generated shims, adapters, and mirror-lock updates.
- Do not hand-edit generated files to force a healthy state.
- Prefer loud validation failures over silent repair.

## Public Hygiene

- Do not commit `.env`, `.env.*`, private keys, local settings, caches, backups, or private continuity logs.
- Do not publish private absolute paths or machine-specific registry locations.
- Keep docs compact and link to focused files instead of duplicating large operating manuals.

## Hermes And Qwen

- Dry-run inventory, preflight, analysis, and prompt preview are allowed.
- Live connectivity is manual, operator-gated, and no-content.
- Live analysis, migration writes, report writing, Graphify, automation, prompt execution, and response parsing are disabled unless a later milestone explicitly enables them.

