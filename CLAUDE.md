<!-- workflow-generated:version=workflow-managed-v1;tool=CLAUDE.md;source=AGENTS.md -->
# Claude Code context — workflow-manager-v2
# Generated from AGENTS.md by `workflow sync`.
# Do not edit the managed section below.

<!-- workflow-managed:start -->
# workflow-manager-v2

## What This Project Is

Public, sanitized Workflow Manager v2 reference implementation for local-first project continuity, generated agent adapters, drift checks, and bounded Hermes dry-run planning surfaces.

## Current Status

The public package includes the repo-local Python CLI, shell bridge, governance helpers, JSON contract checks, role-adapter generation, docs-health checks, DashScope/Qwen dry-run contracts, and an operator-gated no-content connectivity probe.

## Active Task

Keep the public release portable, secret-safe, and small enough for efficient agent context use. Do not publish private workspace paths, `.env` values, local continuity logs, or machine-specific generated caches.

## How To Continue

1. Read `.specify/state/handoff.md`.
2. Read `.specify/state/active.md`.
3. Run `workflow status`.
4. Run `workflow doctor --write-report` before closing changes that touch migration-state files or generated artifacts.

## Key Files

- `ROLES.md`
- `MILESTONES.md`
- `RULES.md`
- `HERMES.md`
- `workflow_manager/cli.py`
- `workflow_manager/role_contract.py`
- `tests/role_contract_invariants.py`
- `tests/hermes_analysis_json_invariants.py`
- `tests/hermes_qwen_preview_json_invariants.py`
- `tests/claude_adapter_invariants.py`
- `tests/opencode_adapter_invariants.py`
- `tests/droid_adapter_invariants.py`
- `tests/init_roles_seed_invariants.py`
- `.workflow/workflow.json`
- `.workflow/mirror-lock.json`

## Rules

- Keep `AGENTS.md` as the canonical cross-tool contract.
- Canonical role definitions live in `~/ROLES.md`; repo-local `ROLES.md` is only a thin pointer plus harness mapping.
- Run `workflow sync` after changing `AGENTS.md`.
- Keep generated mirrors and mirror-lock metadata CLI-owned.
- Keep live network checks operator-gated and no-content.
<!-- workflow-managed:end -->

<!-- workflow-unmanaged:start -->
No unmanaged notes.
Add tool-specific notes here only when they cannot live in `AGENTS.md`.
<!-- workflow-unmanaged:end -->
