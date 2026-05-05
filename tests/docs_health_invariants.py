from __future__ import annotations

from pathlib import Path

from workflow_manager.docs_health import (
    DOCS_HEALTH_DEFAULT_BUDGETS,
    DOCS_HEALTH_REQUIRED_AGENTS_KEY_FILES,
    DOCS_HEALTH_SCHEMA_VERSION,
    DOCS_HEALTH_STATUS_VALUES,
    evaluate_docs_health,
)


EXPECTED_DOCS_HEALTH_SCHEMA_VERSION = "1.0.0"
EXPECTED_DOCS_HEALTH_STATUS_VALUES = ("pass", "warning", "fail")
EXPECTED_DOCS_HEALTH_BUDGETS = {
    "AGENTS.md": 200,
    "ROLES.md": 400,
    "MILESTONES.md": 400,
    "RULES.md": 300,
    "HERMES.md": 260,
    "README.md": 300,
    ".specify/state/active.md": 220,
    ".specify/state/handoff.md": 220,
    ".specify/state/progress.md": 220,
    ".specify/state/session.log.md": 220,
    ".specify/state/migration.md": 220,
    ".specify/memory/constitution.md": 200,
    ".specify/memory/project.md": 200,
    ".specify/memory/decisions.md": 200,
    ".specify/memory/architecture.md": 200,
    ".specify/memory/tech.md": 200,
}
EXPECTED_DOCS_HEALTH_REQUIRED_AGENTS_KEY_FILES = (
    "ROLES.md",
    "MILESTONES.md",
    "RULES.md",
    "HERMES.md",
    "workflow_manager/cli.py",
    "workflow_manager/role_contract.py",
    "tests/role_contract_invariants.py",
    "tests/hermes_analysis_json_invariants.py",
    "tests/hermes_qwen_preview_json_invariants.py",
    "tests/claude_adapter_invariants.py",
    "tests/opencode_adapter_invariants.py",
    "tests/droid_adapter_invariants.py",
    "tests/init_roles_seed_invariants.py",
    ".workflow/workflow.json",
    ".workflow/mirror-lock.json",
)


def verify_docs_health_policy() -> None:
    if DOCS_HEALTH_SCHEMA_VERSION != EXPECTED_DOCS_HEALTH_SCHEMA_VERSION:
        raise AssertionError("Docs-health schema version drifted.")
    if DOCS_HEALTH_STATUS_VALUES != EXPECTED_DOCS_HEALTH_STATUS_VALUES:
        raise AssertionError("Docs-health status vocabulary drifted.")
    if DOCS_HEALTH_DEFAULT_BUDGETS != EXPECTED_DOCS_HEALTH_BUDGETS:
        raise AssertionError("Docs-health line budgets drifted.")
    if DOCS_HEALTH_REQUIRED_AGENTS_KEY_FILES != EXPECTED_DOCS_HEALTH_REQUIRED_AGENTS_KEY_FILES:
        raise AssertionError("Docs-health required AGENTS.md Key files drifted.")


def verify_current_docs_health(repo: Path) -> None:
    verify_docs_health_policy()
    health = evaluate_docs_health(repo)
    if health.status != "pass":
        raise AssertionError(f"Current repo docs-health must pass, got {health.status}: {health.summary}")
    if len(health.entries) != len(EXPECTED_DOCS_HEALTH_BUDGETS):
        raise AssertionError("Docs-health entry count drifted.")
    if health.issues:
        raise AssertionError("Current repo docs-health must not have issues.")


def verify_docs_health_over_budget_example(repo: Path) -> None:
    budgets = dict(EXPECTED_DOCS_HEALTH_BUDGETS)
    budgets["README.md"] = 1
    health = evaluate_docs_health(repo, budgets=budgets)
    if health.status != "fail":
        raise AssertionError("Over-budget docs-health example must fail.")
    if not any("README.md" in issue.message and "over budget" in issue.message for issue in health.failures):
        raise AssertionError("Over-budget docs-health example must identify README.md.")


def verify_docs_health_key_files_example(repo: Path) -> None:
    budgets = dict(EXPECTED_DOCS_HEALTH_BUDGETS)
    health = evaluate_docs_health(repo, budgets=budgets)
    if health.status != "pass":
        raise AssertionError("Baseline docs-health must pass before Key-files drift example.")
    missing = "tests/droid_adapter_invariants.py"
    agents_path = repo / "AGENTS.md"
    original = agents_path.read_text(encoding="utf-8")
    try:
        agents_path.write_text(original.replace(f"`{missing}`", "`tests/missing_adapter_invariants.py`"), encoding="utf-8")
        drifted = evaluate_docs_health(repo, budgets=budgets)
    finally:
        agents_path.write_text(original, encoding="utf-8")
    if drifted.status != "fail":
        raise AssertionError("Missing Key-files docs-health example must fail.")
    if not any(missing in issue.message for issue in drifted.failures):
        raise AssertionError("Missing Key-files docs-health example must identify the missing required entry.")


def verify_docs_health_duplicate_heading_example(repo: Path) -> None:
    budgets = dict(EXPECTED_DOCS_HEALTH_BUDGETS)
    readme_path = repo / "README.md"
    original = readme_path.read_text(encoding="utf-8")
    try:
        readme_path.write_text(original + "\n## Current status\nDuplicated heading example.\n", encoding="utf-8")
        health = evaluate_docs_health(repo, budgets=budgets)
    finally:
        readme_path.write_text(original, encoding="utf-8")
    if health.status != "warning":
        raise AssertionError("Duplicate-heading docs-health example must warn.")
    if not any("current status" in issue.message for issue in health.warnings):
        raise AssertionError("Duplicate-heading docs-health example must identify the repeated heading.")


def verify_docs_health_gemini_claims_example(repo: Path) -> None:
    budgets = dict(EXPECTED_DOCS_HEALTH_BUDGETS)
    roles_path = repo / "ROLES.md"
    original = roles_path.read_text(encoding="utf-8")
    try:
        roles_path.write_text(
            original + "\n- Future claim: `.gemini/agents/architect.md` is a role adapter.\n",
            encoding="utf-8",
        )
        health = evaluate_docs_health(repo, budgets=budgets)
    finally:
        roles_path.write_text(original, encoding="utf-8")
    if health.status != "fail":
        raise AssertionError("Premature Gemini role-adapter docs-health example must fail.")
    if not any(".gemini/agents/architect.md" in issue.message for issue in health.failures):
        raise AssertionError("Gemini role-adapter docs-health example must identify the stale path.")

    readme_path = repo / "README.md"
    original_readme = readme_path.read_text(encoding="utf-8")
    try:
        readme_path.write_text(
            original_readme + "\n- `.gemini/agents/research-orchestrator.md` is the only managed Gemini subagent adapter.\n",
            encoding="utf-8",
        )
        health = evaluate_docs_health(repo, budgets=budgets)
    finally:
        readme_path.write_text(original_readme, encoding="utf-8")
    if health.status != "fail":
        raise AssertionError("Stale single Gemini adapter docs-health example must fail.")
    if not any("only managed Gemini subagent adapter" in issue.message for issue in health.failures):
        raise AssertionError("Gemini ownership docs-health example must identify the stale claim.")
