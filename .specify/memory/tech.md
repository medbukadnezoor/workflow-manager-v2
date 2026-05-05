# Tech Context

Updated: 2026-05-05 18:34 +0700

## Stack
- Python 3 standard library for deterministic workflow commands
- zsh shell bridge in `scripts/workflow.sh`
- Markdown and JSON artifacts stored in-repo

## Core commands
- `workflow init [--dry-run]`
- `workflow sync`
- `workflow status`
- `workflow doctor`
- `workflow open`
- `workflow list`
- `workflow close`
- `workflow save`

## Continuity workflow
1. Read `.specify/state/handoff.md`.
2. Read `.specify/state/active.md`.
3. Run `workflow status`.
4. Run `workflow doctor --write-report` before closing changes that touch migration-state files or generated artifacts.

## Important files
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
