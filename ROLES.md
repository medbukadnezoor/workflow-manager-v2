# Roles

Canonical role contract: `~/ROLES.md`

This repo-local file is a thin public pointer plus harness mapping. It must not copy, summarize, or redefine the canonical Architect, Coder, Verifier, or reserved Tester role definitions.

## Harness Mapping

| Harness | Mapping |
| --- | --- |
| Claude Code CLI | Architect, Coder, and Verifier are generated as thin subagent adapters under `.claude/agents/`. |
| Codex CLI | Use the canonical role contract directly from `~/ROLES.md`. |
| Gemini CLI | Generated `.gemini/agents/*` files are capability adapters, not Architect/Coder/Verifier role adapters. |
| Antigravity IDE | Use `AGENTS.md` plus the canonical role contract. |
| OpenCode | Architect, Coder, and Verifier are generated as thin subagent adapters under `.opencode/agents/`. |
| Factory Droid | Architect → Product, Coder → Code, Verifier → Reliability. |
| Cursor | Deferred until a native subagent-spawning surface exists. |

Tester remains reserved and is activated only by explicit project coordination.
