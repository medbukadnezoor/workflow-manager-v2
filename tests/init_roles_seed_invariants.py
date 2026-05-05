from __future__ import annotations

import json
from pathlib import Path

from workflow_manager.cli import (
    GENERATED_FORMAT_VERSION,
    GENERATED_ROLE_SHIMS,
    parse_generated_role_shim,
    render_role_shim,
    sha256_text,
)


EXPECTED_GENERATED_ROLE_SHIMS = ("ROLES.md",)
EXPECTED_ROLE_SHIM_SOURCE = "~/ROLES.md"


def verify_rendered_roles_seed() -> str:
    text = render_role_shim()
    marker = (
        f"workflow-generated:version={GENERATED_FORMAT_VERSION};"
        "tool=roles-pointer;source=~/ROLES.md"
    )
    if marker not in text:
        raise AssertionError("Seeded `ROLES.md` generated marker drifted.")
    if "Canonical role contract: `~/ROLES.md`" not in text:
        raise AssertionError("Seeded `ROLES.md` must point at `~/ROLES.md`.")
    if "must not copy" not in text or "redefine" not in text:
        raise AssertionError("Seeded `ROLES.md` must preserve the no-redefinition rule.")
    for forbidden_heading in ("### Architect", "### Coder", "### Verifier"):
        if forbidden_heading in text:
            raise AssertionError("Seeded `ROLES.md` must not copy role definition headings.")
    if parse_generated_role_shim(text) is None:
        raise AssertionError("Rendered seeded `ROLES.md` must parse as a generated role pointer.")
    return text


def verify_roles_seed_registry() -> None:
    if tuple(GENERATED_ROLE_SHIMS) != EXPECTED_GENERATED_ROLE_SHIMS:
        raise AssertionError("Generated role-shim registry drifted.")


def verify_seeded_roles_file(repo: Path) -> str:
    text = (repo / "ROLES.md").read_text(encoding="utf-8")
    expected = verify_rendered_roles_seed()
    if text != expected:
        raise AssertionError("Seeded `ROLES.md` drifted from the managed role-pointer render.")
    return text


def verify_seeded_agents_pointer(repo: Path) -> str:
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    if "Canonical role definitions live in `~/ROLES.md`" not in text:
        raise AssertionError("Seeded `AGENTS.md` must name `~/ROLES.md` as the canonical role contract.")
    return text


def verify_seeded_roles_lock(repo: Path) -> dict:
    lock = json.loads((repo / ".workflow/mirror-lock.json").read_text(encoding="utf-8"))
    if tuple(lock.get("generated_role_shims", [])) != EXPECTED_GENERATED_ROLE_SHIMS:
        raise AssertionError("Mirror lock generated role-shim list drifted.")
    role_shims = lock.get("role_shims")
    if not isinstance(role_shims, dict):
        raise AssertionError("Mirror lock must include `role_shims`.")
    if set(role_shims) != set(EXPECTED_GENERATED_ROLE_SHIMS):
        raise AssertionError("Mirror lock role-shim paths drifted.")
    entry = role_shims["ROLES.md"]
    if entry.get("format") != GENERATED_FORMAT_VERSION:
        raise AssertionError("Mirror lock role-shim format drifted.")
    if entry.get("source") != EXPECTED_ROLE_SHIM_SOURCE:
        raise AssertionError("Mirror lock role-shim source drifted.")
    expected_checksum = sha256_text(render_role_shim())
    if entry.get("full_checksum") != expected_checksum:
        raise AssertionError("Mirror lock role-shim checksum drifted.")
    return lock


def verify_seeded_roles_no_redefinition_rejected(text: str) -> None:
    unsafe = text + "\n### Architect\nCopied role prose.\n"
    if parse_generated_role_shim(unsafe) is not None:
        raise AssertionError("Generated role-pointer parser must reject copied role definition headings.")
