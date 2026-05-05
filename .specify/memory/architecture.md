# Architecture

Updated: 2026-05-05 18:34 +0700

## Layers
- Canonical contract: `AGENTS.md`
- Generated shim layer: `CLAUDE.md`, `GEMINI.md`
- Manifest and lock layer: `.workflow/workflow.json`, `.workflow/mirror-lock.json`
- Continuity layer: `.specify/memory/*`, `.specify/state/*`
- Legacy compatibility layer: `.ai/` preserved during migration

## Command model
- `workflow` owns deterministic init, sync, status, doctor, close, save, and list behavior.
- `project-*` commands are thin shell wrappers around the v2 model where possible.
- The shell script remains a thin workspace bridge for navigation-oriented commands.

## Guardrails
- Generated shims are checksum-locked from `AGENTS.md`.
- Sync refuses managed drift unless `--force` is used.
- Doctor fails loudly on missing, empty, inconsistent, or half-migrated artifacts.
