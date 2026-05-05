# Workflow Manager v2

Workflow Manager v2 is a local-first continuity and workflow scaffold for multi-agent coding projects. It keeps one hand-edited project contract, generates thin tool adapters, validates drift, and exposes deterministic Hermes dry-run surfaces before any live automation is allowed.

The public edition is sanitized for reuse: no private workspace paths, no credentials, no local continuity history, and no checked-in `.env` values.

## Install

```bash
python3 -m pip install -e .
workflow --help
```

Without installation, run the repo-local entrypoint:

```bash
python3 bin/workflow --help
```

## Core Model

- `AGENTS.md` is the canonical hand-edited project contract.
- `workflow sync` generates mirror files and role/capability adapters.
- `.workflow/mirror-lock.json` records managed checksums.
- `.specify/memory/*` stores durable project memory.
- `.specify/state/*` stores active handoff and progress state.
- `workflow status` and `workflow doctor` report command/docs, manifest, mirrors, memory, continuity, roots, role-contract, and docs-health.

## Command Surface

- `workflow init [--path <dir>] [--adopt-manual]`
- `workflow sync`
- `workflow status [--json]`
- `workflow doctor [--write-report] [--json]`
- `workflow roots [--validate] [--format text|shell|json]`
- `workflow open <name> [--create --root <path>]`
- `workflow list`
- `workflow save`
- `workflow close`
- `workflow hermes inventory --dry-run [--json]`
- `workflow hermes preflight --dry-run [--json]`
- `workflow hermes analyze --dry-run [--json]`
- `workflow hermes qwen-preview --dry-run [--json]`
- `workflow hermes qwen-connectivity [--probe --no-content --yes-network] [--json]`

## Hermes Boundary

Hermes is intentionally bounded. Inventory, preflight, analysis, and Qwen-preview are deterministic dry runs. Qwen connectivity is operator-gated, no-content, and disabled by default. Live analysis, migration writes, report writing, Graphify, background automation, prompt execution, and response parsing are out of scope until a later governed milestone enables them.

Manual live no-content connectivity probe commands:

```bash
workflow hermes qwen-connectivity --probe --no-content --yes-network
workflow hermes qwen-connectivity --probe --no-content --yes-network --json
```

Run the probe from an interactive terminal only. Automated validation and automated tests must not run it as a live probe. The probe sends no project content, no Hermes inventory content, no prompt preview content, and no target-repo content. It does not run Qwen analysis, does not write reports, does not migrate repos, and does not enable Graphify.

Share only sanitized fields such as `connectivity_status`, `sanitized_error_category`, `http_status_category`, and `network_attempted`.

Do not create a probe result file. Do not write probe results to `.specify/state/`. This path is operator-run only.

## Capability Adapters

Gemini capability adapters are generated from `capabilities/*/CAPABILITY.md` by default. Set `WORKFLOW_AI_SKILLS_CAPABILITIES_ROOT=/path/to/capabilities` to point at another local capability registry.

## Secret Hygiene

`.env` and `.env.*` are ignored. `.env.example` is placeholder-only. The DashScope/Qwen helper code reports key names and readiness booleans only; it must not print key values, Authorization headers, raw request headers, raw response bodies, or target-repo file contents.

## Verify

```bash
python3 -m compileall workflow_manager
python3 bin/workflow --help
python3 bin/workflow hermes --help
python3 -m unittest tests.test_workflow_cli
```
