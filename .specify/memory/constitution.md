# Constitution

Updated: 2026-05-05 18:34 +0700
Primary source: `AGENTS.md`

## Non-negotiables
- Keep `AGENTS.md` as the canonical cross-tool contract.
- Canonical role definitions live in `~/ROLES.md`; repo-local `ROLES.md` is only a thin pointer plus harness mapping.
- Run `workflow sync` after changing `AGENTS.md`.
- Keep generated mirrors and mirror-lock metadata CLI-owned.
- Keep live network checks operator-gated and no-content.

## Continuity contract
- `AGENTS.md` is the only hand-edited cross-tool contract.
- Run `workflow sync` after any change to `AGENTS.md`.
- Treat `.specify/memory/*` and `.specify/state/*` as the primary v2 continuity layer.
- Preserve legacy `.ai/` files during coexistence, but do not treat them as the operational source of truth after v2 activation.
- Prefer loud validation and explicit backups over silent repair.

## Source notes
- This file was seeded from `AGENTS.md` and legacy continuity docs where available.
