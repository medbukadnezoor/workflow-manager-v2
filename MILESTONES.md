# Milestones

## M1 Public Foundation

- Keep `workflow init`, `sync`, `status`, `doctor`, `roots`, `open`, `list`, `save`, and `close` stable.
- Keep generated `CLAUDE.md`, `GEMINI.md`, `.claude/agents/*`, `.opencode/agents/*`, `.factory/droids/*`, and `.gemini/agents/*` checksum-locked.
- Keep docs-health, role-contract, and JSON contract invariants covered by tests.

## M2 Hermes Dry-Run Contracts

- Preserve deterministic `workflow hermes inventory --dry-run`.
- Preserve deterministic `workflow hermes preflight --dry-run`.
- Preserve deterministic `workflow hermes analyze --dry-run`.
- Preserve deterministic `workflow hermes qwen-preview --dry-run`.
- Keep `tests/hermes_inventory_json_invariants.py`, `tests/hermes_preflight_json_invariants.py`, `tests/hermes_analysis_json_invariants.py`, and `tests/hermes_qwen_preview_json_invariants.py` aligned with runtime output.

## M3 Operator-Gated Connectivity

- Keep `workflow hermes qwen-connectivity` local-only by default.
- Require `--probe --no-content --yes-network` before any live network attempt.
- Keep automated tests on mocked transports only.
- Keep raw secrets, Authorization headers, response bodies, target-repo content, and prompt bodies out of reports and command output.

## Deferred

Live Qwen analysis, prompt execution, live response parsing, migration writes, report writing, Graphify, and background automation remain out of scope until a deliberate milestone adds policy, tests, and docs.

