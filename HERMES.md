# Hermes

Hermes is the workflow-manager planning surface for shallow multi-repo inventory and readiness analysis. In this public release it is deliberately bounded to deterministic dry runs and one optional no-content connectivity probe.

## Allowed

- `workflow hermes inventory --dry-run`
- `workflow hermes preflight --dry-run`
- `workflow hermes analyze --dry-run`
- `workflow hermes qwen-preview --dry-run`
- `workflow hermes qwen-connectivity --json`

## Operator-Gated Probe

Manual live no-content connectivity probe:

```bash
workflow hermes qwen-connectivity --probe --no-content --yes-network
workflow hermes qwen-connectivity --probe --no-content --yes-network --json
```

Run this only from an interactive terminal. Automated validation and automated tests must not run it as a live probe.

The probe sends no project content, no Hermes inventory content, no prompt preview content, no target-repo content, no docs/state bodies, and no AGENTS/CLAUDE/GEMINI bodies. Share only sanitized fields such as connectivity status, sanitized error category, HTTP status category, and whether a network attempt occurred.

## Out Of Scope

Qwen analysis, prompt execution, response parsing, migration writes, report writing, Graphify, health-surface auto-probing, and background automation remain disabled.

