from __future__ import annotations

import contextlib
import io
import inspect
import json
import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

from workflow_manager import cli as workflow_cli
from workflow_manager.dashscope_env import (
    DASHSCOPE_ACTIVE_ENV_KEYS,
    DASHSCOPE_FALLBACK_ONLY_ENV_KEYS,
    DASHSCOPE_FALLBACK_MODEL_ENV_KEYS,
    DASHSCOPE_INTENDED_MODEL,
    DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS,
    DASHSCOPE_RESERVED_ENV_KEYS,
    DASHSCOPE_REDACTED_VALUE,
    inspect_dashscope_local_readiness,
)
from workflow_manager.dashscope_request import (
    DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS,
    build_hermes_qwen_offline_request_shape,
    sanitize_dashscope_request_metadata,
)
from workflow_manager.dashscope_prompt import (
    build_hermes_qwen_offline_prompt_template,
    sanitize_dashscope_prompt_section_overrides,
)
from workflow_manager.dashscope_prompt_preview import (
    build_hermes_qwen_offline_prompt_preview,
    sanitize_dashscope_prompt_preview_sections,
)
from workflow_manager.dashscope_response import (
    build_hermes_qwen_offline_response_shape,
    sanitize_dashscope_response_slots,
)
from workflow_manager.dashscope_response_consumer import (
    build_hermes_qwen_offline_response_consumer_policy,
    sanitize_dashscope_response_consumer_examples,
)
from workflow_manager.dashscope_consumer_decision import (
    build_hermes_qwen_offline_consumer_decision_policy,
    sanitize_dashscope_consumer_decision_examples,
)
from workflow_manager.dashscope_escalation import (
    build_hermes_qwen_offline_escalation_policy,
    sanitize_dashscope_escalation_examples,
)
from workflow_manager.dashscope_response_parser import (
    parse_hermes_qwen_offline_simulated_response,
)
from workflow_manager.dashscope_connectivity import (
    DashScopeConnectivityProbeRequest,
    DashScopeConnectivityTransportResult,
    DASHSCOPE_CONNECTIVITY_PROBE_URL,
    probe_dashscope_connectivity,
)
from tests.help_snapshots import (
    HELP_FIXTURE_DIR,
    HELP_SNAPSHOT_LABELS,
    expected_snapshot_paths,
    snapshot_path_for_label,
    verify_help_snapshots,
)
from tests.wrapper_help_fixtures import (
    WRAPPER_FIXTURE_DIR,
    WRAPPER_HELP_CASES,
    expected_fixture_paths as expected_wrapper_fixture_paths,
    fixture_path_for_label as wrapper_fixture_path_for_label,
    verify_wrapper_help_fixtures,
)
from tests.wrapper_entrypoint_fixtures import (
    WRAPPER_ENTRYPOINT_FIXTURE_DIR,
    entrypoint_fixture_path,
    verify_wrapper_entrypoint_fixture,
)
from tests.shell_bridge_fixtures import (
    SHELL_BRIDGE_FIXTURE_DIR,
    shell_bridge_fixture_path,
    verify_shell_bridge_fixture,
)
from tests.cli_entrypoint_invariants import (
    CLI_ENTRYPOINT,
    FORBIDDEN_CLI_ENTRYPOINT_SNIPPETS,
    REQUIRED_CLI_ENTRYPOINT_SNIPPETS,
    verify_cli_entrypoint_invariants,
)
from tests.json_contract_invariants import (
    EXPECTED_JSON_CONTRACT_SCHEMA_VERSION,
    JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD,
    JSON_CONTRACT_CONSUMER_EXAMPLE_MODE,
    JSON_CONTRACT_SURFACES,
    SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION,
    assess_json_contract_change,
    build_future_minor_compatibility_examples,
    consume_future_minor_optional_fields_example,
    verify_future_minor_compatibility_examples,
    verify_future_minor_consumer_handling_example,
    verify_json_contract_reserved_additive_policy,
    verify_json_contract_evolution_policy,
    verify_json_contract_stdout,
)
from tests.role_contract_invariants import (
    EXPECTED_CANONICAL_ROLES,
    EXPECTED_RESERVED_ROLES,
    EXPECTED_ROLE_CONTRACT_SCHEMA_VERSION,
    EXPECTED_SUPPORTED_HARNESSES,
    verify_global_roles_doc,
    verify_local_roles_pointer,
    verify_role_contract_helper,
    verify_role_contract_no_leak_text,
)
from tests.claude_adapter_invariants import (
    EXPECTED_CLAUDE_ADAPTERS,
    verify_claude_adapter_files,
    verify_claude_adapter_lock,
    verify_claude_adapter_registry,
    verify_rendered_claude_adapters,
)
from tests.opencode_adapter_invariants import (
    EXPECTED_OPENCODE_ADAPTERS,
    verify_opencode_adapter_files,
    verify_opencode_adapter_lock,
    verify_opencode_adapter_registry,
    verify_rendered_opencode_adapters,
)
from tests.droid_adapter_invariants import (
    EXPECTED_DROID_ADAPTERS,
    verify_droid_adapter_files,
    verify_droid_adapter_lock,
    verify_droid_adapter_registry,
    verify_rendered_droid_adapters,
)
from tests.docs_health_invariants import (
    verify_current_docs_health,
    verify_docs_health_duplicate_heading_example,
    verify_docs_health_gemini_claims_example,
    verify_docs_health_key_files_example,
    verify_docs_health_over_budget_example,
    verify_docs_health_policy,
)
from tests.init_roles_seed_invariants import (
    verify_rendered_roles_seed,
    verify_roles_seed_registry,
    verify_seeded_agents_pointer,
    verify_seeded_roles_file,
    verify_seeded_roles_lock,
    verify_seeded_roles_no_redefinition_rejected,
)
from tests.hermes_inventory_json_invariants import (
    EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
    EXPECTED_HERMES_INVENTORY_JSON_KEYS,
    EXPECTED_HERMES_INVENTORY_PROJECT_KEYS,
    EXPECTED_HERMES_INVENTORY_ROOT_KEYS,
    ALLOWED_HERMES_PROJECT_CLASSIFICATIONS,
    ALLOWED_HERMES_ROOT_CLASSIFICATIONS,
    HERMES_INVENTORY_JSON_ADDITIVE_CHANGE_CATEGORIES,
    HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES,
    HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD,
    SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
    assess_hermes_inventory_json_change,
    build_hermes_inventory_future_minor_compatibility_example,
    verify_hermes_inventory_json_evolution_policy,
    verify_hermes_inventory_future_minor_compatibility_example,
    verify_hermes_inventory_json_payload,
    verify_hermes_inventory_json_reserved_additive_policy,
    verify_hermes_inventory_json_stdout,
)
from tests.hermes_preflight_json_invariants import (
    EXPECTED_HERMES_PREFLIGHT_JSON_KEYS,
    EXPECTED_HERMES_PREFLIGHT_PROJECT_KEYS,
    EXPECTED_HERMES_PREFLIGHT_ROOT_KEYS,
    verify_hermes_preflight_json_payload,
    verify_hermes_preflight_json_stdout,
)
from tests.hermes_analysis_json_invariants import (
    EXPECTED_HERMES_ANALYSIS_JSON_KEYS,
    EXPECTED_HERMES_ANALYSIS_PROJECT_KEYS,
    EXPECTED_HERMES_ANALYSIS_ROOT_KEYS,
    verify_hermes_analysis_json_payload,
    verify_hermes_analysis_json_stdout,
)
from tests.hermes_qwen_preview_json_invariants import (
    EXPECTED_HERMES_QWEN_PREVIEW_JSON_KEYS,
    EXPECTED_HERMES_QWEN_PREVIEW_PROMPT_KEYS,
    EXPECTED_HERMES_QWEN_PREVIEW_REQUEST_KEYS,
    verify_hermes_qwen_preview_json_payload,
    verify_hermes_qwen_preview_json_stdout,
)
from tests.env_secret_hygiene_invariants import (
    EXPECTED_ACTIVE_SECRET_ENV_KEYS,
    EXPECTED_DASHSCOPE_ENV_KEY_CATEGORIES,
    EXPECTED_DASHSCOPE_GENERIC_API_KEY_POLICY,
    EXPECTED_DASHSCOPE_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_LOCAL_READINESS_KEYS,
    EXPECTED_DASHSCOPE_MODEL_PRECEDENCE_POLICY,
    EXPECTED_DASHSCOPE_MODEL_SELECTION_POLICY,
    EXPECTED_DASHSCOPE_PRECEDENCE_POLICY,
    EXPECTED_ENV_EXAMPLE_VALUES,
    EXPECTED_ENV_IGNORE_PATTERNS,
    EXPECTED_FALLBACK_ONLY_SECRET_ENV_KEYS,
    EXPECTED_FALLBACK_MODEL_ENV_KEYS,
    EXPECTED_LOCAL_SECRET_ENV_KEYS,
    EXPECTED_OPTIONAL_MODEL_ENV_KEYS,
    EXPECTED_RESERVED_SECRET_ENV_KEYS,
    EXPECTED_SECRET_SAFE_GENERATED_FILES,
    assert_secret_absent_from_path,
    assert_secret_absent_from_text,
    inspect_env_file_keys,
    verify_dashscope_local_readiness_contract,
    verify_env_secret_hygiene_files,
)
from tests.dashscope_request_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_KEYS,
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_POLICY,
    EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SOURCE,
    verify_dashscope_offline_request_contract,
)
from tests.dashscope_prompt_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_SOURCE,
    verify_dashscope_offline_prompt_contract,
)
from tests.dashscope_prompt_preview_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE,
    EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE,
    verify_dashscope_offline_prompt_preview_contract,
)
from tests.dashscope_response_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_TYPE,
    verify_dashscope_offline_response_contract,
)
from tests.dashscope_response_consumer_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_NAMES,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
    verify_dashscope_offline_response_consumer_contract,
)
from tests.dashscope_consumer_decision_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_NAMES,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE,
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
    verify_dashscope_offline_consumer_decision_contract,
)
from tests.dashscope_escalation_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_NAMES,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE,
    EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_TYPE,
    verify_dashscope_offline_escalation_contract,
)
from tests.dashscope_response_parser_contract import (
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_FIELDS,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE,
    EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_VALIDATION_RESULTS,
    verify_dashscope_offline_response_parser_contract,
)
from tests.dashscope_connectivity_contract import (
    EXPECTED_DASHSCOPE_CONNECTIVITY_FIELDS,
    EXPECTED_DASHSCOPE_CONNECTIVITY_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_CONNECTIVITY_MODE,
    EXPECTED_DASHSCOPE_CONNECTIVITY_SOURCE,
    EXPECTED_DASHSCOPE_CONNECTIVITY_STATUSES,
    EXPECTED_DASHSCOPE_CONNECTIVITY_TYPE,
    verify_dashscope_connectivity_contract,
)
from tests.dashscope_connectivity_json_contract import (
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_COMMAND,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_ERROR_CATEGORIES,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_FIELDS,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_HTTP_STATUS_CATEGORIES,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_INTENDED_MODEL,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODE,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION,
    EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_STATUSES,
    verify_dashscope_connectivity_json_stdout,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ["/usr/bin/env", "python3", str(ROOT / "bin/workflow")]
SCRIPT = ROOT / "scripts/workflow.sh"
UPDATE_HELP_SNAPSHOTS = ROOT / "scripts/update_help_snapshots.py"
UPDATE_WRAPPER_HELP_FIXTURES = ROOT / "scripts/update_wrapper_help_fixtures.py"
UPDATE_WRAPPER_ENTRYPOINT_FIXTURES = ROOT / "scripts/update_wrapper_entrypoint_fixtures.py"
UPDATE_SHELL_BRIDGE_FIXTURES = ROOT / "scripts/update_shell_bridge_fixtures.py"
JSON_CONTRACT_INVARIANTS = ROOT / "tests/json_contract_invariants.py"
UPDATE_JSON_CONTRACT_FIXTURES = ROOT / "scripts/update_json_contract_fixtures.py"
HERMES_INVENTORY_JSON_INVARIANTS = ROOT / "tests/hermes_inventory_json_invariants.py"
UPDATE_HERMES_INVENTORY_JSON_FIXTURES = ROOT / "scripts/update_hermes_inventory_json_fixtures.py"
HERMES_PREFLIGHT_JSON_INVARIANTS = ROOT / "tests/hermes_preflight_json_invariants.py"
ENV_SECRET_HYGIENE_INVARIANTS = ROOT / "tests/env_secret_hygiene_invariants.py"
DASHSCOPE_REQUEST_CONTRACT = ROOT / "tests/dashscope_request_contract.py"
DASHSCOPE_PROMPT_CONTRACT = ROOT / "tests/dashscope_prompt_contract.py"
DASHSCOPE_PROMPT_PREVIEW_CONTRACT = ROOT / "tests/dashscope_prompt_preview_contract.py"
DASHSCOPE_RESPONSE_CONTRACT = ROOT / "tests/dashscope_response_contract.py"
DASHSCOPE_RESPONSE_CONSUMER_CONTRACT = ROOT / "tests/dashscope_response_consumer_contract.py"
DASHSCOPE_CONSUMER_DECISION_CONTRACT = ROOT / "tests/dashscope_consumer_decision_contract.py"
DASHSCOPE_ESCALATION_CONTRACT = ROOT / "tests/dashscope_escalation_contract.py"
DASHSCOPE_RESPONSE_PARSER_CONTRACT = ROOT / "tests/dashscope_response_parser_contract.py"
DASHSCOPE_CONNECTIVITY_CONTRACT = ROOT / "tests/dashscope_connectivity_contract.py"
DASHSCOPE_CONNECTIVITY_JSON_CONTRACT = ROOT / "tests/dashscope_connectivity_json_contract.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_roots_config(path: Path, roots: list[Path]) -> None:
    write(
        path,
        json.dumps(
            {
                "schema_version": "1.0.0",
                "roots": [str(root) for root in roots],
            },
            indent=2,
        )
        + "\n",
    )


def build_manager_home(
    root: Path,
    *,
    readme_text: str | None = None,
    agents_text: str | None = None,
    script_text: str | None = None,
) -> Path:
    manager_home = root / "manager-home"
    valid_root = root / "configured-root"
    valid_root.mkdir(parents=True, exist_ok=True)
    write_roots_config(manager_home / ".workflow/roots.json", [valid_root])
    write(
        manager_home / "README.md",
        readme_text if readme_text is not None else (ROOT / "README.md").read_text(encoding="utf-8"),
    )
    write(
        manager_home / "AGENTS.md",
        agents_text if agents_text is not None else (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
    )
    write(
        manager_home / "scripts/workflow.sh",
        script_text if script_text is not None else SCRIPT.read_text(encoding="utf-8"),
    )
    return manager_home


def legacy_agents(name: str) -> str:
    return (
        f"# {name}\n\n"
        "## What this project is\n"
        "Legacy repo for workflow testing.\n\n"
        "## Current status\n"
        "Still on the v1 scaffold.\n\n"
        "## Active task\n"
        "Adopt the v2 scaffold safely.\n\n"
        "## How to continue\n"
        "1. Read `.ai/handoffs/NEXT_STEP.md`\n"
        "2. Read `.ai/context/PROJECT_STATE.md`\n\n"
        "## Key files\n"
        "- `AGENTS.md`\n\n"
        "## Rules\n"
        "- Run `project-sync` after editing `AGENTS.md`.\n"
    )


def legacy_shim(title: str, name: str, agents: str) -> str:
    return (
        f"# {title} context — {name}\n"
        "# This file is auto-synced from AGENTS.md via project-sync.\n"
        "# To update: edit AGENTS.md, then run project-sync.\n\n"
        f"{agents}"
    )


def build_legacy_repo(root: Path, name: str = "legacy-repo") -> Path:
    repo = root / name
    agents = legacy_agents(name)
    write(repo / "AGENTS.md", agents)
    write(repo / "CLAUDE.md", legacy_shim("Claude Code", name, agents))
    write(repo / "GEMINI.md", legacy_shim("Gemini CLI", name, agents))
    write(
        repo / ".ai/context/PROJECT_STATE.md",
        "# Project state\n\n"
        "## Known Truths\n"
        "- Legacy continuity exists.\n\n"
        "## Open Unknowns\n"
        "- None.\n\n"
        "## Next Validation Step\n"
        "Run workflow doctor.\n\n"
        "## Completed\n"
        "- Nothing yet.\n",
    )
    write(
        repo / ".ai/handoffs/NEXT_STEP.md",
        "# Next step\n\n"
        "## What was just done\n"
        "Prepared the v1 scaffold.\n\n"
        "## What to do next\n"
        "Run the v2 init flow.\n\n"
        "## Blockers\n"
        "None.\n",
    )
    write(
        repo / ".ai/prompts/CURRENT_TASK.md",
        "# Current task prompt\n\n"
        "Move this repo onto the v2 scaffold.\n",
    )
    write(repo / ".ai/logs/session.log", "[2026-04-20 09:00] Session closed\n")
    return repo


def build_unmanaged_repo(root: Path, name: str = "unmanaged-repo") -> Path:
    repo = root / name
    write(repo / "README.md", "# Plain repo\n")
    write(
        repo / "AGENTS.md",
        "# unmanaged-repo\n\n"
        "## What this project is\n"
        "This directory has AGENTS but no workflow scaffold.\n\n"
        "## Active task\n"
        "Decide whether it should be managed.\n",
    )
    return repo


def build_mixed_repo(root: Path, name: str = "mixed-repo") -> Path:
    repo = build_legacy_repo(root, name)
    write(
        repo / ".specify/state/handoff.md",
        "# Handoff\n\n"
        "## What was just done\n"
        "A partial v2 scaffold appeared.\n\n"
        "## What to do next\n"
        "Resolve the mixed scaffold.\n",
    )
    write(
        repo / ".specify/state/active.md",
        "# Active State\n\n"
        "## Current task\n"
        "Resolve the mixed scaffold.\n",
    )
    return repo


def build_error_repo(root: Path, name: str = "error-repo") -> Path:
    repo = root / name
    write(repo / "AGENTS.md", legacy_agents(name))
    write(repo / ".workflow/workflow.json", "{ invalid json\n")
    write(repo / ".specify/state/handoff.md", "# Handoff\n")
    return repo


def build_valid_hermes_inventory_payload() -> dict:
    root_path = "/tmp/hermes-root"
    return {
        "schema_version": EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
        "command": "hermes_inventory",
        "mode": "inventory",
        "dry_run": True,
        "roots_config_path": "/tmp/hermes-roots.json",
        "summary": "1 repo candidate(s); 1/1 configured root(s) usable.",
        "classification_counts": {
            "v2": 1,
            "legacy": 0,
            "mixed": 0,
            "unmanaged": 0,
            "error": 0,
        },
        "roots": [
            {
                "path": root_path,
                "classification": "configured-root",
                "exists": True,
                "is_directory": True,
                "project_count": 1,
                "issues": [],
                "projects": [
                    {
                        "name": "alpha-v2",
                        "path": f"{root_path}/alpha-v2",
                        "root": root_path,
                        "classification": "v2",
                        "notes": [],
                    }
                ],
            }
        ],
        "warnings": [],
        "errors": [],
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
    }


def build_valid_hermes_preflight_payload() -> dict:
    root_path = "/tmp/hermes-root"
    return {
        "schema_version": "1.0.0",
        "command": "hermes_preflight",
        "mode": "preflight",
        "dry_run": True,
        "roots_config_path": "/tmp/hermes-roots.json",
        "summary": "1 repo candidate(s); 1/1 configured root(s) usable; ready=1, needs_review=0, blocked=0.",
        "roots_info": {
            "configured_root_count": 1,
            "usable_root_count": 1,
            "missing_root_count": 0,
            "invalid_root_count": 0,
            "project_count": 1,
        },
        "readiness_counts": {
            "ready": 1,
            "needs_review": 0,
            "blocked": 0,
        },
        "roots": [
            {
                "path": root_path,
                "classification": "configured-root",
                "exists": True,
                "is_directory": True,
                "project_count": 1,
                "issues": [],
                "projects": [
                    {
                        "name": "alpha-v2",
                        "path": f"{root_path}/alpha-v2",
                        "root": root_path,
                        "scaffold_classification": "v2",
                        "automation_readiness": "ready",
                        "migration_track": "maintain-v2",
                        "migration_risk": "low",
                        "git": {
                            "is_git_repo": True,
                            "is_dirty": False,
                            "status": "clean",
                            "dirty_path_count": 0,
                            "blocks_future_apply": False,
                        },
                        "detected_flags": ["agents-md", "scaffold:v2", "specify-continuity", "workflow-manifest"],
                        "blocking_reasons": [],
                        "warnings": [],
                        "next_safe_action": (
                            "Keep using read-only preflight until a separately approved apply design exists."
                        ),
                    }
                ],
            }
        ],
        "warnings": [],
        "errors": [],
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
        "report_writing_enabled": False,
        "target_repo_file_bodies_read": False,
    }


def build_valid_hermes_analysis_payload() -> dict:
    root_path = "/tmp/hermes-root"
    return {
        "schema_version": "1.0.0",
        "command": "hermes_analysis",
        "mode": "analysis",
        "dry_run": True,
        "roots_config_path": "/tmp/hermes-roots.json",
        "summary": "1 repo candidate(s); 1/1 configured root(s) usable; low=1, medium=0, high=0; human_review=0, blocked=0.",
        "analysis_counts": {
            "low": 1,
            "medium": 0,
            "high": 0,
            "requires_human_review": 0,
            "blocked": 0,
        },
        "roots": [
            {
                "path": root_path,
                "classification": "configured-root",
                "project_count": 1,
                "issues": [],
                "analyses": [
                    {
                        "name": "alpha-v2",
                        "path": f"{root_path}/alpha-v2",
                        "root": root_path,
                        "scaffold_classification": "v2",
                        "automation_readiness": "ready",
                        "migration_track": "maintain-v2",
                        "migration_risk": "low",
                        "git_status": "clean",
                        "deterministic_evidence": [
                            "preflight.scaffold_classification=v2",
                            "preflight.automation_readiness=ready",
                            "preflight.migration_track=maintain-v2",
                            "preflight.migration_risk=low",
                            "preflight.git.status=clean",
                            "preflight.git.blocks_future_apply=false",
                        ],
                        "inferred_recommendation": (
                            "Keep this repo on the maintain-v2 track; no apply, migration, report, or Qwen action is enabled."
                        ),
                        "blocked_actions": [
                            "Graphify execution",
                            "Qwen/DashScope analysis",
                            "live response parsing",
                            "migration writes",
                            "report writing",
                            "target-repo file-body reads",
                            "target-repo writes",
                        ],
                        "required_human_review": False,
                    }
                ],
            }
        ],
        "warnings": [],
        "errors": [],
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
        "report_writing_enabled": False,
        "target_repo_file_bodies_read": False,
        "live_response_parsing_enabled": False,
    }


def build_valid_hermes_qwen_preview_payload() -> dict:
    sections = {
        "system_role": "Use only this bounded offline analysis summary.",
        "task": "Preview the future Qwen request and prompt without executing anything.",
        "source_summary": "Source=hermes_analysis:1.0.0; dry_run=true; roots=1/1; repo_candidates=1; root_warnings=0; root_errors=0.",
        "analysis_summary": "risk=blocked=0, high=0, low=1, medium=0, requires_human_review=0; readiness=blocked=0, needs_review=0, ready=1; git=clean=1, dirty=0, not-git=0; scaffolds=error=0, legacy=0, mixed=0, unmanaged=0, v2=1; tracks=maintain-v2=1.",
        "evidence_category_summary": "Evidence categories only, capped at 16: preflight.git.status=1, preflight.migration_risk=1. Blocked actions: Qwen/DashScope analysis=1.",
        "safety_constraints": "Keep runtime_enabled=false and network_calls_allowed=false.",
        "expected_output_shape": "Future output should be concise structured metadata.",
        "redaction_policy": "Do not include root paths, project paths, API-key values, Authorization headers, .env values, or file bodies.",
    }
    section_order = list(sections.keys())
    assembled = "".join(f"## {name.replace('_', ' ').title()}\n{sections[name]}\n\n" for name in section_order).rstrip() + "\n"
    return {
        "schema_version": "1.0.0",
        "command": "hermes_qwen_preview",
        "mode": "offline_qwen_preview",
        "dry_run": True,
        "source": "hermes_analysis",
        "source_schema_version": "1.0.0",
        "intended_model": DASHSCOPE_INTENDED_MODEL,
        "selected_model": DASHSCOPE_INTENDED_MODEL,
        "model_policy_status": "default",
        "model_policy_ready": True,
        "model_policy_requires_update": False,
        "local_config_ready": False,
        "preview_limits": {
            "max_section_chars": workflow_cli.HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS,
            "max_assembled_prompt_chars": workflow_cli.HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS,
            "max_evidence_categories": workflow_cli.HERMES_QWEN_PREVIEW_MAX_EVIDENCE_CATEGORIES,
        },
        "source_summary": {
            "source_command": "hermes_analysis",
            "source_schema_version": "1.0.0",
            "source_mode": "analysis",
            "source_dry_run": True,
            "configured_root_count": 1,
            "usable_root_count": 1,
            "repo_candidate_count": 1,
            "roots_status": "pass",
            "roots_warning_count": 0,
            "roots_error_count": 0,
        },
        "analysis_summary": {
            "summary": "1 repo candidate(s); 1/1 configured root(s) usable; low=1, medium=0, high=0; human_review=0, blocked=0.",
            "analysis_counts": {
                "low": 1,
                "medium": 0,
                "high": 0,
                "requires_human_review": 0,
                "blocked": 0,
            },
            "readiness_counts": {
                "ready": 1,
                "needs_review": 0,
                "blocked": 0,
            },
            "git_status_counts": {
                "clean": 1,
                "dirty": 0,
                "not-git": 0,
            },
            "scaffold_classification_counts": {
                "v2": 1,
                "legacy": 0,
                "mixed": 0,
                "unmanaged": 0,
                "error": 0,
            },
            "migration_track_counts": {
                "maintain-v2": 1,
            },
            "blocked_action_counts": {
                "Qwen/DashScope analysis": 1,
            },
            "evidence_category_counts": {
                "preflight.git.status": 1,
                "preflight.migration_risk": 1,
            },
            "evidence_category_count": 2,
        },
        "request_preview": {
            "request_shape": "dashscope-qwen-chat-completions-preview",
            "source_command": "hermes_analysis",
            "source_schema_version": "1.0.0",
            "source_mode": "analysis",
            "source_dry_run": True,
            "intended_model": DASHSCOPE_INTENDED_MODEL,
            "selected_model": DASHSCOPE_INTENDED_MODEL,
            "model_policy_status": "default",
            "model_policy_ready": True,
            "model_policy_requires_update": False,
            "local_config_ready": False,
            "runtime_enabled": False,
            "network_calls_allowed": False,
            "request_execution_enabled": False,
            "qwen_dashscope_enabled": False,
            "input_kind": "bounded-analysis-summary",
            "root_paths_included": False,
            "project_paths_included": False,
            "env_values_included": False,
            "api_key_values_included": False,
            "authorization_headers_included": False,
            "target_repo_file_bodies_included": False,
        },
        "prompt_preview": {
            "preview_type": "bounded_prompt_preview",
            "preview_only": True,
            "prompt_execution_enabled": False,
            "section_order": section_order,
            "section_char_counts": {name: len(text) for name, text in sections.items()},
            "sections": sections,
            "assembled_prompt_preview": assembled,
            "assembled_prompt_char_count": len(assembled),
            "max_section_chars": workflow_cli.HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS,
            "max_assembled_prompt_chars": workflow_cli.HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS,
        },
        "warnings": [],
        "errors": [],
        "target_repos_modified": False,
        "network_attempted": False,
        "qwen_dashscope_enabled": False,
        "request_execution_enabled": False,
        "prompt_execution_enabled": False,
        "connectivity_probe_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
        "report_writing_enabled": False,
        "target_repo_file_bodies_read": False,
        "live_response_parsing_enabled": False,
        "root_paths_included": False,
        "project_paths_included": False,
        "env_values_included": False,
        "api_key_values_included": False,
        "authorization_headers_included": False,
    }


def build_dashscope_governed_policy_chain(repo: Path) -> tuple[dict, dict, dict, dict]:
    readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
    request_shape = verify_dashscope_offline_request_contract(
        build_hermes_qwen_offline_request_shape(
            build_valid_hermes_inventory_payload(),
            readiness,
        )
    )
    prompt_template = verify_dashscope_offline_prompt_contract(
        build_hermes_qwen_offline_prompt_template(request_shape)
    )
    prompt_preview = verify_dashscope_offline_prompt_preview_contract(
        build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
    )
    response_shape = verify_dashscope_offline_response_contract(
        build_hermes_qwen_offline_response_shape(prompt_preview)
    )
    response_consumer = verify_dashscope_offline_response_consumer_contract(
        build_hermes_qwen_offline_response_consumer_policy(response_shape)
    )
    consumer_decision = verify_dashscope_offline_consumer_decision_contract(
        build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
    )
    escalation = verify_dashscope_offline_escalation_contract(
        build_hermes_qwen_offline_escalation_policy(consumer_decision)
    )
    return response_shape, response_consumer, consumer_decision, escalation


def build_valid_simulated_response(response_shape: dict[str, object]) -> dict:
    return {
        "response_payload": {
            "analysis_summary": (
                "Deterministic Hermes evidence keeps the current analysis bounded to read-only inventory findings."
            ),
            "risk_summary": (
                "Risk remains bounded because governed writes, network calls, and live parsing all stay disabled."
            ),
            "recommended_next_step": (
                "Continue validating the governed offline chain before any runtime DashScope/Qwen integration."
            ),
            "blocked_actions": [
                "target-repo writes",
                "migration writes",
                "Graphify execution",
                "report writing",
            ],
            "required_human_review": False,
            "confidence": "high",
            "source_of_truth_policy": response_shape["source_of_truth_policy"],
            "forbidden_output_policy": list(response_shape["forbidden_output_policy"]),
            "redaction_policy": response_shape["redaction_policy"],
        },
        "evidence_references": {
            "risk_summary": ["hermes_warning_count"],
            "recommended_next_step": ["status_health_overview"],
            "required_human_review": ["doctor_result_status"],
            "blocked_actions": ["dashscope_readiness_policy"],
        },
        "forbidden_content_flags": [],
        "deterministic_mismatch_flag": False,
        "deterministic_evidence_metadata": {
            "hermes_warning_count": "warning_count=0",
            "status_health_overview": "overall_status=pass",
            "doctor_result_status": "pass",
            "dashscope_readiness_policy": "local_config_ready=true",
        },
    }


class WorkflowCliTests(unittest.TestCase):
    def run_cli(
        self,
        repo: Path,
        *args: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            [*CLI, *args],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
            env=merged_env,
        )

    def run_shell(
        self,
        *,
        roots: list[Path] | None = None,
        command: str,
        open_cmd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        lines = [
            f"source {shlex.quote(str(SCRIPT))}",
            f"WORKFLOW_MANAGER_HOME={shlex.quote(str(ROOT))}",
        ]
        if roots:
            root_assignment = " ".join(shlex.quote(str(root)) for root in roots)
            lines.append(f"WORKFLOW_ROOTS=({root_assignment})")
        if open_cmd is not None:
            lines.append(f"WORKFLOW_OPEN_CMD={shlex.quote(str(open_cmd))}")
        lines.append(command)
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["zsh", "-lc", "\n".join(lines)],
            text=True,
            capture_output=True,
            check=False,
            env=merged_env,
        )

    def create_v2_repo(self, parent: Path, name: str = "v2-repo", *, coexistence: bool = False) -> Path:
        if coexistence:
            repo = build_legacy_repo(parent, name)
        else:
            repo = parent / name
            repo.mkdir(parents=True, exist_ok=True)
        init_result = self.run_cli(repo, "init")
        self.assertEqual(init_result.returncode, 0, init_result.stderr)
        return repo

    def collect_governed_json_payloads(self, repo: Path) -> dict[str, dict]:
        commands = {
            "status": ("status", "--json"),
            "doctor": ("doctor", "--json"),
            "doctor_write_report": ("doctor", "--write-report", "--json"),
            "roots": ("roots", "--format", "json"),
        }
        payloads: dict[str, dict] = {}
        for surface, args in commands.items():
            result = self.run_cli(repo, *args)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            kwargs: dict[str, object] = {}
            if surface == "doctor_write_report":
                kwargs = {
                    "expect_wrote_report": True,
                    "expected_drift_report_path": repo / ".specify/state/drift.md",
                }
            payloads[surface] = verify_json_contract_stdout(result.stdout, surface, **kwargs)
        return payloads

    def snapshot_tree(self, root: Path) -> dict[str, tuple[int, bytes]]:
        snapshot: dict[str, tuple[int, bytes]] = {}
        for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
            relative = str(path.relative_to(root))
            snapshot[relative] = (path.stat().st_mtime_ns, path.read_bytes())
        return snapshot

    def init_clean_git_repo(self, repo: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo, text=True, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, text=True, capture_output=True, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Workflow Tests",
                "-c",
                "user.email=workflow-tests@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        )

    def create_secret_hygiene_repo(
        self,
        parent: Path,
        *,
        secret_value: str,
    ) -> tuple[Path, dict[str, str]]:
        repo = self.create_v2_repo(parent, "secret-hygiene-repo")
        write(
            repo / ".env",
            "# Local-only DashScope credential for hygiene validation.\n"
            f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={secret_value}\n",
        )
        roots_config = parent / "temp-roots.json"
        write_roots_config(roots_config, [parent])
        return repo, {"WORKFLOW_ROOTS_FILE": str(roots_config)}

    def test_init_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = build_legacy_repo(Path(temp_dir))
            result = self.run_cli(repo, "init", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".workflow/workflow.json", result.stdout)
            self.assertFalse((repo / ".workflow").exists())
            self.assertFalse((repo / ".specify").exists())

    def test_init_creates_v2_scaffold_and_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = build_legacy_repo(Path(temp_dir))
            result = self.run_cli(repo, "init")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo / ".workflow/workflow.json").exists())
            self.assertTrue((repo / ".workflow/mirror-lock.json").exists())
            self.assertTrue((repo / "ROLES.md").exists())
            self.assertTrue((repo / ".specify/state/handoff.md").exists())
            self.assertIn("workflow-generated", (repo / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertIn("Canonical role contract: `~/ROLES.md`", (repo / "ROLES.md").read_text(encoding="utf-8"))
            backups = list(repo.glob("CLAUDE.md.bak.*"))
            self.assertTrue(backups)

    def test_init_seeds_managed_roles_pointer_for_fresh_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "roles-seed-repo")
            verify_roles_seed_registry()
            roles_text = verify_seeded_roles_file(repo)
            verify_seeded_roles_no_redefinition_rejected(roles_text)
            verify_seeded_agents_pointer(repo)
            verify_seeded_roles_lock(repo)

            doctor_result = self.run_cli(repo, "doctor")
            self.assertEqual(doctor_result.returncode, 0, doctor_result.stderr)
            self.assertIn("- role-contract health: pass", doctor_result.stdout)
            self.assertIn("- mirror-lock/shim health: pass", doctor_result.stdout)

    def test_sync_refuses_managed_roles_pointer_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "roles-drift-repo")
            roles = repo / "ROLES.md"
            roles.write_text(
                roles.read_text(encoding="utf-8") + "\n### Architect\nCopied role prose.\n",
                encoding="utf-8",
            )

            sync_result = self.run_cli(repo, "sync")
            self.assertNotEqual(sync_result.returncode, 0)
            self.assertIn("generated role-pointer format", sync_result.stderr)

            doctor_result = self.run_cli(repo, "doctor")
            self.assertNotEqual(doctor_result.returncode, 0)
            self.assertIn("Mirror-lock/shim error: `ROLES.md` is not in the managed role-pointer format.", doctor_result.stdout)

    def test_init_roles_seed_invariants_cover_rendered_shape(self) -> None:
            roles_text = verify_rendered_roles_seed()
            self.assertIn("Canonical role contract: `~/ROLES.md`", roles_text)

    def test_init_adopt_manual_preserves_continuity_and_creates_role_lock_parity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "manual-scaffold-repo"
            repo.mkdir()
            write(
                repo / "AGENTS.md",
                "# manual-scaffold-repo\n\n"
                "## What this project is\n"
                "Manual scaffold adoption fixture.\n\n"
                "## Current status\n"
                "Manual continuity exists before CLI adoption.\n\n"
                "## Active task\n"
                "Adopt manual scaffold.\n\n"
                "## How to continue\n"
                "1. Read `.specify/state/handoff.md`\n"
                "2. Read `.specify/state/active.md`\n\n"
                "## Key files\n"
                "- `AGENTS.md`\n"
                "- `ROLES.md`\n\n"
                "## Rules\n"
                "- Keep `AGENTS.md` as the canonical cross-tool contract.\n"
                "- Canonical role definitions live in `~/ROLES.md`; repo-local `ROLES.md` is only a thin pointer.\n",
            )
            write(
                repo / ".specify/memory/constitution.md",
                "# Constitution\n\n## Non-negotiables\n- Keep AGENTS.md canonical.\n\n## Continuity contract\n- Use `.specify/*`.\n",
            )
            write(
                repo / ".specify/memory/project.md",
                "# Project Memory\n\n## What this project is\nManual scaffold adoption fixture.\n\n## Stable facts\n- Manual continuity came first.\n",
            )
            write(
                repo / ".specify/memory/decisions.md",
                "# Decisions\n\n## Durable decisions\n- Preserve manual continuity during adoption.\n",
            )
            write(
                repo / ".specify/memory/architecture.md",
                "# Architecture\n\n## Layers\n- Manual continuity layer.\n\n## Command model\n- `workflow` owns generated mirrors; project-* wrappers stay compatible.\n",
            )
            write(
                repo / ".specify/memory/tech.md",
                "# Tech Context\n\n## Stack\n- Python CLI.\n- zsh shell wrapper.\n\n## Core commands\n- `workflow init --adopt-manual`\n",
            )
            write(
                repo / ".specify/state/active.md",
                "# Active State\n\n## Current task\nAdopt manual scaffold.\n\n## Active spec/task pointer\nNo active spec.\n",
            )
            write(
                repo / ".specify/state/handoff.md",
                "# Handoff\n\n## What was just done\nManual files were created.\n\n## What to do next\nRun adoption.\n\n## Blockers\nNone.\n",
            )
            write(
                repo / ".specify/state/progress.md",
                "# Progress\n\n## Recent progress\n- Manual scaffold exists.\n",
            )
            write(
                repo / ".specify/state/session.log.md",
                "# Session Log\n\n## Entries\n- Manual scaffold created.\n",
            )
            write(
                repo / ".specify/state/migration.md",
                "# Migration State\n\n## Current state\n- Status: v2\n- Phase: milestone-1-foundation\n- Legacy preserved: no\n",
            )

            before_active = (repo / ".specify/state/active.md").read_text(encoding="utf-8")
            default_result = self.run_cli(repo, "init", "--dry-run")
            self.assertNotEqual(default_result.returncode, 0)
            self.assertIn("refusing to overwrite existing .specify/memory/constitution.md", default_result.stderr)

            adopt_result = self.run_cli(repo, "init", "--adopt-manual")
            self.assertEqual(adopt_result.returncode, 0, adopt_result.stderr)
            self.assertIn("preserve existing .specify/state/active.md", adopt_result.stdout)
            self.assertEqual(before_active, (repo / ".specify/state/active.md").read_text(encoding="utf-8"))
            verify_seeded_roles_file(repo)
            verify_seeded_roles_lock(repo)

            doctor_result = self.run_cli(repo, "doctor")
            self.assertEqual(doctor_result.returncode, 0, doctor_result.stderr)
            self.assertIn("- mirror-lock/shim health: pass", doctor_result.stdout)

    def test_init_adopt_manual_requires_agents_role_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "manual-missing-role-pointer"
            repo.mkdir()
            write(repo / "AGENTS.md", "# manual-missing-role-pointer\n\n## Rules\n- Missing role pointer.\n")

            result = self.run_cli(repo, "init", "--adopt-manual")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires `AGENTS.md` to point at `~/ROLES.md`", result.stderr)

    def test_init_refuses_unsafe_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = build_legacy_repo(Path(temp_dir))
            init_result = self.run_cli(repo, "init")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            handoff = repo / ".specify/state/handoff.md"
            handoff.write_text(
                handoff.read_text(encoding="utf-8") + "\nManual edit.\n",
                encoding="utf-8",
            )
            result = self.run_cli(repo, "init")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to overwrite existing .specify/state/handoff.md", result.stderr)

    def test_sync_detects_managed_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = build_legacy_repo(Path(temp_dir))
            init_result = self.run_cli(repo, "init")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            claude = repo / "CLAUDE.md"
            text = claude.read_text(encoding="utf-8").replace("Legacy repo for workflow testing.", "Manual drift.")
            claude.write_text(text, encoding="utf-8")
            result = self.run_cli(repo, "sync")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("managed drift", result.stderr)

    def test_sync_is_deterministic_on_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = build_legacy_repo(Path(temp_dir))
            init_result = self.run_cli(repo, "init")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            before_claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
            before_lock = (repo / ".workflow/mirror-lock.json").read_text(encoding="utf-8")
            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("- no changes", result.stdout)
            self.assertEqual(before_claude, (repo / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertEqual(before_lock, (repo / ".workflow/mirror-lock.json").read_text(encoding="utf-8"))

    def test_sync_generates_thin_gemini_capability_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "gemini-adapter-repo")
            adapter_path = repo / ".gemini/agents/research-orchestrator.md"
            adapter_text = adapter_path.read_text(encoding="utf-8")
            canonical_path = "capabilities/research-orchestrator/CAPABILITY.md"

            self.assertTrue(adapter_text.startswith("---\n"))
            self.assertIn("name: research-orchestrator", adapter_text)
            self.assertIn("description: Thin Workflow Manager adapter", adapter_text)
            self.assertIn("# research-orchestrator Capability Adapter", adapter_text)
            self.assertIn(canonical_path, adapter_text)
            self.assertIn("Read and follow that canonical capability file", adapter_text)
            self.assertNotIn("## Evidence-Spine Workflow", adapter_text)
            self.assertNotIn("## Artifact Map", adapter_text)
            self.assertNotIn("# Research Orchestrator Adapter", adapter_text)

            for managed_path, metadata in workflow_cli.MANAGED_GEMINI_ADAPTERS.items():
                generated = (repo / managed_path).read_text(encoding="utf-8")
                self.assertIn(f"# {metadata['name']} Capability Adapter", generated)
                if metadata["name"] != "research-orchestrator":
                    self.assertNotIn("# Research Orchestrator Adapter", generated)

            lock = json.loads((repo / ".workflow/mirror-lock.json").read_text(encoding="utf-8"))
            self.assertIn(".gemini/agents/research-orchestrator.md", lock["gemini_adapters"])
            self.assertEqual(
                lock["gemini_adapters"][".gemini/agents/research-orchestrator.md"]["canonical_capability"],
                canonical_path,
            )

    def test_doctor_respects_manifest_scoped_gemini_adapter_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "gemini-subset-repo")
            manifest_path = repo / ".workflow/workflow.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["generated_gemini_adapters"] = [".gemini/agents/research-orchestrator.md"]
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            for managed_path in workflow_cli.MANAGED_GEMINI_ADAPTERS:
                if managed_path != ".gemini/agents/research-orchestrator.md":
                    (repo / managed_path).unlink()

            lock_path = repo / ".workflow/mirror-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["gemini_adapters"] = {
                ".gemini/agents/research-orchestrator.md": lock["gemini_adapters"][
                    ".gemini/agents/research-orchestrator.md"
                ]
            }
            write(lock_path, json.dumps(lock, indent=2) + "\n")

            result = self.run_cli(repo, "doctor")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Missing generated Gemini adapter `.gemini/agents/agent-command-guard.md`.", result.stdout)

    def test_doctor_defaults_to_all_gemini_adapters_when_manifest_key_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "gemini-default-repo")
            manifest_path = repo / ".workflow/workflow.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.pop("generated_gemini_adapters", None)
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            (repo / ".gemini/agents/research-orchestrator.md").unlink()

            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "Missing generated Gemini adapter `.gemini/agents/research-orchestrator.md`.",
                result.stdout,
            )

    def test_manifest_managed_adapter_paths_handles_unknown_and_invalid_values(self) -> None:
        managed_path = ".gemini/agents/research-orchestrator.md"
        self.assertIn(managed_path, workflow_cli.MANAGED_GEMINI_ADAPTERS)
        self.assertEqual(
            workflow_cli.manifest_managed_adapter_paths(
                {"generated_gemini_adapters": [managed_path, ".gemini/agents/not-managed.md", 7]},
                "generated_gemini_adapters",
                workflow_cli.MANAGED_GEMINI_ADAPTERS,
            ),
            [managed_path],
        )
        self.assertEqual(
            workflow_cli.manifest_managed_adapter_paths(
                {"generated_gemini_adapters": managed_path},
                "generated_gemini_adapters",
                workflow_cli.MANAGED_GEMINI_ADAPTERS,
            ),
            list(workflow_cli.MANAGED_GEMINI_ADAPTERS.keys()),
        )

    def test_sync_preserves_unmanaged_gemini_agent_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "gemini-unmanaged-repo")
            unmanaged = repo / ".gemini/agents/local-notes.md"
            write(unmanaged, "---\nname: local-notes\n---\n\nHuman-owned agent notes.\n")

            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                unmanaged.read_text(encoding="utf-8"),
                "---\nname: local-notes\n---\n\nHuman-owned agent notes.\n",
            )

    def test_sync_refuses_to_overwrite_unmanaged_declared_gemini_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "gemini-managed-conflict-repo")
            adapter = repo / ".gemini/agents/research-orchestrator.md"
            adapter.unlink()
            lock_path = repo / ".workflow/mirror-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            del lock["gemini_adapters"][".gemini/agents/research-orchestrator.md"]
            write(lock_path, json.dumps(lock, indent=2) + "\n")
            write(adapter, "---\nname: human-owned\n---\n\nDo not overwrite me.\n")

            result = self.run_cli(repo, "sync")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "`.gemini/agents/research-orchestrator.md` no longer matches the generated Gemini adapter format",
                result.stderr,
            )

    def test_doctor_fails_when_required_state_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = build_legacy_repo(Path(temp_dir))
            init_result = self.run_cli(repo, "init")
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            (repo / ".specify/state/handoff.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- continuity-state health: fail", result.stdout)
            self.assertIn("Continuity-state error: Missing continuity-state file `.specify/state/handoff.md`.", result.stdout)

    def test_fresh_agent_recovery_after_v2_init(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "fresh-agent-repo")
            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertTrue((repo / ".workflow/workflow.json").exists())
            for relative in [
                ".specify/state/active.md",
                ".specify/state/handoff.md",
                ".specify/state/progress.md",
                ".specify/state/session.log.md",
            ]:
                self.assertTrue((repo / relative).exists())
                self.assertTrue((repo / relative).read_text(encoding="utf-8").strip())
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("What this project is", result.stdout)
            self.assertIn("Current task", result.stdout)
            self.assertIn("Next step", result.stdout)
            self.assertIn("Migration state", result.stdout)
            self.assertIn("Doctor summary", result.stdout)

    def test_workflow_status_includes_manifest_and_mirror_health_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "artifact-health-repo")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Manifest health", result.stdout)
            self.assertIn("Manifest matches the current v2 repo model.", result.stdout)
            self.assertIn("Mirror-lock/shim health", result.stdout)
            self.assertIn(
                "Mirror lock, AGENTS.md, generated shims, and managed adapters are aligned.",
                result.stdout,
            )
            self.assertIn("- Sync needed: no", result.stdout)

    def test_workflow_status_includes_health_overview_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "overview-status-repo")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Health overview", result.stdout)
            self.assertIn("- Overall health: pass", result.stdout)
            self.assertIn("- Summary: All 8 repo-owned health surfaces pass.", result.stdout)
            self.assertIn(
                "- Subsystems: command/help/docs=pass, manifest=pass, mirror-lock/shim=pass, memory=pass, continuity-state=pass, roots=pass, role-contract=pass, docs-health=pass",
                result.stdout,
            )
            self.assertIn("Role-contract health", result.stdout)
            self.assertIn("Docs health", result.stdout)
            self.assertIn("- Sync needed: no", result.stdout)
            self.assertIn("- Default-root operations safe: yes", result.stdout)
            self.assertIn("- Pre-Hermes readiness: pre-hermes-foundation-ready", result.stdout)

    def test_workflow_doctor_includes_health_overview_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "overview-doctor-repo")
            result = self.run_cli(repo, "doctor")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- health overview: pass", result.stdout)
            self.assertIn("- health summary: All 8 repo-owned health surfaces pass.", result.stdout)
            self.assertIn(
                "- health subsystems: command/help/docs=pass, manifest=pass, mirror-lock/shim=pass, memory=pass, continuity-state=pass, roots=pass, role-contract=pass, docs-health=pass",
                result.stdout,
            )
            self.assertIn("- role-contract health: pass", result.stdout)
            self.assertIn("- docs-health: pass", result.stdout)
            self.assertIn("- sync needed: no", result.stdout)
            self.assertIn("- default-root operations safe: yes", result.stdout)
            self.assertIn("- pre-hermes readiness: pre-hermes-foundation-ready", result.stdout)

    def test_workflow_status_json_is_valid_and_includes_health_overview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "status-json-repo")
            result = self.run_cli(repo, "status", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            payload = verify_json_contract_stdout(result.stdout, "status")
            self.assertEqual(payload["schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)
            self.assertEqual(payload["command"], "status")
            self.assertEqual(payload["classification"], "v2")
            self.assertIn("health_overview", payload)
            self.assertEqual(payload["health_overview"]["overall_status"], "pass")
            self.assertEqual(
                payload["health_overview"]["subsystems"],
                {
                    "command_help_docs": "pass",
                    "manifest": "pass",
                    "mirror_lock_shim": "pass",
                    "memory": "pass",
                    "continuity_state": "pass",
                    "roots": "pass",
                    "role_contract": "pass",
                    "docs_health": "pass",
                },
            )
            self.assertIn("health", payload)
            self.assertEqual(payload["health"]["role_contract"]["canonical_roles"], list(EXPECTED_CANONICAL_ROLES))
            self.assertEqual(payload["health"]["role_contract"]["reserved_roles"], list(EXPECTED_RESERVED_ROLES))
            self.assertNotIn("workflow status ::", result.stdout)

    def test_workflow_doctor_json_is_valid_on_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-json-pass-repo")
            result = self.run_cli(repo, "doctor", "--json")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(result.stderr, "")
            payload = verify_json_contract_stdout(result.stdout, "doctor")
            self.assertEqual(payload["schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)
            self.assertEqual(payload["command"], "doctor")
            self.assertEqual(payload["result_status"], "pass")
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["findings"], [])
            self.assertIn("health", payload)
            self.assertNotIn("workflow doctor ::", result.stdout)

    def test_docs_health_helper_and_current_docs_are_governed(self) -> None:
        verify_docs_health_policy()
        verify_current_docs_health(ROOT)
        verify_docs_health_over_budget_example(ROOT)
        verify_docs_health_key_files_example(ROOT)
        verify_docs_health_duplicate_heading_example(ROOT)
        verify_docs_health_gemini_claims_example(ROOT)

    def test_workflow_doctor_reports_docs_health_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "docs-health-fail-repo")
            write(repo / "README.md", "\n".join(f"line {index}" for index in range(305)) + "\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("docs-health: fail", result.stdout)
            self.assertIn("Docs-health error", result.stdout)

    def test_role_contract_helper_and_docs_are_governed(self) -> None:
        payload = verify_role_contract_helper()
        self.assertEqual(payload["schema_version"], EXPECTED_ROLE_CONTRACT_SCHEMA_VERSION)
        self.assertEqual(payload["canonical_roles"], list(EXPECTED_CANONICAL_ROLES))
        self.assertEqual(payload["reserved_roles"], list(EXPECTED_RESERVED_ROLES))
        self.assertEqual(payload["supported_harnesses"], list(EXPECTED_SUPPORTED_HARNESSES))

        with tempfile.TemporaryDirectory() as temp_dir:
            public_global_roles = Path(temp_dir) / "ROLES.md"
            write(
                public_global_roles,
                "# Canonical Roles\n\n"
                "### Architect\n"
                "- Public fixture only.\n\n"
                "### Coder\n"
                "- Public fixture only.\n\n"
                "### Verifier\n"
                "- Public fixture only.\n\n"
                "## Reserved 4th-role slot\n"
                "- Tester is reserved and must not be added to a single harness in isolation.\n",
            )
            global_text = verify_global_roles_doc(public_global_roles)
        local_text = verify_local_roles_pointer(ROOT / "ROLES.md")
        verify_role_contract_no_leak_text(global_text)
        verify_role_contract_no_leak_text(local_text)

    def test_claude_adapter_invariant_baseline_exists(self) -> None:
        registry = verify_claude_adapter_registry()
        rendered = verify_rendered_claude_adapters()
        self.assertEqual(set(registry), set(EXPECTED_CLAUDE_ADAPTERS))
        self.assertEqual(set(rendered), set(EXPECTED_CLAUDE_ADAPTERS))

    def test_workflow_sync_generates_claude_role_adapters_and_lock_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "claude-adapter-repo")
            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            files = verify_claude_adapter_files(repo)
            lock = verify_claude_adapter_lock(repo)
            self.assertEqual(set(files), set(EXPECTED_CLAUDE_ADAPTERS))
            self.assertEqual(set(lock), set(EXPECTED_CLAUDE_ADAPTERS))

    def test_workflow_doctor_reports_claude_adapter_drift_as_mirror_lock_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "claude-adapter-drift-repo")
            adapter_path = repo / ".claude/agents/architect.md"
            adapter_path.write_text(
                adapter_path.read_text(encoding="utf-8") + "\nManual drift.\n",
                encoding="utf-8",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mirror-lock/shim error", result.stdout)

    def test_opencode_adapter_invariant_baseline_exists(self) -> None:
        registry = verify_opencode_adapter_registry()
        rendered = verify_rendered_opencode_adapters()
        self.assertEqual(set(registry), set(EXPECTED_OPENCODE_ADAPTERS))
        self.assertEqual(set(rendered), set(EXPECTED_OPENCODE_ADAPTERS))

    def test_workflow_sync_generates_opencode_role_adapters_and_lock_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "opencode-adapter-repo")
            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            files = verify_opencode_adapter_files(repo)
            lock = verify_opencode_adapter_lock(repo)
            self.assertEqual(set(files), set(EXPECTED_OPENCODE_ADAPTERS))
            self.assertEqual(set(lock), set(EXPECTED_OPENCODE_ADAPTERS))

    def test_workflow_sync_preserves_unmanaged_opencode_agent_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "opencode-unmanaged-repo")
            unmanaged = repo / ".opencode/agents/local-notes.md"
            write(unmanaged, "---\ndescription: Human-owned OpenCode notes\nmode: subagent\n---\n\nDo not touch.\n")

            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                unmanaged.read_text(encoding="utf-8"),
                "---\ndescription: Human-owned OpenCode notes\nmode: subagent\n---\n\nDo not touch.\n",
            )

    def test_workflow_doctor_reports_opencode_adapter_drift_as_mirror_lock_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "opencode-adapter-drift-repo")
            adapter_path = repo / ".opencode/agents/architect.md"
            adapter_path.write_text(
                adapter_path.read_text(encoding="utf-8") + "\nManual drift.\n",
                encoding="utf-8",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mirror-lock/shim error", result.stdout)
            self.assertIn(".opencode/agents/architect.md", result.stdout)

    def test_droid_adapter_invariant_baseline_exists(self) -> None:
        registry = verify_droid_adapter_registry()
        rendered = verify_rendered_droid_adapters()
        self.assertEqual(set(registry), set(EXPECTED_DROID_ADAPTERS))
        self.assertEqual(set(rendered), set(EXPECTED_DROID_ADAPTERS))

    def test_workflow_sync_generates_droid_role_adapters_and_lock_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "droid-adapter-repo")
            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            files = verify_droid_adapter_files(repo)
            lock = verify_droid_adapter_lock(repo)
            self.assertEqual(set(files), set(EXPECTED_DROID_ADAPTERS))
            self.assertEqual(set(lock), set(EXPECTED_DROID_ADAPTERS))

    def test_workflow_sync_preserves_unmanaged_droid_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "droid-unmanaged-repo")
            unmanaged = repo / ".factory/droids/local-notes.md"
            write(
                unmanaged,
                "---\n"
                "name: local-notes\n"
                "description: Human-owned Factory Droid notes\n"
                "model: inherit\n"
                "tools: read-only\n"
                "---\n\n"
                "Do not touch.\n",
            )

            result = self.run_cli(repo, "sync")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Do not touch.", unmanaged.read_text(encoding="utf-8"))

    def test_workflow_doctor_reports_droid_adapter_drift_as_mirror_lock_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "droid-adapter-drift-repo")
            adapter_path = repo / ".factory/droids/architect.md"
            adapter_path.write_text(
                adapter_path.read_text(encoding="utf-8") + "\nManual drift.\n",
                encoding="utf-8",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mirror-lock/shim error", result.stdout)
            self.assertIn(".factory/droids/architect.md", result.stdout)

    def test_workflow_doctor_reports_role_contract_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "role-contract-health-repo")
            result = self.run_cli(repo, "doctor", "--json")
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = verify_json_contract_stdout(result.stdout, "doctor")
            role_contract = payload["health"]["role_contract"]
            self.assertEqual(role_contract["status"], "pass")
            self.assertEqual(role_contract["canonical_roles"], list(EXPECTED_CANONICAL_ROLES))
            self.assertEqual(role_contract["reserved_roles"], list(EXPECTED_RESERVED_ROLES))
            self.assertEqual(payload["health_overview"]["subsystems"]["role_contract"], "pass")
            self.assertEqual(payload["schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)

    def test_workflow_doctor_json_is_valid_on_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-json-fail-repo")
            write(repo / ".specify/memory/project.md", "")
            result = self.run_cli(repo, "doctor", "--json")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            payload = verify_json_contract_stdout(result.stdout, "doctor")
            self.assertEqual(payload["result_status"], "fail")
            self.assertFalse(payload["passed"])
            self.assertEqual(payload["health"]["memory"]["status"], "fail")
            self.assertTrue(any(finding["surface"] == "memory" for finding in payload["findings"]))
            self.assertTrue(payload["errors"])

    def test_workflow_doctor_json_preserves_warning_exit_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-json-warning-repo")
            missing_root = Path(temp_dir) / "missing-root"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [missing_root])
            result = self.run_cli(repo, "doctor", "--json", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            payload = verify_json_contract_stdout(result.stdout, "doctor")
            self.assertEqual(payload["health_overview"]["overall_status"], "warning")
            self.assertEqual(payload["health"]["roots"]["status"], "warning")
            self.assertTrue(payload["warnings"])

    def test_workflow_doctor_write_report_json_reports_write_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-json-report-repo")
            result = self.run_cli(repo, "doctor", "--write-report", "--json")
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = verify_json_contract_stdout(
                result.stdout,
                "doctor_write_report",
                expect_wrote_report=True,
                expected_drift_report_path=repo / ".specify/state/drift.md",
            )
            self.assertTrue(payload["wrote_report"])
            self.assertEqual(
                Path(payload["drift_report_path"]).resolve(),
                (repo / ".specify/state/drift.md").resolve(),
            )
            self.assertTrue((repo / ".specify/state/drift.md").exists())

    def test_workflow_roots_format_json_is_valid(self) -> None:
        result = self.run_cli(ROOT, "roots", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stderr, "")
        payload = verify_json_contract_stdout(result.stdout, "roots")
        self.assertEqual(payload["schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)
        self.assertEqual(payload["command"], "roots")
        self.assertTrue(payload["passed_validation"])
        self.assertEqual(payload["health"]["status"], "pass")

    def test_json_contract_invariant_baseline_exists(self) -> None:
        self.assertTrue(JSON_CONTRACT_INVARIANTS.exists())
        self.assertEqual(
            JSON_CONTRACT_SURFACES,
            ("status", "doctor", "doctor_write_report", "roots"),
        )

    def test_json_contract_governance_is_invariant_only(self) -> None:
        self.assertFalse(UPDATE_JSON_CONTRACT_FIXTURES.exists())
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-contract-invariant-repo")
            result = self.run_cli(repo, "status", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = verify_json_contract_stdout(result.stdout, "status")
            self.assertEqual(payload["command"], "status")

    def test_env_secret_hygiene_invariant_baseline_exists(self) -> None:
        self.assertTrue(ENV_SECRET_HYGIENE_INVARIANTS.exists())
        report = verify_env_secret_hygiene_files(ROOT)
        self.assertEqual(report["ignored_patterns"], list(EXPECTED_ENV_IGNORE_PATTERNS))
        self.assertEqual(report["env_example_keys"], list(EXPECTED_LOCAL_SECRET_ENV_KEYS))
        self.assertEqual(report["env_example_values"], EXPECTED_ENV_EXAMPLE_VALUES)

    def test_env_secret_hygiene_key_inspection_only_returns_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            write(
                env_path,
                "# comment\n"
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=top-secret-value\n"
                "\n"
                "IGNORED_LINE_WITHOUT_EQUALS\n",
            )
            self.assertEqual(inspect_env_file_keys(env_path), EXPECTED_LOCAL_SECRET_ENV_KEYS)

    def test_env_secret_hygiene_missing_ignore_pattern_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".gitignore", ".env\n.env.*\n")
            write(
                repo / ".env.example",
                "# local-only DashScope credential placeholder\n"
                "# does not make DashScope network calls\n"
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=<set-locally>\n",
            )
            with self.assertRaises(AssertionError) as error:
                verify_env_secret_hygiene_files(repo)
        self.assertIn("`.gitignore`", str(error.exception))
        self.assertIn("!.env.example", str(error.exception))

    def test_env_secret_hygiene_example_value_drift_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".gitignore", ".env\n.env.*\n!.env.example\n")
            write(
                repo / ".env.example",
                "# local-only DashScope credential placeholder\n"
                "# does not make DashScope network calls\n"
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=not-a-placeholder\n",
            )
            with self.assertRaises(AssertionError) as error:
                verify_env_secret_hygiene_files(repo)
        self.assertIn("`.env.example` key `DASHSCOPE_API_KEY_WORKFLOW_MANAGER`", str(error.exception))

    def test_dashscope_local_readiness_helper_reports_redacted_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-readiness-sentinel"
            write(
                repo / ".env",
                f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(set(payload.keys()), set(EXPECTED_DASHSCOPE_LOCAL_READINESS_KEYS))
            self.assertTrue(payload["env_exists"])
            self.assertEqual(payload["expected_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertEqual(payload["active_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertEqual(payload["fallback_only_variable_names"], list(EXPECTED_FALLBACK_ONLY_SECRET_ENV_KEYS))
            self.assertEqual(payload["optional_model_variable_names"], list(EXPECTED_OPTIONAL_MODEL_ENV_KEYS))
            self.assertEqual(payload["fallback_model_variable_names"], list(EXPECTED_FALLBACK_MODEL_ENV_KEYS))
            self.assertEqual(payload["reserved_variable_names"], list(EXPECTED_RESERVED_SECRET_ENV_KEYS))
            self.assertEqual(payload["present_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertEqual(payload["missing_variable_names"], [])
            self.assertEqual(payload["present_model_variable_names"], [])
            self.assertEqual(
                payload["missing_model_variable_names"],
                list(EXPECTED_OPTIONAL_MODEL_ENV_KEYS + EXPECTED_FALLBACK_MODEL_ENV_KEYS),
            )
            self.assertTrue(payload["non_empty_flags"]["DASHSCOPE_API_KEY_WORKFLOW_MANAGER"])
            self.assertEqual(payload["selected_api_key_name"], "DASHSCOPE_API_KEY_WORKFLOW_MANAGER")
            self.assertEqual(payload["selected_api_key_category"], "active")
            self.assertEqual(payload["precedence_policy"], EXPECTED_DASHSCOPE_PRECEDENCE_POLICY)
            self.assertEqual(payload["generic_api_key_policy"], EXPECTED_DASHSCOPE_GENERIC_API_KEY_POLICY)
            self.assertEqual(payload["intended_model_name"], EXPECTED_DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_name"], EXPECTED_DASHSCOPE_INTENDED_MODEL)
            self.assertIsNone(payload["selected_model_variable_name"])
            self.assertIsNone(payload["selected_model_variable_category"])
            self.assertEqual(payload["model_precedence_policy"], EXPECTED_DASHSCOPE_MODEL_PRECEDENCE_POLICY)
            self.assertEqual(payload["model_selection_policy"], EXPECTED_DASHSCOPE_MODEL_SELECTION_POLICY)
            self.assertEqual(payload["model_policy_status"], "default")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])
            self.assertEqual(
                payload["redacted_values"],
                {"DASHSCOPE_API_KEY_WORKFLOW_MANAGER": DASHSCOPE_REDACTED_VALUE},
            )
            self.assertTrue(payload["all_values_redacted"])
            self.assertTrue(payload["local_config_ready"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])
            safe_dump = json.dumps(payload, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertIn(DASHSCOPE_REDACTED_VALUE, safe_dump)

    def test_dashscope_local_readiness_helper_reports_missing_key_without_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "UNRELATED_TOKEN=present\n")
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertTrue(payload["env_exists"])
            self.assertEqual(payload["present_variable_names"], [])
            self.assertEqual(payload["missing_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertFalse(payload["non_empty_flags"]["DASHSCOPE_API_KEY_WORKFLOW_MANAGER"])
            self.assertIsNone(payload["selected_api_key_name"])
            self.assertIsNone(payload["selected_api_key_category"])
            self.assertEqual(payload["selected_model_name"], EXPECTED_DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "default")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])
            self.assertEqual(payload["redacted_values"], {})
            self.assertFalse(payload["local_config_ready"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_local_readiness_helper_reports_missing_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertFalse(payload["env_exists"])
            self.assertEqual(payload["present_variable_names"], [])
            self.assertEqual(payload["missing_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertFalse(payload["non_empty_flags"]["DASHSCOPE_API_KEY_WORKFLOW_MANAGER"])
            self.assertIsNone(payload["selected_api_key_name"])
            self.assertIsNone(payload["selected_api_key_category"])
            self.assertEqual(payload["selected_model_name"], EXPECTED_DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "default")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])
            self.assertEqual(payload["redacted_values"], {})
            self.assertFalse(payload["local_config_ready"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_env_key_policy_is_explicit_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-policy-sentinel"
            write(
                repo / ".env",
                "\n".join(
                    (
                        f"{DASHSCOPE_ACTIVE_ENV_KEYS[0]}={sentinel}",
                        "DASHSCOPE_API_KEY" "=generic-sentinel",
                        "QWEN_MODEL=qwen-max",
                    )
                )
                + "\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["variable_categories"], EXPECTED_DASHSCOPE_ENV_KEY_CATEGORIES)
            self.assertEqual(payload["selected_api_key_name"], DASHSCOPE_ACTIVE_ENV_KEYS[0])
            self.assertEqual(payload["selected_api_key_category"], "active")
            self.assertEqual(payload["precedence_policy"], EXPECTED_DASHSCOPE_PRECEDENCE_POLICY)
            self.assertEqual(payload["generic_api_key_policy"], EXPECTED_DASHSCOPE_GENERIC_API_KEY_POLICY)
            self.assertEqual(payload["selected_model_name"], "qwen-max")
            self.assertEqual(payload["selected_model_variable_name"], "QWEN_MODEL")
            self.assertEqual(payload["selected_model_variable_category"], "optional")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertTrue(payload["local_config_ready"])
            safe_dump = json.dumps(payload, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("generic-sentinel", safe_dump)

    def test_dashscope_env_key_policy_treats_generic_api_key_as_fallback_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY" "=generic-only\n")
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["present_variable_names"], ["DASHSCOPE_API_KEY"])
            self.assertEqual(payload["missing_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertEqual(payload["selected_api_key_name"], "DASHSCOPE_API_KEY")
            self.assertEqual(payload["selected_api_key_category"], "fallback-only")
            self.assertTrue(payload["non_empty_flags"]["DASHSCOPE_API_KEY"])
            self.assertFalse(payload["local_config_ready"])

    def test_dashscope_env_key_policy_prefers_specific_api_key_over_generic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "\n".join(
                    (
                        "DASHSCOPE_API_KEY" "=generic-present",
                        "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=specific-present",
                    )
                )
                + "\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(
                payload["present_variable_names"],
                ["DASHSCOPE_API_KEY_WORKFLOW_MANAGER", "DASHSCOPE_API_KEY"],
            )
            self.assertEqual(payload["selected_api_key_name"], "DASHSCOPE_API_KEY_WORKFLOW_MANAGER")
            self.assertEqual(payload["selected_api_key_category"], "active")
            self.assertTrue(payload["local_config_ready"])

    def test_dashscope_env_key_policy_keeps_reserved_keys_non_activating(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "\n".join(f"{key}=present" for key in DASHSCOPE_RESERVED_ENV_KEYS) + "\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["present_variable_names"], list(DASHSCOPE_RESERVED_ENV_KEYS))
            self.assertEqual(payload["missing_variable_names"], list(EXPECTED_ACTIVE_SECRET_ENV_KEYS))
            self.assertIsNone(payload["selected_api_key_name"])
            self.assertIsNone(payload["selected_api_key_category"])
            for key in DASHSCOPE_RESERVED_ENV_KEYS:
                self.assertTrue(payload["non_empty_flags"][key])
            self.assertFalse(payload["local_config_ready"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_model_policy_is_explicit_and_defaults_to_qwen36_plus(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["intended_model_name"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_name"], DASHSCOPE_INTENDED_MODEL)
            self.assertIsNone(payload["selected_model_variable_name"])
            self.assertIsNone(payload["selected_model_variable_category"])
            self.assertEqual(payload["model_precedence_policy"], EXPECTED_DASHSCOPE_MODEL_PRECEDENCE_POLICY)
            self.assertEqual(payload["model_selection_policy"], EXPECTED_DASHSCOPE_MODEL_SELECTION_POLICY)
            self.assertEqual(payload["model_policy_status"], "default")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])
            self.assertTrue(payload["local_config_ready"])

    def test_dashscope_model_policy_accepts_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["present_model_variable_names"], ["QWEN_MODEL"])
            self.assertEqual(payload["selected_model_name"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_variable_name"], "QWEN_MODEL")
            self.assertEqual(payload["selected_model_variable_category"], "optional")
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_model_policy_accepts_dashscope_model_fallback_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["present_model_variable_names"], ["DASHSCOPE_MODEL"])
            self.assertEqual(payload["selected_model_name"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_variable_name"], "DASHSCOPE_MODEL")
            self.assertEqual(payload["selected_model_variable_category"], "fallback-only")
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_model_policy_prefers_qwen_model_over_dashscope_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n"
                "DASHSCOPE_MODEL=other-model\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["present_model_variable_names"], ["QWEN_MODEL", "DASHSCOPE_MODEL"])
            self.assertEqual(payload["selected_model_name"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_variable_name"], "QWEN_MODEL")
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])

    def test_dashscope_model_policy_classifies_unexpected_model_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            payload = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            self.assertEqual(payload["selected_model_name"], "qwen-surprise")
            self.assertEqual(payload["selected_model_variable_name"], "QWEN_MODEL")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertTrue(payload["local_config_ready"])

    def test_dashscope_offline_request_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_REQUEST_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_REQUEST_KEYS,
            (
                "request_shape_version",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "selected_model_variable_name",
                "selected_model_variable_category",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "request_policy",
                "input_summary",
                "forbidden_fields",
            ),
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SOURCE, "hermes_inventory")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_MODE, "offline_request_shape_only")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INTENDED_MODEL, "qwen3.6-plus")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
            (
                "source_schema_version",
                "source_command",
                "source_mode",
                "source_dry_run",
                "inventory_summary",
                "classification_counts",
                "root_count",
                "total_project_count",
                "root_classification_counts",
                "warning_count",
                "error_count",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS,
            DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS,
        )

    def test_dashscope_offline_request_shape_is_explicit_and_excludes_sensitive_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-request-shape-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            payload = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            self.assertEqual(payload["source"], EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SOURCE)
            self.assertEqual(payload["mode"], EXPECTED_DASHSCOPE_OFFLINE_REQUEST_MODE)
            self.assertEqual(payload["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INTENDED_MODEL)
            self.assertEqual(payload["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "default")
            self.assertTrue(payload["local_config_ready"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])
            self.assertEqual(payload["request_policy"], EXPECTED_DASHSCOPE_OFFLINE_REQUEST_POLICY)
            self.assertEqual(payload["input_summary"]["source_command"], "hermes_inventory")
            self.assertEqual(payload["input_summary"]["root_count"], 1)
            self.assertEqual(payload["input_summary"]["total_project_count"], 1)
            self.assertEqual(payload["input_summary"]["root_classification_counts"], {"configured-root": 1})
            safe_dump = json.dumps(payload, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("project_source_code", payload["input_summary"])
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)

    def test_dashscope_offline_request_shape_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            payload = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_variable_name"], "QWEN_MODEL")
            self.assertEqual(payload["selected_model_variable_category"], "optional")
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_request_shape_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            payload = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["selected_model_variable_name"], "DASHSCOPE_MODEL")
            self.assertEqual(payload["selected_model_variable_category"], "fallback-only")
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_request_shape_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            payload = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["selected_model_variable_name"], "QWEN_MODEL")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_offline_request_shape_rejects_forbidden_metadata_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            with self.assertRaisesRegex(ValueError, "forbidden fields"):
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                    candidate_metadata={"api_key": "sentinel-value"},
                )
            with self.assertRaisesRegex(ValueError, "forbidden fields"):
                sanitize_dashscope_request_metadata({"project_source_code": "print('hi')"})

    def test_dashscope_offline_prompt_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_PROMPT_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FIELDS,
            (
                "prompt_template_version",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "request_shape_version",
                "request_shape_source",
                "request_shape_mode",
                "request_shape_scope",
                "allowed_sections",
                "required_sections",
                "forbidden_sections",
                "forbidden_content",
                "prompt_policy",
                "rendered_sections",
            ),
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_SOURCE, "hermes_inventory")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_MODE, "offline_prompt_template_only")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_INTENDED_MODEL, "qwen3.6-plus")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
            (
                "system_role",
                "task",
                "source_of_truth",
                "inventory_summary",
                "classification_counts",
                "safety_constraints",
                "forbidden_actions",
                "expected_output_shape",
                "redaction_policy",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
        )
        self.assertIn("hidden reasoning requests", EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT)
        self.assertIn("migration_write_instructions", EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS)

    def test_dashscope_offline_prompt_template_is_explicit_and_excludes_sensitive_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-prompt-template-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            payload = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            self.assertEqual(payload["source"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_SOURCE)
            self.assertEqual(payload["mode"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_MODE)
            self.assertEqual(payload["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_INTENDED_MODEL)
            self.assertEqual(payload["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "default")
            self.assertTrue(payload["local_config_ready"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])
            self.assertFalse(payload["qwen_dashscope_enabled"])
            self.assertFalse(payload["graphify_enabled"])
            self.assertFalse(payload["migration_writes_enabled"])
            safe_dump = json.dumps(payload, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)
            self.assertEqual(
                tuple(payload["allowed_sections"]),
                EXPECTED_DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
            )
            self.assertEqual(
                tuple(payload["required_sections"]),
                EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
            )

    def test_dashscope_offline_prompt_template_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            payload = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_prompt_template_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            payload = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_prompt_template_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            payload = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_offline_prompt_template_rejects_forbidden_and_extra_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            with self.assertRaisesRegex(ValueError, "forbidden sections"):
                build_hermes_qwen_offline_prompt_template(
                    request_shape,
                    candidate_sections={"hidden_reasoning": "Do hidden reasoning."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden sections"):
                build_hermes_qwen_offline_prompt_template(
                    request_shape,
                    candidate_sections={"migration_write_instructions": "Write migrations."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden sections"):
                build_hermes_qwen_offline_prompt_template(
                    request_shape,
                    candidate_sections={"target_repo_file_contents": "contents"},
                )
            with self.assertRaisesRegex(ValueError, "custom section content"):
                build_hermes_qwen_offline_prompt_template(
                    request_shape,
                    candidate_sections={"system_role": "Custom role text"},
                )
            with self.assertRaisesRegex(ValueError, "extra sections"):
                sanitize_dashscope_prompt_section_overrides({"extra_context": "not allowed"})

    def test_dashscope_offline_prompt_preview_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_PROMPT_PREVIEW_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_FIELDS,
            (
                "prompt_preview_version",
                "preview_type",
                "source",
                "mode",
                "preview_only",
                "prompt_execution_enabled",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "request_shape_version",
                "request_shape_source",
                "request_shape_mode",
                "prompt_template_version",
                "prompt_template_mode",
                "section_order",
                "sections",
                "assembled_prompt_preview",
                "redaction_policy",
                "forbidden_content_policy",
                "input_summary",
            ),
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE, "assembled_prompt_preview")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE, "hermes_inventory")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE, "offline_prompt_preview_only")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INTENDED_MODEL, "qwen3.6-plus")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER,
            EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
        )

    def test_dashscope_offline_prompt_preview_is_explicit_deterministic_and_excludes_sensitive_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-prompt-preview-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            first = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            second = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            self.assertEqual(first["source"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE)
            self.assertEqual(first["mode"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE)
            self.assertEqual(first["preview_type"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE)
            self.assertTrue(first["preview_only"])
            self.assertFalse(first["prompt_execution_enabled"])
            self.assertFalse(first["runtime_enabled"])
            self.assertFalse(first["network_calls_allowed"])
            self.assertEqual(first["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INTENDED_MODEL)
            self.assertEqual(first["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INTENDED_MODEL)
            self.assertEqual(tuple(first["section_order"]), EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER)
            self.assertEqual(first["section_order"], second["section_order"])
            self.assertEqual(first["sections"], second["sections"])
            self.assertEqual(first["assembled_prompt_preview"], second["assembled_prompt_preview"])
            safe_dump = json.dumps(first, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)
            self.assertIn("## System Role", first["assembled_prompt_preview"])
            self.assertIn("## Redaction Policy", first["assembled_prompt_preview"])

    def test_dashscope_offline_prompt_preview_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            payload = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_prompt_preview_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            payload = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_prompt_preview_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            payload = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["prompt_execution_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_offline_prompt_preview_rejects_forbidden_and_extra_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            with self.assertRaisesRegex(ValueError, "forbidden sections"):
                build_hermes_qwen_offline_prompt_preview(
                    request_shape,
                    prompt_template,
                    candidate_sections={"hidden_reasoning": "Do hidden reasoning."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden sections"):
                build_hermes_qwen_offline_prompt_preview(
                    request_shape,
                    prompt_template,
                    candidate_sections={"migration_write_instructions": "Write migrations."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden sections"):
                build_hermes_qwen_offline_prompt_preview(
                    request_shape,
                    prompt_template,
                    candidate_sections={"target_repo_file_contents": "contents"},
                )
            with self.assertRaisesRegex(ValueError, "custom section content"):
                build_hermes_qwen_offline_prompt_preview(
                    request_shape,
                    prompt_template,
                    candidate_sections={"system_role": "Custom role text"},
                )
            with self.assertRaisesRegex(ValueError, "extra sections"):
                sanitize_dashscope_prompt_preview_sections({"preview_notes": "not allowed"})

    def test_dashscope_offline_response_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_RESPONSE_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELDS,
            (
                "response_shape_version",
                "response_type",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "preview_type",
                "prompt_preview_mode",
                "preview_only",
                "response_explanatory_only",
                "live_response_parsing_enabled",
                "allowed_response_fields",
                "required_response_fields",
                "response_field_order",
                "response_slots",
                "forbidden_response_fields",
                "source_of_truth_policy",
                "forbidden_output_policy",
                "redaction_policy",
                "input_summary",
            ),
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_TYPE, "explanatory_response_shape")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE, "hermes_inventory")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_MODE, "offline_response_shape_only")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INTENDED_MODEL, "qwen3.6-plus")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER,
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
        )

    def test_dashscope_offline_response_shape_is_explicit_and_excludes_sensitive_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-response-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            first = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            second = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            self.assertEqual(first["source"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE)
            self.assertEqual(first["mode"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_MODE)
            self.assertEqual(first["response_type"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_TYPE)
            self.assertTrue(first["response_explanatory_only"])
            self.assertFalse(first["live_response_parsing_enabled"])
            self.assertFalse(first["runtime_enabled"])
            self.assertFalse(first["network_calls_allowed"])
            self.assertEqual(first["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INTENDED_MODEL)
            self.assertEqual(first["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INTENDED_MODEL)
            self.assertEqual(
                tuple(first["allowed_response_fields"]),
                EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
            )
            self.assertEqual(
                tuple(first["required_response_fields"]),
                EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
            )
            self.assertEqual(tuple(first["response_field_order"]), EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER)
            self.assertEqual(first["response_field_order"], second["response_field_order"])
            self.assertEqual(first["response_slots"], second["response_slots"])
            safe_dump = json.dumps(first, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)
            self.assertIn("explanatory only", first["source_of_truth_policy"])

    def test_dashscope_offline_response_shape_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            payload = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_response_shape_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            payload = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_response_shape_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            payload = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["live_response_parsing_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_offline_response_shape_rejects_forbidden_and_extra_output_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            with self.assertRaisesRegex(ValueError, "forbidden output fields"):
                build_hermes_qwen_offline_response_shape(
                    prompt_preview,
                    candidate_output={"hidden_reasoning": "Reveal chain-of-thought."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden output fields"):
                build_hermes_qwen_offline_response_shape(
                    prompt_preview,
                    candidate_output={"migration_write_instructions": "Apply migration writes."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden output fields"):
                build_hermes_qwen_offline_response_shape(
                    prompt_preview,
                    candidate_output={"target_repo_modification_instructions": "Write to target repos."},
                )
            with self.assertRaisesRegex(ValueError, "forbidden output fields"):
                build_hermes_qwen_offline_response_shape(
                    prompt_preview,
                    candidate_output={"source_of_truth_override": "Qwen output is source of truth."},
                )
            with self.assertRaisesRegex(ValueError, "custom response slot content"):
                build_hermes_qwen_offline_response_shape(
                    prompt_preview,
                    candidate_output={"analysis_summary": "Custom analysis summary."},
                )
            with self.assertRaisesRegex(ValueError, "extra output fields"):
                sanitize_dashscope_response_slots({"response_notes": "not allowed"})

    def test_dashscope_offline_response_consumer_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_RESPONSE_CONSUMER_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FIELDS,
            (
                "response_consumer_policy_version",
                "consumer_type",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "response_shape_version",
                "response_type",
                "response_mode",
                "response_explanatory_only",
                "live_response_parsing_enabled",
                "allowed_evidence_reference_categories",
                "response_fields_requiring_evidence",
                "required_evidence_rules",
                "forbidden_evidence_references",
                "consumer_authority_policy",
                "ungrounded_recommendation_policy",
                "uncertainty_policy",
                "simulated_examples_in_memory_only",
                "simulated_examples",
                "redaction_policy",
                "input_summary",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
            "evidence_slot_response_consumer_policy",
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE, "hermes_inventory")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
            "offline_response_consumer_policy_only",
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INTENDED_MODEL,
            "qwen3.6-plus",
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
            (
                "risk_summary",
                "recommended_next_step",
                "required_human_review",
                "blocked_actions",
            ),
        )

    def test_dashscope_offline_response_consumer_policy_is_explicit_and_uses_in_memory_simulations_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-response-consumer-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            first = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            second = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            self.assertEqual(first["source"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE)
            self.assertEqual(first["mode"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE)
            self.assertEqual(first["consumer_type"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE)
            self.assertTrue(first["response_explanatory_only"])
            self.assertFalse(first["live_response_parsing_enabled"])
            self.assertFalse(first["runtime_enabled"])
            self.assertFalse(first["network_calls_allowed"])
            self.assertTrue(first["simulated_examples_in_memory_only"])
            self.assertEqual(first["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INTENDED_MODEL)
            self.assertEqual(first["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INTENDED_MODEL)
            self.assertEqual(
                tuple(first["allowed_evidence_reference_categories"]),
                EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
            )
            self.assertEqual(
                tuple(first["response_fields_requiring_evidence"]),
                EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
            )
            self.assertEqual(
                tuple(example["example_name"] for example in first["simulated_examples"]),
                EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_NAMES,
            )
            self.assertEqual(first["simulated_examples"], second["simulated_examples"])
            safe_dump = json.dumps(first, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)
            self.assertIn("explanatory", json.dumps(first["consumer_authority_policy"], sort_keys=True))

    def test_dashscope_offline_response_consumer_policy_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            payload = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_response_consumer_policy_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            payload = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_response_consumer_policy_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            payload = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["live_response_parsing_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_offline_response_consumer_policy_rejects_ungrounded_and_unsafe_simulated_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )

            valid_examples = sanitize_dashscope_response_consumer_examples(
                [
                    {
                        "example_name": "grounded_accept_case",
                        "grounding_status": "grounded",
                        "expected_consumer_action": "accept",
                        "response_fields_present": [
                            "analysis_summary",
                            "risk_summary",
                            "recommended_next_step",
                            "blocked_actions",
                            "required_human_review",
                        ],
                        "evidence_references": {
                            "risk_summary": ["hermes_warning_count"],
                            "recommended_next_step": ["status_health_overview"],
                            "required_human_review": ["doctor_result_status"],
                            "blocked_actions": ["dashscope_readiness_policy"],
                        },
                        "invalid_evidence_references": [],
                        "forbidden_or_unexpected_fields": [],
                        "consumer_reason": "Accept because every governed recommendation field is grounded.",
                    }
                ]
            )
            self.assertEqual(valid_examples[0]["expected_consumer_action"], "accept")
            self.assertEqual(
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=valid_examples,
                ).to_safe_dict()["simulated_examples"][0]["example_name"],
                "grounded_accept_case",
            )

            with self.assertRaisesRegex(ValueError, "recommended_next_step"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "missing_evidence_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["recommended_next_step"],
                            "evidence_references": {},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": [],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "unknown evidence references"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "unknown_evidence_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["risk_summary"],
                            "evidence_references": {"risk_summary": ["made_up_reference"]},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": [],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "source_of_truth_override"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "source_of_truth_override_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["source_of_truth_policy"],
                            "evidence_references": {},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": ["source_of_truth_override"],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "migration_write_instructions"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "migration_write_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["blocked_actions"],
                            "evidence_references": {"blocked_actions": ["dashscope_readiness_policy"]},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": ["migration_write_instructions"],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "hidden_reasoning"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "hidden_reasoning_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["analysis_summary"],
                            "evidence_references": {},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": ["hidden_reasoning"],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "api_key_material"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "secret_like_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["redaction_policy"],
                            "evidence_references": {},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": ["api_key_material"],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "target_repo_file_contents"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "target_repo_file_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["analysis_summary"],
                            "evidence_references": {},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": ["target_repo_file_contents"],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "response_notes"):
                build_hermes_qwen_offline_response_consumer_policy(
                    response_shape,
                    candidate_examples=[
                        {
                            "example_name": "unsafe_extra_field_case",
                            "grounding_status": "grounded",
                            "expected_consumer_action": "accept",
                            "response_fields_present": ["analysis_summary"],
                            "evidence_references": {},
                            "invalid_evidence_references": [],
                            "forbidden_or_unexpected_fields": ["response_notes"],
                            "consumer_reason": "Should be accepted.",
                        }
                    ],
                )

    def test_dashscope_offline_consumer_decision_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_CONSUMER_DECISION_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_FIELDS,
            (
                "consumer_decision_policy_version",
                "decision_type",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "response_consumer_policy_version",
                "consumer_policy_type",
                "consumer_policy_mode",
                "response_explanatory_only",
                "live_response_parsing_enabled",
                "allowed_decision_states",
                "allowed_decision_inputs",
                "required_human_review_rules",
                "confidence_policy",
                "ready_to_migrate_claim_policy",
                "decision_authority_policy",
                "decision_examples_in_memory_only",
                "simulated_decision_examples",
                "redaction_policy",
                "input_summary",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
            "consumer_decision_human_review_policy",
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE, "hermes_inventory")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
            "offline_consumer_decision_policy_only",
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INTENDED_MODEL,
            "qwen3.6-plus",
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
            (
                "accept_explanatory_only",
                "reject_unsafe",
                "escalate_human_review",
                "requires_deterministic_recheck",
                "blocked_by_missing_evidence",
                "blocked_by_policy_violation",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
            (
                "evidence_validation_result",
                "missing_evidence_fields",
                "unknown_evidence_references",
                "forbidden_content_flags",
                "source_of_truth_override_flag",
                "migration_write_authorization_flag",
                "ready_to_migrate_claim_flag",
                "confidence_state",
                "required_human_review_flag",
                "blocked_actions_present",
                "deterministic_reference_categories",
                "model_policy_status",
                "deterministic_mismatch_flag",
            ),
        )

    def test_dashscope_offline_consumer_decision_policy_is_explicit_and_uses_in_memory_examples_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-consumer-decision-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            first = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            second = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            self.assertEqual(first["source"], EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE)
            self.assertEqual(first["mode"], EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE)
            self.assertEqual(first["decision_type"], EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE)
            self.assertTrue(first["response_explanatory_only"])
            self.assertFalse(first["live_response_parsing_enabled"])
            self.assertFalse(first["runtime_enabled"])
            self.assertFalse(first["network_calls_allowed"])
            self.assertTrue(first["decision_examples_in_memory_only"])
            self.assertEqual(first["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INTENDED_MODEL)
            self.assertEqual(first["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INTENDED_MODEL)
            self.assertEqual(tuple(first["allowed_decision_states"]), EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES)
            self.assertEqual(tuple(first["allowed_decision_inputs"]), EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS)
            self.assertEqual(
                tuple(example["example_name"] for example in first["simulated_decision_examples"]),
                EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_NAMES,
            )
            self.assertEqual(first["simulated_decision_examples"], second["simulated_decision_examples"])
            safe_dump = json.dumps(first, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)
            self.assertIn("explanatory", json.dumps(first["decision_authority_policy"], sort_keys=True))

    def test_dashscope_offline_consumer_decision_policy_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            payload = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_consumer_decision_policy_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            payload = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_consumer_decision_policy_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            payload = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["live_response_parsing_enabled"])
            self.assertFalse(payload["network_calls_allowed"])

    def test_dashscope_offline_consumer_decision_policy_classifies_states_and_review_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            payload = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            examples = {
                example["example_name"]: example
                for example in payload["simulated_decision_examples"]
            }
            self.assertEqual(
                examples["valid_grounded_explanatory_response"]["expected_decision_state"],
                "accept_explanatory_only",
            )
            self.assertFalse(examples["valid_grounded_explanatory_response"]["requires_human_review"])
            self.assertEqual(
                examples["missing_evidence_for_recommendation"]["expected_decision_state"],
                "blocked_by_missing_evidence",
            )
            self.assertEqual(
                examples["unknown_evidence_reference"]["expected_decision_state"],
                "requires_deterministic_recheck",
            )
            self.assertTrue(examples["unknown_evidence_reference"]["requires_deterministic_recheck"])
            self.assertEqual(
                examples["source_of_truth_override_claim"]["expected_decision_state"],
                "reject_unsafe",
            )
            self.assertEqual(
                examples["migration_write_authorization"]["expected_decision_state"],
                "reject_unsafe",
            )
            self.assertEqual(
                examples["ready_to_migrate_without_gates"]["expected_decision_state"],
                "reject_unsafe",
            )
            self.assertEqual(
                examples["hidden_reasoning_output"]["expected_decision_state"],
                "reject_unsafe",
            )
            self.assertEqual(
                examples["target_repo_file_contents"]["expected_decision_state"],
                "reject_unsafe",
            )
            self.assertEqual(
                examples["low_confidence_requires_human_review"]["expected_decision_state"],
                "escalate_human_review",
            )
            self.assertTrue(examples["low_confidence_requires_human_review"]["requires_human_review"])
            self.assertEqual(
                examples["missing_confidence_requires_recheck"]["expected_decision_state"],
                "requires_deterministic_recheck",
            )
            self.assertTrue(examples["missing_confidence_requires_recheck"]["requires_deterministic_recheck"])
            self.assertEqual(
                examples["confidence_cannot_override_missing_evidence"]["expected_decision_state"],
                "blocked_by_missing_evidence",
            )
            self.assertEqual(
                examples["deterministic_mismatch_requires_human_review"]["expected_decision_state"],
                "escalate_human_review",
            )
            self.assertTrue(examples["deterministic_mismatch_requires_human_review"]["requires_human_review"])
            self.assertEqual(
                examples["unsafe_extra_field"]["expected_decision_state"],
                "blocked_by_policy_violation",
            )
            self.assertTrue(examples["unsafe_extra_field"]["requires_human_review"])

    def test_dashscope_offline_consumer_decision_policy_rejects_unsafe_and_drifted_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )

            valid_examples = sanitize_dashscope_consumer_decision_examples(
                [
                    {
                        "example_name": "grounded_accept_case",
                        "decision_inputs": {
                            "evidence_validation_result": "grounded",
                            "missing_evidence_fields": [],
                            "unknown_evidence_references": [],
                            "forbidden_content_flags": [],
                            "source_of_truth_override_flag": False,
                            "migration_write_authorization_flag": False,
                            "ready_to_migrate_claim_flag": False,
                            "confidence_state": "high",
                            "required_human_review_flag": False,
                            "blocked_actions_present": True,
                            "deterministic_reference_categories": [
                                "hermes_warning_count",
                                "status_health_overview",
                            ],
                            "model_policy_status": "default",
                            "deterministic_mismatch_flag": False,
                        },
                        "expected_decision_state": "accept_explanatory_only",
                        "requires_human_review": False,
                        "requires_deterministic_recheck": False,
                        "decision_reason": "Accept only as explanatory output because deterministic evidence is present.",
                    }
                ]
            )
            self.assertEqual(valid_examples[0]["expected_decision_state"], "accept_explanatory_only")
            self.assertEqual(
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=valid_examples,
                ).to_safe_dict()["simulated_decision_examples"][0]["example_name"],
                "grounded_accept_case",
            )

            with self.assertRaisesRegex(ValueError, "unsupported missing-evidence fields"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "bad_missing_evidence_case",
                            "decision_inputs": {
                                "evidence_validation_result": "missing-evidence",
                                "missing_evidence_fields": ["analysis_summary"],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": [],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["hermes_warning_count"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "blocked_by_missing_evidence",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be blocked.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "unsupported deterministic reference categories"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "unknown_evidence_case",
                            "decision_inputs": {
                                "evidence_validation_result": "unknown-evidence",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": ["repo_text_body"],
                                "forbidden_content_flags": [],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["repo_text_body"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "requires_deterministic_recheck",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": True,
                            "decision_reason": "Should require recheck.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `reject_unsafe`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "source_of_truth_override_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["source_of_truth_override"],
                                "source_of_truth_override_flag": True,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["status_health_overview"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `reject_unsafe`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "migration_write_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["migration_write_instructions"],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": True,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": True,
                                "deterministic_reference_categories": ["dashscope_readiness_policy"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `reject_unsafe`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "ready_to_migrate_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["ready_to_migrate_without_deterministic_gates"],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": True,
                                "confidence_state": "high",
                                "required_human_review_flag": True,
                                "blocked_actions_present": True,
                                "deterministic_reference_categories": ["doctor_result_status"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `reject_unsafe`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "hidden_reasoning_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["hidden_reasoning"],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["status_health_overview"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `reject_unsafe`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "secret_like_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["api_key_material"],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["dashscope_readiness_policy"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `reject_unsafe`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "target_repo_file_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["target_repo_file_contents"],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["hermes_inventory_summary"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `escalate_human_review`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "low_confidence_case",
                            "decision_inputs": {
                                "evidence_validation_result": "grounded",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": [],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "low",
                                "required_human_review_flag": False,
                                "blocked_actions_present": True,
                                "deterministic_reference_categories": ["doctor_result_status"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `requires_deterministic_recheck`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "missing_confidence_case",
                            "decision_inputs": {
                                "evidence_validation_result": "grounded",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": [],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "missing",
                                "required_human_review_flag": False,
                                "blocked_actions_present": True,
                                "deterministic_reference_categories": ["doctor_result_status"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `blocked_by_missing_evidence`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "confidence_override_case",
                            "decision_inputs": {
                                "evidence_validation_result": "missing-evidence",
                                "missing_evidence_fields": ["risk_summary"],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": [],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": False,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["status_health_overview"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `escalate_human_review`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "deterministic_mismatch_case",
                            "decision_inputs": {
                                "evidence_validation_result": "deterministic-mismatch",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": [],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": True,
                                "blocked_actions_present": True,
                                "deterministic_reference_categories": [
                                    "status_health_overview",
                                    "doctor_result_status",
                                ],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": True,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )
            with self.assertRaisesRegex(ValueError, "expected `accept_explanatory_only` but the governed decision rules classify it as `blocked_by_policy_violation`"):
                build_hermes_qwen_offline_consumer_decision_policy(
                    response_consumer,
                    candidate_examples=[
                        {
                            "example_name": "unsafe_extra_field_case",
                            "decision_inputs": {
                                "evidence_validation_result": "policy-violation",
                                "missing_evidence_fields": [],
                                "unknown_evidence_references": [],
                                "forbidden_content_flags": ["response_notes"],
                                "source_of_truth_override_flag": False,
                                "migration_write_authorization_flag": False,
                                "ready_to_migrate_claim_flag": False,
                                "confidence_state": "high",
                                "required_human_review_flag": True,
                                "blocked_actions_present": False,
                                "deterministic_reference_categories": ["status_health_overview"],
                                "model_policy_status": "default",
                                "deterministic_mismatch_flag": False,
                            },
                            "expected_decision_state": "accept_explanatory_only",
                            "requires_human_review": False,
                            "requires_deterministic_recheck": False,
                            "decision_reason": "Should be accepted.",
                        }
                    ],
                )

    def test_dashscope_offline_escalation_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_ESCALATION_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FIELDS,
            (
                "escalation_policy_version",
                "escalation_type",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "report_writing_enabled",
                "consumer_decision_policy_version",
                "decision_type",
                "decision_mode",
                "response_explanatory_only",
                "live_response_parsing_enabled",
                "allowed_acceptance_threshold_categories",
                "allowed_escalation_fields",
                "required_escalation_fields",
                "required_human_review_rules",
                "confidence_messaging_policy",
                "blocked_action_summary_policy",
                "ready_to_migrate_claim_policy",
                "source_of_truth_policy",
                "forbidden_message_content",
                "redaction_policy",
                "escalation_examples_in_memory_only",
                "simulated_escalation_examples",
                "input_summary",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_TYPE,
            "acceptance_threshold_escalation_report_policy",
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE, "hermes_inventory")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_MODE, "offline_escalation_policy_only")
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INTENDED_MODEL, "qwen3.6-plus")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
            (
                "explanatory_only_acceptance",
                "human_review_required",
                "deterministic_recheck_required",
                "unsafe_rejection",
                "missing_evidence_block",
                "policy_violation_block",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
            (
                "decision_state",
                "human_review_required",
                "deterministic_recheck_required",
                "blocked",
                "blocked_reason",
                "evidence_status",
                "confidence_status",
                "blocked_actions_summary",
                "allowed_human_message",
                "forbidden_message_content",
                "source_of_truth_policy",
                "redaction_policy",
                "report_writing_enabled",
                "runtime_enabled",
                "network_calls_allowed",
                "live_response_parsing_enabled",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS,
            EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
        )

    def test_dashscope_offline_escalation_policy_is_explicit_and_uses_in_memory_examples_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-escalation-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            consumer_decision = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            first = verify_dashscope_offline_escalation_contract(
                build_hermes_qwen_offline_escalation_policy(consumer_decision)
            )
            second = verify_dashscope_offline_escalation_contract(
                build_hermes_qwen_offline_escalation_policy(consumer_decision)
            )
            self.assertEqual(first["source"], EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE)
            self.assertEqual(first["mode"], EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_MODE)
            self.assertEqual(first["escalation_type"], EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_TYPE)
            self.assertFalse(first["report_writing_enabled"])
            self.assertTrue(first["response_explanatory_only"])
            self.assertFalse(first["live_response_parsing_enabled"])
            self.assertFalse(first["runtime_enabled"])
            self.assertFalse(first["network_calls_allowed"])
            self.assertTrue(first["escalation_examples_in_memory_only"])
            self.assertEqual(first["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INTENDED_MODEL)
            self.assertEqual(first["selected_model"], EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INTENDED_MODEL)
            self.assertEqual(
                tuple(first["allowed_acceptance_threshold_categories"]),
                EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
            )
            self.assertEqual(
                tuple(first["allowed_escalation_fields"]),
                EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
            )
            self.assertEqual(
                tuple(first["required_escalation_fields"]),
                EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS,
            )
            self.assertEqual(
                tuple(example["example_name"] for example in first["simulated_escalation_examples"]),
                EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_NAMES,
            )
            self.assertEqual(first["simulated_escalation_examples"], second["simulated_escalation_examples"])
            safe_dump = json.dumps(first, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)
            self.assertIn("explanatory only", first["source_of_truth_policy"])

    def test_dashscope_offline_escalation_policy_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            consumer_decision = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            payload = verify_dashscope_offline_escalation_contract(
                build_hermes_qwen_offline_escalation_policy(consumer_decision)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_escalation_policy_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            consumer_decision = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            payload = verify_dashscope_offline_escalation_contract(
                build_hermes_qwen_offline_escalation_policy(consumer_decision)
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])

    def test_dashscope_offline_escalation_policy_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            consumer_decision = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            payload = verify_dashscope_offline_escalation_contract(
                build_hermes_qwen_offline_escalation_policy(consumer_decision)
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertFalse(payload["live_response_parsing_enabled"])
            self.assertFalse(payload["network_calls_allowed"])
            self.assertFalse(payload["report_writing_enabled"])

    def test_dashscope_offline_escalation_policy_classifies_thresholds_and_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            consumer_decision = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            payload = verify_dashscope_offline_escalation_contract(
                build_hermes_qwen_offline_escalation_policy(consumer_decision)
            )
            examples = {
                example["example_name"]: example
                for example in payload["simulated_escalation_examples"]
            }
            self.assertEqual(
                examples["valid_grounded_explanatory_response"]["acceptance_threshold_category"],
                "explanatory_only_acceptance",
            )
            self.assertTrue(examples["valid_grounded_explanatory_response"]["accepted_explanatory_only"])
            self.assertFalse(examples["valid_grounded_explanatory_response"]["escalation_fields"]["blocked"])
            self.assertFalse(examples["valid_grounded_explanatory_response"]["escalation_fields"]["human_review_required"])
            self.assertFalse(
                examples["valid_grounded_explanatory_response"]["escalation_fields"]["deterministic_recheck_required"]
            )
            self.assertIn(
                "Accept only as explanatory output.",
                examples["valid_grounded_explanatory_response"]["escalation_fields"]["allowed_human_message"],
            )
            self.assertEqual(
                examples["missing_evidence_for_recommendation"]["acceptance_threshold_category"],
                "missing_evidence_block",
            )
            self.assertTrue(examples["missing_evidence_for_recommendation"]["escalation_fields"]["blocked"])
            self.assertTrue(
                examples["missing_evidence_for_recommendation"]["escalation_fields"]["deterministic_recheck_required"]
            )
            self.assertEqual(
                examples["unknown_evidence_reference"]["acceptance_threshold_category"],
                "deterministic_recheck_required",
            )
            self.assertFalse(examples["unknown_evidence_reference"]["escalation_fields"]["blocked"])
            self.assertTrue(examples["unknown_evidence_reference"]["escalation_fields"]["deterministic_recheck_required"])
            self.assertEqual(
                examples["source_of_truth_override_claim"]["acceptance_threshold_category"],
                "unsafe_rejection",
            )
            self.assertTrue(examples["source_of_truth_override_claim"]["escalation_fields"]["blocked"])
            self.assertTrue(examples["source_of_truth_override_claim"]["escalation_fields"]["human_review_required"])
            self.assertEqual(
                examples["source_of_truth_override_claim"]["escalation_fields"]["blocked_reason"],
                "source-of-truth-override",
            )
            self.assertEqual(
                examples["migration_write_authorization"]["escalation_fields"]["blocked_reason"],
                "migration-write-authorization",
            )
            self.assertEqual(
                examples["ready_to_migrate_without_gates"]["acceptance_threshold_category"],
                "unsafe_rejection",
            )
            self.assertEqual(
                examples["hidden_reasoning_output"]["acceptance_threshold_category"],
                "unsafe_rejection",
            )
            self.assertEqual(
                examples["secret_like_content"]["acceptance_threshold_category"],
                "unsafe_rejection",
            )
            self.assertEqual(
                examples["target_repo_file_contents"]["acceptance_threshold_category"],
                "unsafe_rejection",
            )
            self.assertEqual(
                examples["low_confidence_requires_human_review"]["acceptance_threshold_category"],
                "human_review_required",
            )
            self.assertTrue(
                examples["low_confidence_requires_human_review"]["escalation_fields"]["human_review_required"]
            )
            self.assertEqual(
                examples["missing_confidence_requires_recheck"]["acceptance_threshold_category"],
                "deterministic_recheck_required",
            )
            self.assertTrue(
                examples["missing_confidence_requires_recheck"]["escalation_fields"]["deterministic_recheck_required"]
            )
            self.assertEqual(
                examples["confidence_cannot_override_missing_evidence"]["acceptance_threshold_category"],
                "missing_evidence_block",
            )
            self.assertEqual(
                examples["deterministic_mismatch_requires_human_review"]["acceptance_threshold_category"],
                "human_review_required",
            )
            self.assertEqual(
                examples["unsafe_extra_field"]["acceptance_threshold_category"],
                "policy_violation_block",
            )
            self.assertTrue(examples["unsafe_extra_field"]["escalation_fields"]["blocked"])
            self.assertTrue(examples["unsafe_extra_field"]["escalation_fields"]["human_review_required"])
            self.assertIn(
                "Do not authorize target-repo writes",
                examples["migration_write_authorization"]["escalation_fields"]["blocked_actions_summary"],
            )
            self.assertFalse(
                examples["migration_write_authorization"]["escalation_fields"]["report_writing_enabled"]
            )

    def test_dashscope_offline_escalation_policy_rejects_unsafe_and_drifted_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            request_shape = verify_dashscope_offline_request_contract(
                build_hermes_qwen_offline_request_shape(
                    build_valid_hermes_inventory_payload(),
                    readiness,
                )
            )
            prompt_template = verify_dashscope_offline_prompt_contract(
                build_hermes_qwen_offline_prompt_template(request_shape)
            )
            prompt_preview = verify_dashscope_offline_prompt_preview_contract(
                build_hermes_qwen_offline_prompt_preview(request_shape, prompt_template)
            )
            response_shape = verify_dashscope_offline_response_contract(
                build_hermes_qwen_offline_response_shape(prompt_preview)
            )
            response_consumer = verify_dashscope_offline_response_consumer_contract(
                build_hermes_qwen_offline_response_consumer_policy(response_shape)
            )
            consumer_decision = verify_dashscope_offline_consumer_decision_contract(
                build_hermes_qwen_offline_consumer_decision_policy(response_consumer)
            )
            valid_examples = sanitize_dashscope_escalation_examples(
                consumer_decision["simulated_decision_examples"]
            )
            self.assertEqual(
                tuple(example["example_name"] for example in valid_examples),
                EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_NAMES,
            )

            wrong_category = json.loads(json.dumps(valid_examples[0]))
            wrong_category["acceptance_threshold_category"] = "human_review_required"
            with self.assertRaisesRegex(ValueError, "acceptance_threshold_category"):
                build_hermes_qwen_offline_escalation_policy(
                    consumer_decision,
                    candidate_examples=[wrong_category],
                )

            wrong_acceptance = json.loads(json.dumps(valid_examples[1]))
            wrong_acceptance["accepted_explanatory_only"] = True
            with self.assertRaisesRegex(ValueError, "accepted_explanatory_only"):
                build_hermes_qwen_offline_escalation_policy(
                    consumer_decision,
                    candidate_examples=[wrong_acceptance],
                )

            wrong_state = json.loads(json.dumps(valid_examples[7]))
            wrong_state["decision_state"] = "accept_explanatory_only"
            with self.assertRaisesRegex(ValueError, "expected decision_state"):
                build_hermes_qwen_offline_escalation_policy(
                    consumer_decision,
                    candidate_examples=[wrong_state],
                )

            drifted_fields = json.loads(json.dumps(valid_examples[4]))
            drifted_fields["escalation_fields"]["blocked"] = False
            with self.assertRaisesRegex(ValueError, "drifted from the governed escalation-field rules"):
                build_hermes_qwen_offline_escalation_policy(
                    consumer_decision,
                    candidate_examples=[drifted_fields],
                )

            extra_field = json.loads(json.dumps(valid_examples[13]))
            extra_field["escalation_fields"]["escalation_notes"] = "not allowed"
            with self.assertRaisesRegex(ValueError, "escalation_fields keys drifted"):
                build_hermes_qwen_offline_escalation_policy(
                    consumer_decision,
                    candidate_examples=[extra_field],
                )

    def test_dashscope_offline_response_parser_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_RESPONSE_PARSER_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_FIELDS,
            (
                "parser_policy_version",
                "parser_type",
                "source",
                "mode",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "local_config_ready",
                "input_kind",
                "runtime_enabled",
                "network_calls_allowed",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "report_writing_enabled",
                "response_explanatory_only",
                "live_response_parsing_enabled",
                "response_shape_version",
                "response_consumer_policy_version",
                "consumer_decision_policy_version",
                "escalation_policy_version",
                "parsed_response",
                "validation_result",
                "evidence_validation_result",
                "consumer_decision",
                "escalation_summary",
                "errors",
                "warnings",
                "source_of_truth_policy",
                "redaction_policy",
                "input_summary",
            ),
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE,
            "offline_response_parser_validation_dry_run",
        )
        self.assertEqual(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE, "hermes_inventory")
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE,
            "offline_response_parser_validation_only",
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND,
            "simulated_response_only",
        )
        self.assertEqual(
            EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INTENDED_MODEL,
            "qwen3.6-plus",
        )

    def test_dashscope_offline_response_parser_is_explicit_and_uses_simulated_inputs_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            sentinel = "dashscope-response-parser-sentinel"
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={sentinel}\n")
            response_shape, response_consumer, consumer_decision, escalation = build_dashscope_governed_policy_chain(repo)
            simulated_response = build_valid_simulated_response(response_shape)
            first = verify_dashscope_offline_response_parser_contract(
                parse_hermes_qwen_offline_simulated_response(
                    simulated_response,
                    response_shape,
                    response_consumer,
                    consumer_decision,
                    escalation,
                )
            )
            second = verify_dashscope_offline_response_parser_contract(
                parse_hermes_qwen_offline_simulated_response(
                    simulated_response,
                    response_shape,
                    response_consumer,
                    consumer_decision,
                    escalation,
                )
            )
            self.assertEqual(first["source"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE)
            self.assertEqual(first["mode"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE)
            self.assertEqual(first["parser_type"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE)
            self.assertEqual(first["input_kind"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND)
            self.assertEqual(first["intended_model"], EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INTENDED_MODEL)
            self.assertEqual(first["validation_result"], "accepted-explanatory-only")
            self.assertEqual(first["evidence_validation_result"]["status"], "grounded")
            self.assertEqual(first["consumer_decision"]["decision_state"], "accept_explanatory_only")
            self.assertTrue(first["escalation_summary"]["accepted_explanatory_only"])
            self.assertFalse(first["report_writing_enabled"])
            self.assertFalse(first["runtime_enabled"])
            self.assertFalse(first["network_calls_allowed"])
            self.assertFalse(first["live_response_parsing_enabled"])
            self.assertEqual(first["errors"], [])
            self.assertEqual(first["warnings"], [])
            self.assertEqual(first, second)
            self.assertFalse((repo / ".specify/state/drift.md").exists())
            safe_dump = json.dumps(first, sort_keys=True)
            self.assertNotIn(sentinel, safe_dump)
            self.assertNotIn("/tmp/hermes-root", safe_dump)
            self.assertNotIn("/tmp/hermes-root/alpha-v2", safe_dump)
            self.assertNotIn("print('hi')", safe_dump)
            self.assertIn(DASHSCOPE_INTENDED_MODEL, safe_dump)

    def test_dashscope_offline_response_parser_accepts_optional_qwen_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen3.6-plus\n",
            )
            response_shape, response_consumer, consumer_decision, escalation = build_dashscope_governed_policy_chain(repo)
            payload = verify_dashscope_offline_response_parser_contract(
                parse_hermes_qwen_offline_simulated_response(
                    build_valid_simulated_response(response_shape),
                    response_shape,
                    response_consumer,
                    consumer_decision,
                    escalation,
                )
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "explicit-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])
            self.assertEqual(payload["validation_result"], "accepted-explanatory-only")

    def test_dashscope_offline_response_parser_accepts_fallback_model_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "DASHSCOPE_MODEL=qwen3.6-plus\n",
            )
            response_shape, response_consumer, consumer_decision, escalation = build_dashscope_governed_policy_chain(repo)
            payload = verify_dashscope_offline_response_parser_contract(
                parse_hermes_qwen_offline_simulated_response(
                    build_valid_simulated_response(response_shape),
                    response_shape,
                    response_consumer,
                    consumer_decision,
                    escalation,
                )
            )
            self.assertEqual(payload["selected_model"], DASHSCOPE_INTENDED_MODEL)
            self.assertEqual(payload["model_policy_status"], "fallback-match")
            self.assertTrue(payload["model_policy_ready"])
            self.assertFalse(payload["model_policy_requires_update"])
            self.assertEqual(payload["validation_result"], "accepted-explanatory-only")

    def test_dashscope_offline_response_parser_surfaces_model_mismatch_without_enabling_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(
                repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n"
                "QWEN_MODEL=qwen-surprise\n",
            )
            response_shape, response_consumer, consumer_decision, escalation = build_dashscope_governed_policy_chain(repo)
            payload = verify_dashscope_offline_response_parser_contract(
                parse_hermes_qwen_offline_simulated_response(
                    build_valid_simulated_response(response_shape),
                    response_shape,
                    response_consumer,
                    consumer_decision,
                    escalation,
                )
            )
            self.assertEqual(payload["selected_model"], "qwen-surprise")
            self.assertEqual(payload["model_policy_status"], "mismatch")
            self.assertFalse(payload["model_policy_ready"])
            self.assertTrue(payload["model_policy_requires_update"])
            self.assertEqual(payload["validation_result"], "human-review-required")
            self.assertEqual(payload["consumer_decision"]["decision_state"], "escalate_human_review")
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["network_calls_allowed"])
            self.assertFalse(payload["report_writing_enabled"])

    def test_dashscope_offline_response_parser_validates_simulated_responses_across_governed_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            response_shape, response_consumer, consumer_decision, escalation = build_dashscope_governed_policy_chain(repo)

            missing_evidence = build_valid_simulated_response(response_shape)
            missing_evidence["evidence_references"].pop("recommended_next_step")
            missing_payload = parse_hermes_qwen_offline_simulated_response(
                missing_evidence,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(missing_payload["validation_result"], "blocked-missing-evidence")
            self.assertEqual(missing_payload["consumer_decision"]["decision_state"], "blocked_by_missing_evidence")
            self.assertTrue(missing_payload["escalation_summary"]["escalation_fields"]["blocked"])
            self.assertTrue(
                missing_payload["escalation_summary"]["escalation_fields"]["deterministic_recheck_required"]
            )

            unknown_evidence = build_valid_simulated_response(response_shape)
            unknown_evidence["evidence_references"]["risk_summary"] = ["repo_text_body"]
            unknown_payload = parse_hermes_qwen_offline_simulated_response(
                unknown_evidence,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(unknown_payload["evidence_validation_result"]["status"], "unknown-evidence")
            self.assertEqual(unknown_payload["validation_result"], "deterministic-recheck-required")
            self.assertEqual(unknown_payload["consumer_decision"]["decision_state"], "requires_deterministic_recheck")

            low_confidence = build_valid_simulated_response(response_shape)
            low_confidence["response_payload"]["confidence"] = "low"
            low_confidence_payload = parse_hermes_qwen_offline_simulated_response(
                low_confidence,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(low_confidence_payload["validation_result"], "human-review-required")
            self.assertEqual(low_confidence_payload["consumer_decision"]["decision_state"], "escalate_human_review")
            self.assertTrue(low_confidence_payload["consumer_decision"]["requires_human_review"])

            missing_confidence = build_valid_simulated_response(response_shape)
            missing_confidence["response_payload"]["confidence"] = "missing"
            missing_confidence_payload = parse_hermes_qwen_offline_simulated_response(
                missing_confidence,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(missing_confidence_payload["validation_result"], "deterministic-recheck-required")
            self.assertEqual(
                missing_confidence_payload["consumer_decision"]["decision_state"],
                "requires_deterministic_recheck",
            )

            confidence_cannot_override = build_valid_simulated_response(response_shape)
            confidence_cannot_override["response_payload"]["confidence"] = "high"
            confidence_cannot_override["evidence_references"].pop("risk_summary")
            confidence_override_payload = parse_hermes_qwen_offline_simulated_response(
                confidence_cannot_override,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(confidence_override_payload["validation_result"], "blocked-missing-evidence")
            self.assertEqual(confidence_override_payload["consumer_decision"]["decision_state"], "blocked_by_missing_evidence")

            deterministic_mismatch = build_valid_simulated_response(response_shape)
            deterministic_mismatch["deterministic_mismatch_flag"] = True
            deterministic_mismatch_payload = parse_hermes_qwen_offline_simulated_response(
                deterministic_mismatch,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(deterministic_mismatch_payload["evidence_validation_result"]["status"], "deterministic-mismatch")
            self.assertEqual(deterministic_mismatch_payload["validation_result"], "human-review-required")
            self.assertEqual(
                deterministic_mismatch_payload["consumer_decision"]["decision_state"],
                "escalate_human_review",
            )

    def test_dashscope_offline_response_parser_rejects_invalid_and_unsafe_simulated_responses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            response_shape, response_consumer, consumer_decision, escalation = build_dashscope_governed_policy_chain(repo)

            missing_field = build_valid_simulated_response(response_shape)
            missing_field["response_payload"].pop("analysis_summary")
            missing_field_payload = parse_hermes_qwen_offline_simulated_response(
                missing_field,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(missing_field_payload["validation_result"], "rejected-invalid-simulated-response")
            self.assertEqual(missing_field_payload["consumer_decision"]["decision_state"], "blocked_by_policy_violation")
            self.assertIn("missing required response fields", "\n".join(missing_field_payload["errors"]))

            wrong_type = build_valid_simulated_response(response_shape)
            wrong_type["response_payload"]["blocked_actions"] = "write now"
            wrong_type_payload = parse_hermes_qwen_offline_simulated_response(
                wrong_type,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(wrong_type_payload["validation_result"], "rejected-invalid-simulated-response")
            self.assertIn("blocked_actions", "\n".join(wrong_type_payload["errors"]))

            unknown_field = build_valid_simulated_response(response_shape)
            unknown_field["response_payload"]["response_notes"] = "not allowed"
            unknown_field_payload = parse_hermes_qwen_offline_simulated_response(
                unknown_field,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(unknown_field_payload["validation_result"], "rejected-invalid-simulated-response")
            self.assertIn("unsupported response fields", "\n".join(unknown_field_payload["errors"]))

            source_override = build_valid_simulated_response(response_shape)
            source_override["forbidden_content_flags"] = ["source_of_truth_override"]
            source_override_payload = parse_hermes_qwen_offline_simulated_response(
                source_override,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(source_override_payload["validation_result"], "rejected-unsafe")
            self.assertEqual(source_override_payload["consumer_decision"]["decision_state"], "reject_unsafe")

            migration_write = build_valid_simulated_response(response_shape)
            migration_write["forbidden_content_flags"] = ["migration_write_instructions"]
            migration_write_payload = parse_hermes_qwen_offline_simulated_response(
                migration_write,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(migration_write_payload["validation_result"], "rejected-unsafe")
            self.assertEqual(
                migration_write_payload["escalation_summary"]["escalation_fields"]["blocked_reason"],
                "migration-write-authorization",
            )

            ready_to_migrate = build_valid_simulated_response(response_shape)
            ready_to_migrate["forbidden_content_flags"] = ["ready_to_migrate_without_deterministic_gates"]
            ready_to_migrate_payload = parse_hermes_qwen_offline_simulated_response(
                ready_to_migrate,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(ready_to_migrate_payload["validation_result"], "rejected-unsafe")

            hidden_reasoning = build_valid_simulated_response(response_shape)
            hidden_reasoning["forbidden_content_flags"] = ["hidden_reasoning"]
            hidden_reasoning_payload = parse_hermes_qwen_offline_simulated_response(
                hidden_reasoning,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(hidden_reasoning_payload["validation_result"], "rejected-unsafe")

            secret_like = build_valid_simulated_response(response_shape)
            secret_like["forbidden_content_flags"] = ["api_key_material"]
            secret_like_payload = parse_hermes_qwen_offline_simulated_response(
                secret_like,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(secret_like_payload["validation_result"], "rejected-unsafe")

            target_repo_contents = build_valid_simulated_response(response_shape)
            target_repo_contents["forbidden_content_flags"] = ["target_repo_file_contents"]
            target_repo_payload = parse_hermes_qwen_offline_simulated_response(
                target_repo_contents,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(target_repo_payload["validation_result"], "rejected-unsafe")

            unsafe_extra = build_valid_simulated_response(response_shape)
            unsafe_extra["forbidden_content_flags"] = ["unsafe_extra_field"]
            unsafe_extra_payload = parse_hermes_qwen_offline_simulated_response(
                unsafe_extra,
                response_shape,
                response_consumer,
                consumer_decision,
                escalation,
            ).to_safe_dict()
            self.assertEqual(unsafe_extra_payload["validation_result"], "blocked-policy-violation")
            self.assertEqual(unsafe_extra_payload["consumer_decision"]["decision_state"], "blocked_by_policy_violation")
            self.assertTrue(unsafe_extra_payload["escalation_summary"]["escalation_fields"]["human_review_required"])

    def test_dashscope_connectivity_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_CONNECTIVITY_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_CONNECTIVITY_FIELDS,
            (
                "connectivity_policy_version",
                "probe_type",
                "source",
                "mode",
                "probe_requested",
                "network_attempted",
                "local_config_ready",
                "selected_api_key_name",
                "selected_api_key_category",
                "intended_model",
                "selected_model",
                "model_policy_status",
                "model_policy_ready",
                "model_policy_requires_update",
                "probe_endpoint_label",
                "request_method",
                "request_body_kind",
                "request_body_bytes_length",
                "project_content_sent",
                "inventory_content_sent",
                "prompt_preview_content_sent",
                "target_repo_content_sent",
                "connectivity_status",
                "sanitized_error_category",
                "http_status_category",
                "qwen_analysis_enabled",
                "runtime_enabled",
                "report_writing_enabled",
                "health_surface_integration_enabled",
                "authorization_header_logged",
                "raw_request_headers_logged",
                "raw_response_body_logged",
                "redaction_policy",
            ),
        )
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_TYPE, "dashscope_connectivity_probe")
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_SOURCE, "dashscope_local_readiness")
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_MODE, "explicit_opt_in_no_content_probe")
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_INTENDED_MODEL, "qwen3.6-plus")
        self.assertIn("reachable", EXPECTED_DASHSCOPE_CONNECTIVITY_STATUSES)

    def test_dashscope_connectivity_json_contract_baseline_exists(self) -> None:
        self.assertTrue(DASHSCOPE_CONNECTIVITY_JSON_CONTRACT.exists())
        self.assertEqual(
            EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_FIELDS,
            (
                "schema_version",
                "command",
                "mode",
                "intended_model",
                "selected_model",
                "selected_api_key_name",
                "selected_api_key_category",
                "local_config_ready",
                "model_policy_status",
                "probe_requested",
                "no_content",
                "yes_network",
                "interactive_required",
                "interactive_session",
                "operator_gate_satisfied",
                "network_attempted",
                "connectivity_status",
                "sanitized_error_category",
                "http_status_category",
                "request_method",
                "request_body_kind",
                "request_body_bytes_length",
                "project_content_sent",
                "inventory_content_sent",
                "prompt_preview_content_sent",
                "target_repo_content_sent",
                "qwen_analysis_enabled",
                "report_writing_enabled",
                "migration_writes_enabled",
                "graphify_enabled",
                "health_surface_integration_enabled",
                "warnings",
                "errors",
            ),
        )
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION, "1.0.0")
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_COMMAND, "hermes_qwen_connectivity")
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODE, "explicit_opt_in_no_content_probe")
        self.assertEqual(EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_INTENDED_MODEL, "qwen3.6-plus")
        self.assertIn("reachable", EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_STATUSES)
        self.assertIn("none", EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_ERROR_CATEGORIES)
        self.assertIn("2xx", EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_HTTP_STATUS_CATEGORIES)

    def test_dashscope_connectivity_probe_requires_explicit_opt_in_and_attempts_no_network_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            calls: list[dict[str, object]] = []

            def transport(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                calls.append(
                    {
                        "request": request.to_safe_dict(),
                        "env_path": str(env_path),
                        "selected_api_key_name": selected_api_key_name,
                    }
                )
                return DashScopeConnectivityTransportResult(http_status=200)

            payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(readiness, transport=transport)
            )
            self.assertEqual(calls, [])
            self.assertEqual(payload["connectivity_status"], "not-requested")
            self.assertEqual(payload["sanitized_error_category"], "none")
            self.assertEqual(payload["http_status_category"], "not-attempted")
            self.assertFalse(payload["network_attempted"])
            self.assertFalse(payload["project_content_sent"])
            self.assertFalse(payload["inventory_content_sent"])
            self.assertFalse(payload["prompt_preview_content_sent"])
            self.assertFalse(payload["target_repo_content_sent"])
            self.assertFalse(payload["qwen_analysis_enabled"])
            self.assertFalse(payload["runtime_enabled"])
            self.assertFalse(payload["report_writing_enabled"])
            self.assertFalse(payload["health_surface_integration_enabled"])

    def test_dashscope_connectivity_probe_explicit_opt_in_uses_only_no_content_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))
            calls: list[dict[str, object]] = []

            def transport(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> dict[str, object]:
                calls.append(
                    {
                        "request": request.to_safe_dict(),
                        "env_path": str(env_path),
                        "selected_api_key_name": selected_api_key_name,
                    }
                )
                return {"http_status": 204, "error_category": "none"}

            payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(
                    readiness,
                    probe_requested=True,
                    transport=transport,
                )
            )
            self.assertEqual(len(calls), 1)
            request = calls[0]["request"]
            self.assertEqual(calls[0]["env_path"], str(repo / ".env"))
            self.assertEqual(calls[0]["selected_api_key_name"], "DASHSCOPE_API_KEY_WORKFLOW_MANAGER")
            self.assertEqual(request["request_method"], "GET")
            self.assertEqual(request["request_body_kind"], "none")
            self.assertEqual(request["request_body_bytes_length"], 0)
            self.assertEqual(request["url"], DASHSCOPE_CONNECTIVITY_PROBE_URL)
            self.assertFalse(request["project_content_sent"])
            self.assertFalse(request["inventory_content_sent"])
            self.assertFalse(request["prompt_preview_content_sent"])
            self.assertFalse(request["target_repo_content_sent"])
            self.assertFalse(request["qwen_analysis_enabled"])
            self.assertTrue(payload["probe_requested"])
            self.assertTrue(payload["network_attempted"])
            self.assertEqual(payload["connectivity_status"], "reachable")
            self.assertEqual(payload["sanitized_error_category"], "none")
            self.assertEqual(payload["http_status_category"], "2xx")

    def test_dashscope_connectivity_probe_handles_missing_key_and_model_mismatch_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_repo = Path(temp_dir) / "missing"
            missing_repo.mkdir(parents=True, exist_ok=True)
            missing_readiness = verify_dashscope_local_readiness_contract(
                inspect_dashscope_local_readiness(missing_repo)
            )
            missing_calls: list[str] = []

            def should_not_run(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                missing_calls.append("called")
                return DashScopeConnectivityTransportResult(http_status=200)

            missing_payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(
                    missing_readiness,
                    probe_requested=True,
                    transport=should_not_run,
                )
            )
            self.assertEqual(missing_calls, [])
            self.assertEqual(missing_payload["connectivity_status"], "not-configured")
            self.assertEqual(missing_payload["sanitized_error_category"], "missing-api-key")
            self.assertFalse(missing_payload["network_attempted"])

            mismatch_repo = Path(temp_dir) / "mismatch"
            mismatch_repo.mkdir(parents=True, exist_ok=True)
            write(
                mismatch_repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\nQWEN_MODEL=qwen3.6-turbo\n",
            )
            mismatch_readiness = verify_dashscope_local_readiness_contract(
                inspect_dashscope_local_readiness(mismatch_repo)
            )
            mismatch_calls: list[str] = []

            def should_not_run_mismatch(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                mismatch_calls.append("called")
                return DashScopeConnectivityTransportResult(http_status=200)

            mismatch_payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(
                    mismatch_readiness,
                    probe_requested=True,
                    transport=should_not_run_mismatch,
                )
            )
            self.assertEqual(mismatch_calls, [])
            self.assertEqual(mismatch_payload["selected_model"], "qwen3.6-turbo")
            self.assertEqual(mismatch_payload["model_policy_status"], "mismatch")
            self.assertEqual(mismatch_payload["connectivity_status"], "model-policy-mismatch")
            self.assertEqual(mismatch_payload["sanitized_error_category"], "model-policy-mismatch")
            self.assertFalse(mismatch_payload["network_attempted"])

    def test_dashscope_connectivity_probe_uses_sanitized_error_categories_and_redacts_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            secret_value = "dashscope-connectivity-sentinel-secret"
            repo = Path(temp_dir)
            write(repo / ".env", f"DASHSCOPE_API_KEY_WORKFLOW_MANAGER={secret_value}\n")
            readiness = verify_dashscope_local_readiness_contract(inspect_dashscope_local_readiness(repo))

            auth_payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(
                    readiness,
                    probe_requested=True,
                    transport=lambda request, env_path, selected_api_key_name: {
                        "http_status": 401,
                        "error_category": "http-401",
                    },
                )
            )
            self.assertEqual(auth_payload["connectivity_status"], "auth-error")
            self.assertEqual(auth_payload["http_status_category"], "401")

            server_payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(
                    readiness,
                    probe_requested=True,
                    transport=lambda request, env_path, selected_api_key_name: {
                        "http_status": 503,
                        "error_category": "http-5xx",
                    },
                )
            )
            self.assertEqual(server_payload["connectivity_status"], "service-error")
            self.assertEqual(server_payload["http_status_category"], "5xx")

            timeout_payload = verify_dashscope_connectivity_contract(
                probe_dashscope_connectivity(
                    readiness,
                    probe_requested=True,
                    transport=lambda request, env_path, selected_api_key_name: (_ for _ in ()).throw(
                        TimeoutError("timed out")
                    ),
                )
            )
            self.assertEqual(timeout_payload["connectivity_status"], "network-error")
            self.assertEqual(timeout_payload["sanitized_error_category"], "timeout")
            serialized = json.dumps(timeout_payload, sort_keys=True)
            self.assertNotIn(secret_value, serialized)
            self.assertNotIn("Authorization: Bearer", serialized)
            self.assertFalse(timeout_payload["authorization_header_logged"])
            self.assertFalse(timeout_payload["raw_request_headers_logged"])
            self.assertFalse(timeout_payload["raw_response_body_logged"])

    def test_workflow_hermes_qwen_connectivity_help_is_explicit_and_human_only(self) -> None:
        result = self.run_cli(ROOT, "hermes", "qwen-connectivity", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: workflow hermes qwen-connectivity", result.stdout)
        self.assertIn("--probe", result.stdout)
        self.assertIn("--no-content", result.stdout)
        self.assertIn("--yes-network", result.stdout)
        self.assertIn("--json", result.stdout)
        self.assertIn("Human-readable", result.stdout)
        self.assertNotIn("Authorization:", result.stdout)
        self.assertNotIn("Bearer ", result.stdout)

    def test_workflow_hermes_qwen_connectivity_default_and_incomplete_flags_stay_local_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            calls: list[dict[str, object]] = []

            def transport(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                calls.append(
                    {
                        "request": request.to_safe_dict(),
                        "env_path": str(env_path),
                        "selected_api_key_name": selected_api_key_name,
                    }
                )
                return DashScopeConnectivityTransportResult(http_status=200)

            cases = (
                (False, False, False),
                (True, False, False),
                (True, True, False),
            )
            for probe, no_content, yes_network in cases:
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    returncode = workflow_cli.hermes_qwen_connectivity_command(
                        repo=repo,
                        probe=probe,
                        no_content=no_content,
                        yes_network=yes_network,
                        transport=transport,
                        interactive_session=True,
                    )
                self.assertEqual(returncode, 1)
                self.assertEqual(calls, [])
                rendered = stdout.getvalue()
                self.assertIn("- operator gate satisfied: no", rendered)
                self.assertIn("- network attempted: no", rendered)
                self.assertIn("- qwen analysis enabled: no", rendered)
                self.assertNotIn("Authorization:", rendered)
                self.assertNotIn("Bearer ", rendered)

    def test_workflow_hermes_qwen_connectivity_full_opt_in_wraps_helper_once_with_mocked_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            calls: list[dict[str, object]] = []

            def transport(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                calls.append(
                    {
                        "request": request.to_safe_dict(),
                        "env_path": str(env_path),
                        "selected_api_key_name": selected_api_key_name,
                    }
                )
                return DashScopeConnectivityTransportResult(http_status=204)

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                returncode = workflow_cli.hermes_qwen_connectivity_command(
                    repo=repo,
                    probe=True,
                    no_content=True,
                    yes_network=True,
                    transport=transport,
                    interactive_session=True,
                )

            self.assertEqual(returncode, 0)
            self.assertEqual(len(calls), 1)
            request = calls[0]["request"]
            self.assertEqual(calls[0]["env_path"], str(repo / ".env"))
            self.assertEqual(calls[0]["selected_api_key_name"], "DASHSCOPE_API_KEY_WORKFLOW_MANAGER")
            self.assertEqual(request["request_method"], "GET")
            self.assertEqual(request["request_body_kind"], "none")
            self.assertEqual(request["request_body_bytes_length"], 0)
            self.assertEqual(request["url"], DASHSCOPE_CONNECTIVITY_PROBE_URL)
            self.assertFalse(request["project_content_sent"])
            self.assertFalse(request["inventory_content_sent"])
            self.assertFalse(request["prompt_preview_content_sent"])
            self.assertFalse(request["target_repo_content_sent"])
            rendered = stdout.getvalue()
            self.assertIn("- operator gate satisfied: yes", rendered)
            self.assertIn("- network attempted: yes", rendered)
            self.assertIn("- connectivity status: reachable", rendered)
            self.assertNotIn("Authorization:", rendered)
            self.assertNotIn("Bearer ", rendered)

    def test_workflow_hermes_qwen_connectivity_cli_subprocess_paths_stay_redacted_and_noninteractive(self) -> None:
        cases = (
            ("default", ("hermes", "qwen-connectivity"), "network stays disabled"),
            ("probe_only", ("hermes", "qwen-connectivity", "--probe"), "network stays disabled"),
            (
                "probe_no_content",
                ("hermes", "qwen-connectivity", "--probe", "--no-content"),
                "network stays disabled",
            ),
            (
                "full_opt_in_noninteractive",
                ("hermes", "qwen-connectivity", "--probe", "--no-content", "--yes-network"),
                "live probing is refused in non-interactive runs",
            ),
        )
        for _, args, expected_reason in cases:
            result = self.run_cli(ROOT, *args)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("workflow hermes qwen-connectivity :: mode=explicit-opt-in-no-content", result.stdout)
            self.assertIn("- network attempted: no", result.stdout)
            self.assertIn(expected_reason, result.stdout)
            self.assertIn("- qwen analysis enabled: no", result.stdout)
            self.assertIn("- migration writes enabled: no", result.stdout)
            self.assertNotIn("Authorization:", result.stdout)
            self.assertNotIn("Bearer ", result.stdout)
            self.assertEqual(result.stderr, "")

    def test_workflow_hermes_qwen_connectivity_json_full_opt_in_wraps_helper_once_with_mocked_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\n")
            calls: list[dict[str, object]] = []

            def transport(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                calls.append(
                    {
                        "request": request.to_safe_dict(),
                        "env_path": str(env_path),
                        "selected_api_key_name": selected_api_key_name,
                    }
                )
                return DashScopeConnectivityTransportResult(http_status=204)

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                returncode = workflow_cli.hermes_qwen_connectivity_command(
                    repo=repo,
                    probe=True,
                    no_content=True,
                    yes_network=True,
                    transport=transport,
                    interactive_session=True,
                    as_json=True,
                )

            self.assertEqual(returncode, 0)
            self.assertEqual(len(calls), 1)
            request = calls[0]["request"]
            self.assertEqual(calls[0]["env_path"], str(repo / ".env"))
            self.assertEqual(calls[0]["selected_api_key_name"], "DASHSCOPE_API_KEY_WORKFLOW_MANAGER")
            self.assertEqual(request["request_method"], "GET")
            self.assertEqual(request["request_body_kind"], "none")
            self.assertEqual(request["request_body_bytes_length"], 0)
            self.assertEqual(request["url"], DASHSCOPE_CONNECTIVITY_PROBE_URL)
            payload = verify_dashscope_connectivity_json_stdout(stdout.getvalue())
            self.assertTrue(payload["probe_requested"])
            self.assertTrue(payload["no_content"])
            self.assertTrue(payload["yes_network"])
            self.assertTrue(payload["interactive_session"])
            self.assertTrue(payload["operator_gate_satisfied"])
            self.assertTrue(payload["network_attempted"])
            self.assertEqual(payload["connectivity_status"], "reachable")
            self.assertEqual(payload["warnings"], [])
            self.assertEqual(payload["errors"], [])

    def test_workflow_hermes_qwen_connectivity_json_represents_missing_key_and_model_mismatch_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_repo = Path(temp_dir) / "missing"
            missing_repo.mkdir(parents=True, exist_ok=True)
            calls: list[str] = []

            def should_not_run(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                calls.append("called")
                return DashScopeConnectivityTransportResult(http_status=200)

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                returncode = workflow_cli.hermes_qwen_connectivity_command(
                    repo=missing_repo,
                    probe=True,
                    no_content=True,
                    yes_network=True,
                    transport=should_not_run,
                    interactive_session=True,
                    as_json=True,
                )
            self.assertEqual(returncode, 1)
            self.assertEqual(calls, [])
            missing_payload = verify_dashscope_connectivity_json_stdout(stdout.getvalue())
            self.assertTrue(missing_payload["operator_gate_satisfied"])
            self.assertFalse(missing_payload["network_attempted"])
            self.assertEqual(missing_payload["connectivity_status"], "not-configured")
            self.assertEqual(missing_payload["sanitized_error_category"], "missing-api-key")
            self.assertIn("missing an active API key", " ".join(missing_payload["warnings"]))
            self.assertEqual(missing_payload["errors"], [])

            mismatch_repo = Path(temp_dir) / "mismatch"
            mismatch_repo.mkdir(parents=True, exist_ok=True)
            write(
                mismatch_repo / ".env",
                "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=present\nQWEN_MODEL=qwen3.6-turbo\n",
            )
            mismatch_calls: list[str] = []

            def should_not_run_mismatch(
                request: DashScopeConnectivityProbeRequest,
                env_path: Path,
                selected_api_key_name: str,
            ) -> DashScopeConnectivityTransportResult:
                mismatch_calls.append("called")
                return DashScopeConnectivityTransportResult(http_status=200)

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                returncode = workflow_cli.hermes_qwen_connectivity_command(
                    repo=mismatch_repo,
                    probe=True,
                    no_content=True,
                    yes_network=True,
                    transport=should_not_run_mismatch,
                    interactive_session=True,
                    as_json=True,
                )
            self.assertEqual(returncode, 1)
            self.assertEqual(mismatch_calls, [])
            mismatch_payload = verify_dashscope_connectivity_json_stdout(stdout.getvalue())
            self.assertEqual(mismatch_payload["selected_model"], "qwen3.6-turbo")
            self.assertEqual(mismatch_payload["model_policy_status"], "mismatch")
            self.assertEqual(mismatch_payload["connectivity_status"], "model-policy-mismatch")
            self.assertEqual(mismatch_payload["sanitized_error_category"], "model-policy-mismatch")
            self.assertFalse(mismatch_payload["network_attempted"])
            self.assertIn("does not match the governed qwen3.6-plus connectivity policy", " ".join(mismatch_payload["warnings"]))
            self.assertEqual(mismatch_payload["errors"], [])

    def test_workflow_hermes_qwen_connectivity_json_paths_are_clean_parseable_and_noninteractive(self) -> None:
        cases = (
            (
                ("hermes", "qwen-connectivity", "--json"),
                False,
                False,
                False,
                "network stays disabled",
            ),
            (
                ("hermes", "qwen-connectivity", "--probe", "--json"),
                True,
                False,
                False,
                "network stays disabled",
            ),
            (
                ("hermes", "qwen-connectivity", "--probe", "--no-content", "--json"),
                True,
                True,
                False,
                "network stays disabled",
            ),
            (
                ("hermes", "qwen-connectivity", "--probe", "--no-content", "--yes-network", "--json"),
                True,
                True,
                True,
                "live probing is refused in non-interactive runs",
            ),
        )
        for args, probe, no_content, yes_network, expected_reason in cases:
            result = self.run_cli(ROOT, *args)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertNotIn("Authorization:", result.stdout)
            self.assertNotIn("Bearer ", result.stdout)
            payload = verify_dashscope_connectivity_json_stdout(result.stdout)
            self.assertEqual(payload["probe_requested"], probe)
            self.assertEqual(payload["no_content"], no_content)
            self.assertEqual(payload["yes_network"], yes_network)
            self.assertTrue(payload["interactive_required"])
            self.assertFalse(payload["interactive_session"])
            self.assertFalse(payload["operator_gate_satisfied"])
            self.assertFalse(payload["network_attempted"])
            self.assertEqual(payload["connectivity_status"], "not-requested")
            self.assertEqual(payload["sanitized_error_category"], "none")
            self.assertEqual(payload["errors"], [])
            self.assertIn(expected_reason, " ".join(payload["warnings"]))

    def test_connectivity_manual_live_probe_runbook_is_documented_and_safely_scoped(self) -> None:
        readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        handoff_text = (ROOT / ".specify/state/handoff.md").read_text(encoding="utf-8")
        progress_text = (ROOT / ".specify/state/progress.md").read_text(encoding="utf-8")
        migration_text = (ROOT / ".specify/state/migration.md").read_text(encoding="utf-8")
        combined = "\n".join((readme_text, agents_text, handoff_text, progress_text, migration_text))

        self.assertIn("workflow hermes qwen-connectivity --probe --no-content --yes-network", combined)
        self.assertIn("workflow hermes qwen-connectivity --probe --no-content --yes-network --json", combined)
        self.assertIn("manual live no-content connectivity probe", combined.lower())
        self.assertIn("interactive terminal only", combined)
        self.assertIn("Automated validation and automated tests must not run it as a live probe.", combined)
        self.assertIn("no project content", combined)
        self.assertIn("no Hermes inventory content", combined)
        self.assertIn("no prompt preview content", combined)
        self.assertIn("no target-repo content", combined)
        self.assertIn("does not run Qwen analysis", combined)
        self.assertIn("does not write reports", combined)
        self.assertIn("does not migrate repos", combined)
        self.assertIn("does not enable Graphify", combined)
        self.assertIn("Authorization headers", combined)
        self.assertIn("raw request headers", combined)
        self.assertIn("raw response bodies", combined)
        self.assertIn("`.env` values", combined)
        self.assertIn("connectivity_status", combined)
        self.assertIn("sanitized_error_category", combined)
        self.assertIn("http_status_category", combined)
        self.assertIn("Do not create a probe result file.", combined)
        self.assertIn("Do not write probe results to `.specify/state/`.", combined)
        self.assertIn("operator-run only", combined)

    def test_workflow_connectivity_remains_outside_status_doctor_and_hermes_inventory(self) -> None:
        original_probe = workflow_cli.probe_dashscope_connectivity
        cwd = Path.cwd()

        def fail_probe(*args: object, **kwargs: object) -> object:
            raise AssertionError("probe_dashscope_connectivity should not be called by status, doctor, or hermes inventory")

        try:
            workflow_cli.probe_dashscope_connectivity = fail_probe
            os.chdir(ROOT)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(workflow_cli.main(["status", "--json"]), 0)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(workflow_cli.main(["doctor", "--json"]), 0)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(workflow_cli.main(["hermes", "inventory", "--dry-run"]), 0)
        finally:
            workflow_cli.probe_dashscope_connectivity = original_probe
            os.chdir(cwd)

    def test_workflow_qwen_still_does_not_exist_and_hermes_analyze_is_dry_run_only(self) -> None:
        workflow_qwen = self.run_cli(ROOT, "qwen")
        self.assertNotEqual(workflow_qwen.returncode, 0)
        self.assertIn("invalid choice", workflow_qwen.stderr)

        hermes_analyze = self.run_cli(ROOT, "hermes", "analyze")
        self.assertNotEqual(hermes_analyze.returncode, 0)
        self.assertEqual(hermes_analyze.stdout, "")
        self.assertIn("dry-run only", hermes_analyze.stderr)

    def test_env_secret_hygiene_commands_and_generated_files_do_not_leak_sentinel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            secret_value = "dashscope-secret-sentinel-for-workflow-manager-tests"
            repo, env = self.create_secret_hygiene_repo(
                Path(temp_dir),
                secret_value=secret_value,
            )

            sync_result = self.run_cli(repo, "sync", env=env)
            self.assertEqual(sync_result.returncode, 0, sync_result.stderr)
            assert_secret_absent_from_text("workflow sync stdout", sync_result.stdout, secret_value)
            assert_secret_absent_from_text("workflow sync stderr", sync_result.stderr, secret_value)

            command_cases = (
                ("status", ("status",)),
                ("status_json", ("status", "--json")),
                ("doctor", ("doctor",)),
                ("doctor_json", ("doctor", "--json")),
                ("doctor_write_report", ("doctor", "--write-report")),
                ("doctor_write_report_json", ("doctor", "--write-report", "--json")),
                ("hermes_inventory", ("hermes", "inventory", "--dry-run")),
                ("hermes_inventory_json", ("hermes", "inventory", "--dry-run", "--json")),
            )
            results: dict[str, subprocess.CompletedProcess[str]] = {}
            for label, args in command_cases:
                result = self.run_cli(repo, *args, env=env)
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                assert_secret_absent_from_text(f"{label} stdout", result.stdout, secret_value)
                assert_secret_absent_from_text(f"{label} stderr", result.stderr, secret_value)
                results[label] = result

            verify_json_contract_stdout(results["status_json"].stdout, "status")
            verify_json_contract_stdout(results["doctor_json"].stdout, "doctor")
            verify_json_contract_stdout(
                results["doctor_write_report_json"].stdout,
                "doctor_write_report",
                expect_wrote_report=True,
                expected_drift_report_path=repo / ".specify/state/drift.md",
            )
            verify_hermes_inventory_json_stdout(
                results["hermes_inventory_json"].stdout,
                expected_roots_config_path=Path(env["WORKFLOW_ROOTS_FILE"]),
            )

            for relative in EXPECTED_SECRET_SAFE_GENERATED_FILES:
                assert_secret_absent_from_path(repo / relative, secret_value)

    def test_hermes_inventory_json_invariant_baseline_exists(self) -> None:
        self.assertTrue(HERMES_INVENTORY_JSON_INVARIANTS.exists())
        self.assertEqual(
            EXPECTED_HERMES_INVENTORY_JSON_KEYS,
            (
                "schema_version",
                "command",
                "mode",
                "dry_run",
                "roots_config_path",
                "summary",
                "classification_counts",
                "roots",
                "warnings",
                "errors",
                "target_repos_modified",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
            ),
        )
        self.assertEqual(
            EXPECTED_HERMES_INVENTORY_ROOT_KEYS,
            ("path", "classification", "exists", "is_directory", "project_count", "issues", "projects"),
        )
        self.assertEqual(
            EXPECTED_HERMES_INVENTORY_PROJECT_KEYS,
            ("name", "path", "root", "classification", "notes"),
        )
        self.assertEqual(
            ALLOWED_HERMES_PROJECT_CLASSIFICATIONS,
            {"v2", "legacy", "mixed", "unmanaged", "error"},
        )
        self.assertEqual(
            ALLOWED_HERMES_ROOT_CLASSIFICATIONS,
            {"configured-root", "missing-root", "invalid-root"},
        )

    def test_hermes_inventory_json_governance_is_invariant_only(self) -> None:
        self.assertFalse(UPDATE_HERMES_INVENTORY_JSON_FIXTURES.exists())
        payload = verify_hermes_inventory_json_payload(build_valid_hermes_inventory_payload())
        self.assertEqual(payload["command"], "hermes_inventory")
        self.assertTrue(payload["dry_run"])

    def test_hermes_inventory_json_invariant_failure_is_clear_for_missing_top_level_field(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload.pop("summary")
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory payload keys drifted", str(error.exception))
        self.assertIn("summary", str(error.exception))

    def test_hermes_inventory_json_invariant_failure_is_clear_for_wrong_top_level_field_type(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["classification_counts"] = []
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory payload.classification_counts", str(error.exception))
        self.assertIn("JSON object", str(error.exception))

    def test_hermes_inventory_json_invariant_failure_is_clear_for_missing_root_field(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["roots"][0].pop("issues")
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory root payload keys drifted", str(error.exception))
        self.assertIn("issues", str(error.exception))

    def test_hermes_inventory_json_invariant_failure_is_clear_for_invalid_root_classification(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["roots"][0]["classification"] = "unexpected-root"
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory root payload.classification", str(error.exception))
        self.assertIn("configured-root", str(error.exception))

    def test_hermes_inventory_json_invariant_failure_is_clear_for_missing_project_field(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["roots"][0]["projects"][0].pop("notes")
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory project payload keys drifted", str(error.exception))
        self.assertIn("notes", str(error.exception))

    def test_hermes_inventory_json_invariant_failure_is_clear_for_invalid_project_classification(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["roots"][0]["projects"][0]["classification"] = "unexpected-project"
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory project payload.classification", str(error.exception))
        self.assertIn("legacy", str(error.exception))

    def test_hermes_inventory_json_invariant_failure_is_clear_for_wrong_safety_flag(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["target_repos_modified"] = True
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory payload.target_repos_modified", str(error.exception))
        self.assertIn("false", str(error.exception))

    def test_hermes_inventory_json_schema_policy_is_explicit_and_separate(self) -> None:
        policy = verify_hermes_inventory_json_evolution_policy()
        self.assertEqual(policy["schema_surface"], "hermes_inventory")
        self.assertEqual(policy["schema_version"], EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION)
        self.assertEqual(policy["versioning_mode"], "surface-local")
        self.assertEqual(policy["versioning_scheme"], "semver")
        self.assertTrue(policy["separate_from_health_json_contract"])
        self.assertFalse(policy["command_specific_versioning"])
        self.assertFalse(policy["additive_keys_allowed"])
        self.assertTrue(policy["breaking_changes_require_version_bump"])
        self.assertTrue(policy["coordinated_updates_required"])
        self.assertTrue(policy["classification_vocabularies_governed"])
        self.assertTrue(policy["safety_flags_governed"])
        self.assertTrue(policy["dry_run_gating_governed"])
        self.assertTrue(policy["read_only_behavior_governed"])
        self.assertTrue(policy["deterministic_ordering_governed"])
        self.assertEqual(
            policy["breaking_change_categories"],
            HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES,
        )
        self.assertEqual(
            policy["additive_change_categories"],
            HERMES_INVENTORY_JSON_ADDITIVE_CHANGE_CATEGORIES,
        )

    def test_hermes_inventory_json_schema_policy_matches_live_schema_version(self) -> None:
        policy = verify_hermes_inventory_json_evolution_policy()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "inventory-root"
            root.mkdir()
            self.create_v2_repo(root, "alpha-v2")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])
            result = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = verify_hermes_inventory_json_stdout(
                result.stdout,
                expected_roots_config_path=config,
            )
            self.assertEqual(payload["schema_version"], policy["schema_version"])
            self.assertEqual(payload["command"], policy["schema_surface"])
            self.assertEqual(payload["mode"], "inventory")
            self.assertTrue(payload["dry_run"])

    def test_hermes_inventory_json_reserved_additive_policy_is_explicit_and_gated(self) -> None:
        policy = verify_hermes_inventory_json_reserved_additive_policy()
        self.assertEqual(policy["status"], "reserved-not-enabled")
        self.assertFalse(policy["enabled_by_default"])
        self.assertEqual(policy["current_schema_version"], EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION)
        self.assertEqual(
            policy["future_minor_version_path"],
            "reserved-hermes-inventory-minor-version-bump",
        )
        self.assertTrue(policy["minor_version_bump_required"])
        self.assertTrue(policy["new_fields_must_be_optional_for_consumers"])
        self.assertTrue(policy["new_fields_must_not_change_existing_field_meaning"])
        self.assertTrue(policy["new_fields_must_not_change_existing_field_types"])
        self.assertTrue(policy["new_fields_must_not_change_classification_vocabularies"])
        self.assertTrue(policy["new_fields_must_not_change_safety_flag_semantics"])
        self.assertTrue(policy["new_fields_must_not_change_dry_run_gating"])
        self.assertTrue(policy["new_fields_must_not_change_read_only_behavior"])
        self.assertTrue(policy["new_fields_must_not_change_deterministic_ordering"])
        self.assertIn("minor-version-upgrade", policy["consumer_unknown_field_rule_when_enabled"])

    def test_hermes_inventory_json_schema_policy_classifies_top_level_removal_as_breaking(self) -> None:
        assessment = assess_hermes_inventory_json_change("remove-governed-top-level-field")
        self.assertEqual(assessment["classification"], "breaking")
        self.assertEqual(assessment["required_version_change"], "major")
        self.assertTrue(assessment["requires_policy_update"])
        self.assertTrue(assessment["read_only_behavior_must_remain"])
        self.assertIn("explicitly governed as breaking", assessment["reason"])

    def test_hermes_inventory_json_schema_policy_classifies_type_drift_as_breaking(self) -> None:
        assessment = assess_hermes_inventory_json_change(
            "add-governed-top-level-field",
            changes_existing_field_type=True,
        )
        self.assertEqual(assessment["classification"], "breaking")
        self.assertEqual(assessment["required_version_change"], "major")
        self.assertIn("type of an existing governed Hermes inventory JSON field is breaking", assessment["reason"])

    def test_hermes_inventory_json_schema_policy_classifies_root_and_project_shape_drift_as_breaking(self) -> None:
        root_assessment = assess_hermes_inventory_json_change("remove-governed-root-field")
        project_assessment = assess_hermes_inventory_json_change("change-governed-project-field-type")
        self.assertEqual(root_assessment["classification"], "breaking")
        self.assertEqual(root_assessment["required_version_change"], "major")
        self.assertIn("remove-governed-root-field", root_assessment["reason"])
        self.assertEqual(project_assessment["classification"], "breaking")
        self.assertEqual(project_assessment["required_version_change"], "major")
        self.assertIn("change-governed-project-field-type", project_assessment["reason"])

    def test_hermes_inventory_json_schema_policy_classifies_classification_vocabulary_drift_as_breaking(self) -> None:
        root_assessment = assess_hermes_inventory_json_change("change-root-classification-vocabulary")
        project_assessment = assess_hermes_inventory_json_change(
            "add-governed-project-field",
            changes_classification_vocabulary=True,
        )
        self.assertEqual(root_assessment["classification"], "breaking")
        self.assertEqual(root_assessment["required_version_change"], "major")
        self.assertIn("change-root-classification-vocabulary", root_assessment["reason"])
        self.assertEqual(project_assessment["classification"], "breaking")
        self.assertEqual(project_assessment["required_version_change"], "major")
        self.assertIn("classification vocabulary is breaking", project_assessment["reason"])

    def test_hermes_inventory_json_schema_policy_classifies_safety_and_dry_run_semantics_as_breaking(self) -> None:
        safety_assessment = assess_hermes_inventory_json_change("change-safety-flag-semantics")
        dry_run_assessment = assess_hermes_inventory_json_change(
            "add-governed-root-field",
            changes_dry_run_gating=True,
        )
        self.assertEqual(safety_assessment["classification"], "breaking")
        self.assertEqual(safety_assessment["required_version_change"], "major")
        self.assertIn("change-safety-flag-semantics", safety_assessment["reason"])
        self.assertEqual(dry_run_assessment["classification"], "breaking")
        self.assertEqual(dry_run_assessment["required_version_change"], "major")
        self.assertIn("dry-run gating is breaking", dry_run_assessment["reason"])

    def test_hermes_inventory_json_schema_policy_classifies_ordering_and_read_only_semantics_as_breaking(self) -> None:
        ordering_assessment = assess_hermes_inventory_json_change(
            "change-deterministic-ordering-guarantee"
        )
        read_only_assessment = assess_hermes_inventory_json_change(
            "add-governed-project-field",
            changes_read_only_behavior=True,
        )
        target_write_assessment = assess_hermes_inventory_json_change("allow-target-repo-writes")
        self.assertEqual(ordering_assessment["classification"], "breaking")
        self.assertEqual(ordering_assessment["required_version_change"], "major")
        self.assertIn("change-deterministic-ordering-guarantee", ordering_assessment["reason"])
        self.assertEqual(read_only_assessment["classification"], "breaking")
        self.assertEqual(read_only_assessment["required_version_change"], "major")
        self.assertIn("read-only behavior is breaking", read_only_assessment["reason"])
        self.assertEqual(target_write_assessment["classification"], "breaking")
        self.assertEqual(target_write_assessment["required_version_change"], "major")
        self.assertIn("allow-target-repo-writes", target_write_assessment["reason"])

    def test_hermes_inventory_json_schema_policy_gates_additive_keys(self) -> None:
        payload = build_valid_hermes_inventory_payload()
        payload["future_field"] = "not-allowed-yet"
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(payload)
        self.assertIn("Hermes inventory payload keys drifted", str(error.exception))
        self.assertIn("Unexpected keys", str(error.exception))
        self.assertIn("future_field", str(error.exception))

        assessment = assess_hermes_inventory_json_change("add-governed-top-level-field")
        self.assertEqual(assessment["classification"], "reserved-additive-requires-policy-update")
        self.assertEqual(assessment["required_version_change"], "minor")
        self.assertTrue(assessment["requires_policy_update"])
        self.assertTrue(assessment["read_only_behavior_must_remain"])
        self.assertIn("minor schema-version bump", assessment["reason"])

    def test_hermes_inventory_future_minor_compatibility_example_is_optional_and_not_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "inventory-root"
            root.mkdir()
            self.create_v2_repo(root, "alpha-v2")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            result = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            live_payload = verify_hermes_inventory_json_stdout(
                result.stdout,
                expected_roots_config_path=config,
            )
            self.assertEqual(live_payload["schema_version"], EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION)
            self.assertNotIn(HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD, live_payload)

            example = build_hermes_inventory_future_minor_compatibility_example(live_payload)
            verified = verify_hermes_inventory_future_minor_compatibility_example(example)

            self.assertEqual(
                verified["schema_version"],
                SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
            )
            example_field = verified[HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD]
            self.assertEqual(example_field["status"], "example-only")
            self.assertEqual(example_field["schema_surface"], "hermes_inventory")
            self.assertEqual(
                example_field["future_minor_version"],
                SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
            )
            self.assertTrue(example_field["optional_for_consumers"])
            self.assertTrue(example_field["live_contract_unchanged"])
            for key, value in live_payload.items():
                if key == "schema_version":
                    continue
                self.assertEqual(verified[key], value)

    def test_hermes_inventory_future_minor_compatibility_example_still_fails_live_exact_key_validation(self) -> None:
        example = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_json_payload(example)
        self.assertIn("Hermes inventory payload keys drifted", str(error.exception))
        self.assertIn("Unexpected keys", str(error.exception))
        self.assertIn(HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD, str(error.exception))

    def test_hermes_inventory_future_minor_compatibility_example_rejects_breaking_type_drift(self) -> None:
        example = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        example["classification_counts"] = []
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_future_minor_compatibility_example(example)
        self.assertIn("Hermes inventory payload.classification_counts", str(error.exception))
        self.assertIn("JSON object", str(error.exception))

    def test_hermes_inventory_future_minor_compatibility_example_rejects_classification_vocabulary_drift(self) -> None:
        example = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        example["roots"][0]["projects"][0]["classification"] = "future-project"
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_future_minor_compatibility_example(example)
        self.assertIn("Hermes inventory project payload.classification", str(error.exception))
        self.assertIn("legacy", str(error.exception))

    def test_hermes_inventory_future_minor_compatibility_example_rejects_safety_flag_drift(self) -> None:
        example = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        example["target_repos_modified"] = True
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_future_minor_compatibility_example(example)
        self.assertIn("Hermes inventory payload.target_repos_modified", str(error.exception))
        self.assertIn("false", str(error.exception))

    def test_hermes_inventory_future_minor_compatibility_example_rejects_dry_run_or_read_only_drift(self) -> None:
        dry_run_drift = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        dry_run_drift["dry_run"] = False
        with self.assertRaises(AssertionError) as dry_run_error:
            verify_hermes_inventory_future_minor_compatibility_example(dry_run_drift)
        self.assertIn("Hermes inventory payload.dry_run", str(dry_run_error.exception))

        read_only_drift = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        read_only_drift["migration_writes_enabled"] = True
        with self.assertRaises(AssertionError) as read_only_error:
            verify_hermes_inventory_future_minor_compatibility_example(read_only_drift)
        self.assertIn("Hermes inventory payload.migration_writes_enabled", str(read_only_error.exception))
        self.assertIn("false", str(read_only_error.exception))

    def test_hermes_inventory_future_minor_compatibility_example_rejects_deterministic_ordering_drift(self) -> None:
        example = build_hermes_inventory_future_minor_compatibility_example(
            build_valid_hermes_inventory_payload()
        )
        example["roots"] = [
            {
                "path": "/tmp/z-root",
                "classification": "configured-root",
                "exists": True,
                "is_directory": True,
                "project_count": 0,
                "issues": [],
                "projects": [],
            },
            example["roots"][0],
        ]
        with self.assertRaises(AssertionError) as error:
            verify_hermes_inventory_future_minor_compatibility_example(example)
        self.assertIn("ordered deterministically by root path", str(error.exception))

    def test_json_contract_invariant_failure_is_clear_for_missing_status_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-contract-missing-status-key-repo")
            result = self.run_cli(repo, "status", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            payload.pop("health_overview")
            with self.assertRaises(AssertionError) as error:
                verify_json_contract_stdout(json.dumps(payload) + "\n", "status")
            self.assertIn("status payload", str(error.exception))
            self.assertIn("Missing keys", str(error.exception))
            self.assertIn("health_overview", str(error.exception))

    def test_json_contract_invariant_failure_is_clear_for_missing_health_subsystem(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-contract-missing-health-repo")
            result = self.run_cli(repo, "doctor", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            payload["health"].pop("command_help_docs")
            with self.assertRaises(AssertionError) as error:
                verify_json_contract_stdout(json.dumps(payload) + "\n", "doctor")
            self.assertIn("health", str(error.exception))
            self.assertIn("command_help_docs", str(error.exception))

    def test_json_schema_policy_is_explicit_shared_and_gated(self) -> None:
        policy = verify_json_contract_evolution_policy()
        self.assertEqual(policy["shared_schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)
        self.assertTrue(policy["all_surfaces_share_version"])
        self.assertFalse(policy["command_specific_versioning"])
        self.assertFalse(policy["additive_keys_allowed"])
        self.assertEqual(policy["versioning_mode"], "shared")
        self.assertEqual(policy["versioning_scheme"], "semver")
        self.assertEqual(policy["patch_change_rule"], "no-governed-contract-change")
        self.assertEqual(
            policy["minor_change_rule"],
            "reserved-for-future-additive-compatible-changes",
        )
        self.assertEqual(
            policy["major_change_rule"],
            "required-for-breaking-contract-changes",
        )
        self.assertTrue(policy["breaking_changes_require_version_bump"])
        self.assertTrue(policy["coordinated_updates_required"])
        self.assertEqual(
            policy["breaking_change_categories"],
            (
                "remove-governed-top-level-field",
                "rename-governed-top-level-field",
                "change-governed-field-type",
                "remove-governed-health-subsystem",
                "change-pass-warning-fail-vocabulary",
                "change-doctor-exit-code-semantics",
            ),
        )
        self.assertEqual(
            policy["additive_change_categories"],
            (
                "add-governed-top-level-field",
                "add-governed-nested-field",
                "add-governed-health-subsystem",
            ),
        )

    def test_json_schema_policy_enforces_shared_schema_version_across_governed_commands(self) -> None:
        policy = verify_json_contract_evolution_policy()
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-schema-version-repo")
            commands = {
                "status": ("status", "--json"),
                "doctor": ("doctor", "--json"),
                "doctor_write_report": ("doctor", "--write-report", "--json"),
                "roots": ("roots", "--format", "json"),
            }
            observed_versions: dict[str, str] = {}
            for surface, args in commands.items():
                result = self.run_cli(repo, *args)
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                kwargs: dict[str, object] = {}
                if surface == "doctor_write_report":
                    kwargs = {
                        "expect_wrote_report": True,
                        "expected_drift_report_path": repo / ".specify/state/drift.md",
                    }
                payload = verify_json_contract_stdout(result.stdout, surface, **kwargs)
                observed_versions[surface] = payload["schema_version"]
            self.assertEqual(set(observed_versions.keys()), set(JSON_CONTRACT_SURFACES))
            self.assertEqual(set(observed_versions.values()), {policy["shared_schema_version"]})

    def test_json_schema_policy_failure_is_clear_for_type_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-schema-type-change-repo")
            result = self.run_cli(repo, "doctor", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            payload["passed"] = "yes"
            with self.assertRaises(AssertionError) as error:
                verify_json_contract_stdout(json.dumps(payload) + "\n", "doctor")
            self.assertIn("doctor payload.passed", str(error.exception))
            self.assertIn("boolean", str(error.exception))

    def test_json_schema_policy_failure_is_clear_for_additive_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-schema-additive-key-repo")
            result = self.run_cli(repo, "status", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            payload["future_field"] = "not-allowed-yet"
            with self.assertRaises(AssertionError) as error:
                verify_json_contract_stdout(json.dumps(payload) + "\n", "status")
            self.assertIn("status payload", str(error.exception))
            self.assertIn("Unexpected keys", str(error.exception))
            self.assertIn("future_field", str(error.exception))
            self.assertIn("intentionally gated", str(error.exception))
            self.assertIn("minor-version path", str(error.exception))

    def test_json_additive_policy_is_reserved_and_not_enabled(self) -> None:
        policy = verify_json_contract_reserved_additive_policy()
        self.assertEqual(policy["status"], "reserved-not-enabled")
        self.assertFalse(policy["enabled_by_default"])
        self.assertEqual(policy["current_schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)
        self.assertEqual(policy["future_minor_version_path"], "reserved-shared-minor-version-bump")
        self.assertTrue(policy["minor_version_bump_required"])
        self.assertTrue(policy["all_surfaces_must_move_together"])
        self.assertFalse(policy["command_specific_additions_allowed"])
        self.assertTrue(policy["new_fields_must_be_optional_for_consumers"])
        self.assertTrue(policy["new_fields_must_not_change_existing_field_meaning"])
        self.assertTrue(policy["new_fields_must_not_change_existing_field_types"])
        self.assertTrue(policy["new_fields_must_not_change_status_vocabulary"])
        self.assertTrue(policy["new_fields_must_not_change_doctor_exit_code_semantics"])
        self.assertIn("shared-minor-version-upgrade", policy["consumer_unknown_field_rule_when_enabled"])

    def test_json_additive_policy_classifies_reserved_minor_path(self) -> None:
        assessment = assess_json_contract_change("add-governed-top-level-field")
        self.assertEqual(assessment["classification"], "reserved-additive-requires-policy-update")
        self.assertEqual(assessment["required_version_change"], "minor")
        self.assertTrue(assessment["requires_policy_update"])
        self.assertTrue(assessment["all_surfaces_must_move_together"])
        self.assertIn("shared minor schema-version bump", assessment["reason"])
        self.assertIn("unknown-optional-fields", assessment["consumer_guidance"])

    def test_json_additive_policy_rejects_command_specific_addition(self) -> None:
        assessment = assess_json_contract_change(
            "add-governed-nested-field",
            command_specific_addition=True,
        )
        self.assertEqual(assessment["classification"], "reserved-additive-policy-violation")
        self.assertEqual(assessment["required_version_change"], "minor")
        self.assertTrue(assessment["requires_policy_update"])
        self.assertIn("command-specific additive fields are not allowed", assessment["reason"])

    def test_json_additive_policy_classifies_type_or_meaning_change_as_breaking(self) -> None:
        type_assessment = assess_json_contract_change(
            "add-governed-top-level-field",
            changes_existing_field_type=True,
        )
        meaning_assessment = assess_json_contract_change(
            "add-governed-nested-field",
            changes_existing_field_meaning=True,
        )
        self.assertEqual(type_assessment["classification"], "breaking")
        self.assertEqual(type_assessment["required_version_change"], "major")
        self.assertIn("type of an existing governed field is breaking", type_assessment["reason"])
        self.assertEqual(meaning_assessment["classification"], "breaking")
        self.assertEqual(meaning_assessment["required_version_change"], "major")
        self.assertIn("meaning of an existing governed field is breaking", meaning_assessment["reason"])

    def test_json_additive_policy_classifies_vocabulary_or_exit_change_as_breaking(self) -> None:
        vocab_assessment = assess_json_contract_change(
            "add-governed-health-subsystem",
            changes_status_vocabulary=True,
        )
        exit_assessment = assess_json_contract_change(
            "add-governed-health-subsystem",
            changes_doctor_exit_code_semantics=True,
        )
        self.assertEqual(vocab_assessment["classification"], "breaking")
        self.assertEqual(vocab_assessment["required_version_change"], "major")
        self.assertIn("pass/warning/fail vocabulary is breaking", vocab_assessment["reason"])
        self.assertEqual(exit_assessment["classification"], "breaking")
        self.assertEqual(exit_assessment["required_version_change"], "major")
        self.assertIn("doctor exit-code semantics is breaking", exit_assessment["reason"])

    def test_json_additive_policy_classifies_breaking_category_as_breaking(self) -> None:
        assessment = assess_json_contract_change("remove-governed-top-level-field")
        self.assertEqual(assessment["classification"], "breaking")
        self.assertEqual(assessment["required_version_change"], "major")
        self.assertIn("explicitly governed as breaking", assessment["reason"])

    def test_json_future_minor_compatibility_example_is_shared_optional_and_not_live(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-example-repo")
            live_payloads = self.collect_governed_json_payloads(repo)

            self.assertEqual(set(live_payloads.keys()), set(JSON_CONTRACT_SURFACES))
            for surface, payload in live_payloads.items():
                self.assertEqual(payload["schema_version"], EXPECTED_JSON_CONTRACT_SCHEMA_VERSION)
                self.assertNotIn(JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD, payload, surface)

            examples = build_future_minor_compatibility_examples(live_payloads)
            verified = verify_future_minor_compatibility_examples(examples)

            self.assertEqual(set(verified.keys()), set(JSON_CONTRACT_SURFACES))
            for surface in JSON_CONTRACT_SURFACES:
                payload = verified[surface]
                self.assertEqual(
                    payload["schema_version"],
                    SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION,
                )
                example = payload[JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD]
                self.assertEqual(example["status"], "example-only")
                self.assertTrue(example["optional_for_consumers"])
                self.assertTrue(example["live_contract_unchanged"])
                self.assertEqual(
                    example["shared_minor_version"],
                    SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION,
                )
                for key, value in live_payloads[surface].items():
                    if key == "schema_version":
                        continue
                    self.assertEqual(payload[key], value)

    def test_json_future_minor_compatibility_example_rejects_partial_command_movement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-partial-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            examples.pop("roots")
            with self.assertRaises(AssertionError) as error:
                verify_future_minor_compatibility_examples(examples)
            self.assertIn("all governed JSON commands together", str(error.exception))

    def test_json_future_minor_compatibility_example_still_fails_live_exact_key_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-live-baseline-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            with self.assertRaises(AssertionError) as error:
                verify_json_contract_stdout(
                    json.dumps(examples["status"]) + "\n",
                    "status",
                )
            self.assertIn("status payload", str(error.exception))
            self.assertIn("Unexpected keys", str(error.exception))
            self.assertIn(JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD, str(error.exception))
            self.assertIn("intentionally gated", str(error.exception))

    def test_json_future_minor_compatibility_example_rejects_breaking_type_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-breaking-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            examples["doctor"]["passed"] = "yes"
            with self.assertRaises(AssertionError) as error:
                verify_future_minor_compatibility_examples(examples)
            self.assertIn("doctor payload.passed", str(error.exception))
            self.assertIn("boolean", str(error.exception))

    def test_json_future_minor_consumer_example_tolerates_and_preserves_optional_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-consumer-repo")
            live_payloads = self.collect_governed_json_payloads(repo)
            examples = build_future_minor_compatibility_examples(live_payloads)
            consumed = consume_future_minor_optional_fields_example(examples)
            verified = verify_future_minor_consumer_handling_example(consumed)

            self.assertEqual(set(verified.keys()), set(JSON_CONTRACT_SURFACES))
            for surface in JSON_CONTRACT_SURFACES:
                item = verified[surface]
                self.assertEqual(
                    item["schema_version"],
                    SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION,
                )
                self.assertEqual(item["consumer_mode"], JSON_CONTRACT_CONSUMER_EXAMPLE_MODE)
                self.assertEqual(
                    item["tolerated_optional_fields"],
                    [JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD],
                )
                self.assertNotIn(
                    JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD,
                    item["known_payload"],
                )
                self.assertIn(
                    JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD,
                    item["preserved_optional_fields"],
                )
                self.assertEqual(
                    item["known_payload"]["command"],
                    live_payloads[surface]["command"],
                )
                self.assertEqual(
                    item["preserved_optional_fields"][JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD][
                        "shared_minor_version"
                    ],
                    SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION,
                )

    def test_json_future_minor_consumer_example_rejects_missing_known_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-consumer-missing-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            examples["status"].pop("health_overview")
            with self.assertRaises(AssertionError) as error:
                consume_future_minor_optional_fields_example(examples)
            self.assertIn("status", str(error.exception))
            self.assertIn("missing current governed keys", str(error.exception))
            self.assertIn("health_overview", str(error.exception))

    def test_json_future_minor_consumer_example_rejects_known_field_type_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-consumer-type-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            examples["doctor"]["passed"] = "yes"
            with self.assertRaises(AssertionError) as error:
                consume_future_minor_optional_fields_example(examples)
            self.assertIn("doctor payload.passed", str(error.exception))
            self.assertIn("boolean", str(error.exception))

    def test_json_future_minor_consumer_example_rejects_status_vocabulary_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-consumer-vocab-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            examples["doctor"]["result_status"] = "warning"
            examples["doctor"]["passed"] = False
            with self.assertRaises(AssertionError) as error:
                consume_future_minor_optional_fields_example(examples)
            self.assertIn("doctor payload.result_status", str(error.exception))
            self.assertIn("pass` or `fail", str(error.exception))

    def test_json_future_minor_consumer_example_rejects_partial_command_movement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "json-future-minor-consumer-partial-repo")
            examples = build_future_minor_compatibility_examples(
                self.collect_governed_json_payloads(repo)
            )
            examples.pop("roots")
            with self.assertRaises(AssertionError) as error:
                consume_future_minor_optional_fields_example(examples)
            self.assertIn("all governed JSON commands together", str(error.exception))

    def test_workflow_status_includes_command_help_docs_consistency_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "command-docs-status-repo")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Command/help/docs consistency", result.stdout)
            self.assertIn("- Status: pass", result.stdout)
            self.assertIn(f"- Path: `{ROOT}`", result.stdout)
            self.assertIn(
                "CLI commands, wrapper guidance, help text, and repo docs align with the current v2 model.",
                result.stdout,
            )

    def test_workflow_doctor_reports_command_help_docs_consistency_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "command-docs-doctor-repo")
            result = self.run_cli(repo, "doctor")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- command/help/docs consistency: pass", result.stdout)
            self.assertIn(f"- command/help/docs root: {ROOT}", result.stdout)
            self.assertIn(
                "- command/help/docs summary: CLI commands, wrapper guidance, help text, and repo docs align with the current v2 model.",
                result.stdout,
            )

    def test_help_snapshot_fixtures_exist_for_all_expected_commands(self) -> None:
        expected_paths = expected_snapshot_paths()
        self.assertEqual(set(expected_paths.keys()), set(HELP_SNAPSHOT_LABELS))
        for label, path in expected_paths.items():
            self.assertTrue(path.exists(), f"Missing help snapshot for `{label}`: {path}")

    def test_help_snapshots_match_current_cli_help(self) -> None:
        verify_help_snapshots()

    def test_help_snapshot_verification_reports_missing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "help"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            for label, path in expected_snapshot_paths().items():
                if label == "workflow save":
                    continue
                target = fixture_dir / path.name
                target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

            with self.assertRaises(FileNotFoundError) as error:
                from tests.help_snapshots import load_expected_help_snapshots

                load_expected_help_snapshots(fixture_dir)

            self.assertIn("Missing help snapshot for `workflow save`", str(error.exception))

    def test_help_snapshot_verification_reports_mismatch_with_command_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "help"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            for _, path in expected_snapshot_paths().items():
                target = fixture_dir / path.name
                target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

            mismatch_path = snapshot_path_for_label("workflow status", fixture_dir)
            mismatch_path.write_text("usage: workflow status\nBROKEN SNAPSHOT\n", encoding="utf-8")

            with self.assertRaises(AssertionError) as error:
                verify_help_snapshots(fixture_dir)

            message = str(error.exception)
            self.assertIn("Help snapshot mismatch for `workflow status`", message)
            self.assertIn("workflow-status.txt", message)

    def test_update_help_snapshots_script_requires_explicit_write_flag(self) -> None:
        result = subprocess.run(
            ["/usr/bin/env", "python3", str(UPDATE_HELP_SNAPSHOTS)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--write", result.stderr)

    def test_update_help_snapshots_script_writes_snapshots_to_explicit_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "help"
            result = subprocess.run(
                [
                    "/usr/bin/env",
                    "python3",
                    str(UPDATE_HELP_SNAPSHOTS),
                    "--write",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wrote 11 help snapshot files", result.stdout)
            self.assertTrue((output_dir / "workflow.txt").exists())
            self.assertTrue((output_dir / "workflow-save.txt").exists())

    def test_wrapper_help_fixtures_exist_for_expected_outputs(self) -> None:
        expected_paths = expected_wrapper_fixture_paths()
        self.assertEqual(set(expected_paths.keys()), set(WRAPPER_HELP_CASES.keys()))
        for label, path in expected_paths.items():
            self.assertTrue(path.exists(), f"Missing wrapper fixture for `{label}`: {path}")

    def test_wrapper_help_fixtures_match_current_outputs(self) -> None:
        verify_wrapper_help_fixtures()

    def test_wrapper_help_fixture_verification_reports_missing_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "wrapper-help"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            for label, path in expected_wrapper_fixture_paths().items():
                if label == "project-open-invalid-argument":
                    continue
                target = fixture_dir / path.name
                target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

            with self.assertRaises(FileNotFoundError) as error:
                from tests.wrapper_help_fixtures import load_expected_wrapper_fixtures

                load_expected_wrapper_fixtures(fixture_dir)

            self.assertIn("Missing wrapper fixture for `project-open-invalid-argument`", str(error.exception))

    def test_wrapper_help_fixture_verification_reports_mismatch_with_fixture_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "wrapper-help"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            for _, path in expected_wrapper_fixture_paths().items():
                target = fixture_dir / path.name
                target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

            mismatch_path = wrapper_fixture_path_for_label("project-add-root-instructions", fixture_dir)
            mismatch_path.write_text("exit=0\nBROKEN WRAPPER FIXTURE\n", encoding="utf-8")

            with self.assertRaises(AssertionError) as error:
                verify_wrapper_help_fixtures(fixture_dir)

            message = str(error.exception)
            self.assertIn("Wrapper fixture mismatch for `project-add-root-instructions`", message)
            self.assertIn("project-add-root-instructions.txt", message)

    def test_update_wrapper_help_fixtures_script_requires_explicit_write_flag(self) -> None:
        result = subprocess.run(
            ["/usr/bin/env", "python3", str(UPDATE_WRAPPER_HELP_FIXTURES)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--write", result.stderr)

    def test_update_wrapper_help_fixtures_script_writes_to_explicit_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "wrapper-help"
            result = subprocess.run(
                [
                    "/usr/bin/env",
                    "python3",
                    str(UPDATE_WRAPPER_HELP_FIXTURES),
                    "--write",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wrote 3 wrapper-help fixture files", result.stdout)
            self.assertTrue((output_dir / "project-add-root-usage.txt").exists())
            self.assertTrue((output_dir / "project-open-invalid-argument.txt").exists())

    def test_wrapper_entrypoint_fixture_exists(self) -> None:
        path = entrypoint_fixture_path()
        self.assertEqual(path.parent, WRAPPER_ENTRYPOINT_FIXTURE_DIR)
        self.assertTrue(path.exists(), f"Missing wrapper entrypoint fixture: {path}")

    def test_wrapper_entrypoint_fixture_matches_current_file(self) -> None:
        verify_wrapper_entrypoint_fixture()

    def test_wrapper_entrypoint_verification_reports_missing_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "wrapper-entrypoint"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            with self.assertRaises(FileNotFoundError) as error:
                verify_wrapper_entrypoint_fixture(fixture_dir)
            self.assertIn("Missing wrapper entrypoint fixture", str(error.exception))

    def test_wrapper_entrypoint_fixture_mismatch_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "wrapper-entrypoint"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            path = entrypoint_fixture_path(fixture_dir)
            path.write_text("#!/usr/bin/env zsh\nBROKEN ENTRYPOINT\n", encoding="utf-8")
            with self.assertRaises(AssertionError) as error:
                verify_wrapper_entrypoint_fixture(fixture_dir)
            self.assertIn("Wrapper entrypoint fixture mismatch", str(error.exception))
            self.assertIn("workflow-wrapper.txt", str(error.exception))

    def test_wrapper_entrypoint_invariant_failure_is_clear(self) -> None:
        broken = (
            '#!/usr/bin/env zsh\n'
            'WORKFLOW_WRAPPER_SOURCE="${${(%):-%x}:A}"\n'
            'WORKFLOW_WRAPPER_HOME="${WORKFLOW_WRAPPER_SOURCE:h:h}"\n'
            'source "$WORKFLOW_WRAPPER_HOME/scripts/workflow.sh"\n'
            '"$cmd" "$@"\n'
        )
        with self.assertRaises(AssertionError) as error:
            verify_wrapper_entrypoint_fixture(current_text=broken)
        self.assertIn("dispatch-by-basename", str(error.exception))

    def test_update_wrapper_entrypoint_fixtures_script_requires_explicit_write_flag(self) -> None:
        result = subprocess.run(
            ["/usr/bin/env", "python3", str(UPDATE_WRAPPER_ENTRYPOINT_FIXTURES)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--write", result.stderr)

    def test_update_wrapper_entrypoint_fixtures_script_writes_to_explicit_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "wrapper-entrypoint"
            result = subprocess.run(
                [
                    "/usr/bin/env",
                    "python3",
                    str(UPDATE_WRAPPER_ENTRYPOINT_FIXTURES),
                    "--write",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wrote wrapper-entrypoint fixture", result.stdout)
            self.assertTrue((output_dir / "workflow-wrapper.txt").exists())

    def test_shell_bridge_fixture_exists(self) -> None:
        path = shell_bridge_fixture_path()
        self.assertEqual(path.parent, SHELL_BRIDGE_FIXTURE_DIR)
        self.assertTrue(path.exists(), f"Missing shell-bridge fixture: {path}")

    def test_shell_bridge_fixture_matches_current_profile(self) -> None:
        verify_shell_bridge_fixture()

    def test_shell_bridge_verification_reports_missing_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "shell-bridge"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            with self.assertRaises(FileNotFoundError) as error:
                verify_shell_bridge_fixture(fixture_dir)
            self.assertIn("Missing shell-bridge fixture", str(error.exception))

    def test_shell_bridge_fixture_mismatch_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_dir = Path(temp_dir) / "shell-bridge"
            fixture_dir.mkdir(parents=True, exist_ok=True)
            path = shell_bridge_fixture_path(fixture_dir)
            path.write_text("script: scripts/workflow.sh\n\nBROKEN PROFILE\n", encoding="utf-8")
            with self.assertRaises(AssertionError) as error:
                verify_shell_bridge_fixture(fixture_dir)
            self.assertIn("Shell-bridge fixture mismatch", str(error.exception))
            self.assertIn("workflow-sh-profile.txt", str(error.exception))

    def test_shell_bridge_invariant_failure_is_clear(self) -> None:
        broken = SCRIPT.read_text(encoding="utf-8").replace(
            'roots_payload=$(workflow roots --format shell) || return 1',
            'roots_payload=$(print "skip cli roots") || return 1',
        )
        with self.assertRaises(AssertionError) as error:
            verify_shell_bridge_fixture(current_text=broken)
        self.assertIn("cli-roots-shell-export", str(error.exception))

    def test_update_shell_bridge_fixtures_script_requires_explicit_write_flag(self) -> None:
        result = subprocess.run(
            ["/usr/bin/env", "python3", str(UPDATE_SHELL_BRIDGE_FIXTURES)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--write", result.stderr)

    def test_update_shell_bridge_fixtures_script_writes_to_explicit_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "shell-bridge"
            result = subprocess.run(
                [
                    "/usr/bin/env",
                    "python3",
                    str(UPDATE_SHELL_BRIDGE_FIXTURES),
                    "--write",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Wrote shell-bridge fixture", result.stdout)
            self.assertTrue((output_dir / "workflow-sh-profile.txt").exists())

    def test_cli_entrypoint_invariant_baseline_exists(self) -> None:
        self.assertEqual(CLI_ENTRYPOINT, ROOT / "bin/workflow")
        self.assertTrue(CLI_ENTRYPOINT.exists(), f"Missing CLI entrypoint: {CLI_ENTRYPOINT}")
        self.assertTrue(REQUIRED_CLI_ENTRYPOINT_SNIPPETS)
        self.assertTrue(FORBIDDEN_CLI_ENTRYPOINT_SNIPPETS)

    def test_cli_entrypoint_invariants_match_current_file(self) -> None:
        verify_cli_entrypoint_invariants()

    def test_cli_entrypoint_invariant_failure_is_clear_for_missing_required_snippet(self) -> None:
        broken = CLI_ENTRYPOINT.read_text(encoding="utf-8").replace(
            "from workflow_manager.cli import main",
            "from workflow_manager.cli import cli_main",
        )
        with self.assertRaises(AssertionError) as error:
            verify_cli_entrypoint_invariants(broken)
        self.assertIn("cli-main-import", str(error.exception))

    def test_cli_entrypoint_invariant_failure_is_clear_for_forbidden_snippet(self) -> None:
        broken = CLI_ENTRYPOINT.read_text(encoding="utf-8") + "\n# .ai/context/scaffold-template\n"
        with self.assertRaises(AssertionError) as error:
            verify_cli_entrypoint_invariants(broken)
        self.assertIn("legacy-scaffold-template", str(error.exception))

    def test_cli_entrypoint_governance_is_invariant_only(self) -> None:
        self.assertFalse((ROOT / "tests/fixtures/cli-entrypoint").exists())
        self.assertFalse((ROOT / "scripts/update_cli_entrypoint_fixtures.py").exists())

    def test_workflow_status_includes_memory_health_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "memory-health-repo")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Memory health", result.stdout)
            self.assertIn("All 5 memory files are structurally healthy.", result.stdout)

    def test_workflow_doctor_reports_memory_health_pass_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "memory-pass-repo")
            result = self.run_cli(repo, "doctor")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("- memory health: pass", result.stdout)

    def test_workflow_status_includes_continuity_state_health_for_valid_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "continuity-health-repo")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Continuity-state health", result.stdout)
            self.assertIn("All 5 continuity-state files are structurally healthy.", result.stdout)

    def test_workflow_status_surfaces_continuity_state_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "continuity-status-fail-repo")
            write(repo / ".specify/state/handoff.md", "# Handoff\n")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Continuity-state health", result.stdout)
            self.assertIn("- Status: fail", result.stdout)
            self.assertIn("handoff.md", result.stdout)
            self.assertIn("missing a next-step handoff signal", result.stdout)

    def test_health_overview_reports_fail_when_one_subsystem_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "overview-fail-repo")
            write(repo / ".specify/memory/project.md", "")
            status_result = self.run_cli(repo, "status")
            self.assertEqual(status_result.returncode, 0, status_result.stderr)
            self.assertIn("Health overview", status_result.stdout)
            self.assertIn("- Overall health: fail", status_result.stdout)
            self.assertIn("memory=fail", status_result.stdout)
            self.assertIn("- Pre-Hermes readiness: blocked", status_result.stdout)

            doctor_result = self.run_cli(repo, "doctor")
            self.assertNotEqual(doctor_result.returncode, 0)
            self.assertIn("- health overview: fail", doctor_result.stdout)
            self.assertIn("memory=fail", doctor_result.stdout)
            self.assertIn("- pre-hermes readiness: blocked", doctor_result.stdout)
            self.assertIn("Memory error: Memory file `.specify/memory/project.md` is empty.", doctor_result.stdout)

    def test_evaluate_command_docs_health_reports_missing_cli_command(self) -> None:
        snapshot = workflow_cli.build_cli_surface_snapshot()
        snapshot.commands = [command for command in snapshot.commands if command != "save"]
        health = workflow_cli.evaluate_command_docs_health(manager_home=ROOT, cli_snapshot=snapshot)
        self.assertEqual(health.status, "fail")
        self.assertTrue(any("CLI command `save` is missing" in issue.message for issue in health.failures))

    def test_evaluate_command_docs_health_reports_missing_wrapper_function(self) -> None:
        script_text = SCRIPT.read_text(encoding="utf-8").replace("project-sync()", "project-sync-renamed()")
        health = workflow_cli.evaluate_command_docs_health(manager_home=ROOT, script_text=script_text)
        self.assertEqual(health.status, "fail")
        self.assertTrue(any("Wrapper command `project-sync` is missing" in issue.message for issue in health.failures))

    def test_evaluate_command_docs_health_reports_stale_wrapper_guidance(self) -> None:
        script_text = SCRIPT.read_text(encoding="utf-8") + '\necho "Edit scripts/workflow.sh as the primary way to add roots."\n'
        health = workflow_cli.evaluate_command_docs_health(manager_home=ROOT, script_text=script_text)
        self.assertEqual(health.status, "fail")
        self.assertTrue(any("tells users to edit `scripts/workflow.sh`" in issue.message for issue in health.failures))

    def test_evaluate_command_docs_health_reports_help_text_contradiction(self) -> None:
        snapshot = workflow_cli.build_cli_surface_snapshot()
        snapshot.help_texts["workflow roots"] = "usage: workflow roots\n"
        health = workflow_cli.evaluate_command_docs_health(manager_home=ROOT, cli_snapshot=snapshot)
        self.assertEqual(health.status, "fail")
        self.assertTrue(any("`workflow roots --help` must describe `.workflow/roots.json`" in issue.message for issue in health.failures))

    def test_workflow_status_surfaces_stale_readme_root_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "stale-readme-roots-repo")
            manager_home = build_manager_home(
                Path(temp_dir),
                readme_text=(
                    (ROOT / "README.md").read_text(encoding="utf-8")
                    + "\nEdit scripts/workflow.sh as the primary way to add roots.\n"
                ),
            )
            result = self.run_cli(repo, "status", env={"WORKFLOW_MANAGER_HOME": str(manager_home)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Health overview", result.stdout)
            self.assertIn("command/help/docs=fail", result.stdout)
            self.assertIn("Command/help/docs consistency", result.stdout)
            self.assertIn("- Status: fail", result.stdout)
            self.assertIn("tells users to edit `scripts/workflow.sh`", result.stdout)

    def test_workflow_doctor_surfaces_stale_scaffold_template_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "stale-template-repo")
            manager_home = build_manager_home(
                Path(temp_dir),
                readme_text=(
                    (ROOT / "README.md").read_text(encoding="utf-8")
                    + "\nThe primary new-project scaffold path is .ai/context/scaffold-template.\n"
                ),
            )
            result = self.run_cli(repo, "doctor", env={"WORKFLOW_MANAGER_HOME": str(manager_home)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- command/help/docs consistency: fail", result.stdout)
            self.assertIn("treats `.ai/context/scaffold-template` as live v2 scaffold guidance", result.stdout)

    def test_workflow_doctor_surfaces_stale_canonical_v2_ai_handoff_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "stale-ai-handoff-repo")
            manager_home = build_manager_home(
                Path(temp_dir),
                agents_text=(
                    (ROOT / "AGENTS.md").read_text(encoding="utf-8")
                    + "\nFor v2 repos, the canonical handoff is `.ai/handoffs/NEXT_STEP.md`.\n"
                ),
            )
            result = self.run_cli(repo, "doctor", env={"WORKFLOW_MANAGER_HOME": str(manager_home)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("treats `.ai/handoffs/NEXT_STEP.md` as canonical v2 guidance", result.stdout)

    def test_workflow_doctor_surfaces_stale_canonical_v2_ai_log_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "stale-ai-log-repo")
            manager_home = build_manager_home(
                Path(temp_dir),
                agents_text=(
                    (ROOT / "AGENTS.md").read_text(encoding="utf-8")
                    + "\nFor v2 repos, the primary session log is `.ai/logs/session.log`.\n"
                ),
            )
            result = self.run_cli(repo, "doctor", env={"WORKFLOW_MANAGER_HOME": str(manager_home)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("treats `.ai/logs/session.log` as the primary v2 session log", result.stdout)

    def test_workflow_doctor_surfaces_stale_live_implementation_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "stale-implementation-guidance-repo")
            manager_home = build_manager_home(
                Path(temp_dir),
                readme_text=(
                    (ROOT / "README.md").read_text(encoding="utf-8")
                    + "\nHermes is implemented.\nDashScope is integrated.\nQwen integration is complete.\nGraphify is implemented.\nFull spec-kit fork/preset is implemented.\n"
                ),
            )
            result = self.run_cli(repo, "doctor", env={"WORKFLOW_MANAGER_HOME": str(manager_home)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("claims Hermes is implemented", result.stdout)
            self.assertIn("claims DashScope integration is implemented", result.stdout)
            self.assertIn("claims Qwen integration is implemented", result.stdout)
            self.assertIn("claims Graphify is implemented", result.stdout)
            self.assertIn("claims a full spec-kit fork/preset is implemented", result.stdout)

    def test_workflow_status_surfaces_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-manifest-repo")
            (repo / ".workflow/workflow.json").unlink()
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Manifest health", result.stdout)
            self.assertIn("Missing manifest", result.stdout)

    def test_workflow_doctor_reports_invalid_manifest_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "invalid-manifest-repo")
            write(repo / ".workflow/workflow.json", "{ invalid json\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- manifest health: fail", result.stdout)
            self.assertIn("Manifest error: Invalid manifest", result.stdout)

    def test_workflow_doctor_reports_missing_manifest_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "manifest-key-repo")
            manifest_path = repo / ".workflow/workflow.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["canonical_contract"]
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required key `canonical_contract`", result.stdout)

    def test_workflow_doctor_reports_misleading_manifest_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "manifest-roots-repo", coexistence=True)
            manifest_path = repo / ".workflow/workflow.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["canonical_contract"] = "README.md"
            manifest["memory_root"] = ".memory"
            manifest["state_root"] = ".state"
            manifest["legacy_root"] = ".legacy"
            manifest["migration"]["status"] = "v2"
            manifest["migration"]["legacy_preserved"] = False
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must declare `canonical_contract` as `AGENTS.md`", result.stdout)
            self.assertIn("must declare `memory_root` as `.specify/memory`", result.stdout)
            self.assertIn("coexistence model", result.stdout)

    def test_workflow_doctor_reports_missing_constitution_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-constitution-repo")
            (repo / ".specify/memory/constitution.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- memory health: fail", result.stdout)
            self.assertIn("Memory error: Missing memory file `.specify/memory/constitution.md`.", result.stdout)

    def test_workflow_doctor_reports_empty_project_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "empty-project-memory-repo")
            write(repo / ".specify/memory/project.md", "")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Memory error: Memory file `.specify/memory/project.md` is empty.", result.stdout)

    def test_workflow_doctor_reports_missing_decisions_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-decisions-repo")
            (repo / ".specify/memory/decisions.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Memory error: Missing memory file `.specify/memory/decisions.md`.", result.stdout)

    def test_workflow_doctor_reports_empty_tech_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "empty-tech-repo")
            write(repo / ".specify/memory/tech.md", "")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Memory error: Memory file `.specify/memory/tech.md` is empty.", result.stdout)

    def test_workflow_doctor_reports_missing_constitution_canonical_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "constitution-signal-repo")
            write(
                repo / ".specify/memory/constitution.md",
                "# Constitution\n\n"
                "## Non-negotiables\n"
                "- Preserve continuity.\n\n"
                "## Continuity contract\n"
                "- Keep summaries in repo files.\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing the AGENTS-as-canonical signal", result.stdout)

    def test_workflow_doctor_reports_missing_project_identity_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "project-identity-repo")
            write(
                repo / ".specify/memory/project.md",
                "# Project Memory\n\n"
                "## Stable facts\n"
                "- Something exists.\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing a project identity or purpose signal", result.stdout)

    def test_workflow_doctor_reports_missing_durable_decisions_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "durable-decisions-repo", coexistence=True)
            write(
                repo / ".specify/memory/decisions.md",
                "# Decisions\n\n"
                "## Imported legacy context\n"
                "- Nothing imported.\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing a durable-decisions signal", result.stdout)

    def test_workflow_doctor_reports_missing_architecture_command_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "architecture-signal-repo")
            write(
                repo / ".specify/memory/architecture.md",
                "# Architecture\n\n"
                "## Layers\n"
                "- One layer.\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing a command-model signal", result.stdout)

    def test_workflow_doctor_reports_missing_tech_runtime_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "tech-runtime-repo")
            write(
                repo / ".specify/memory/tech.md",
                "# Tech Context\n\n"
                "## Stack\n"
                "- Markdown only.\n\n"
                "## Core commands\n"
                "- `workflow status`\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing the Python CLI runtime signal", result.stdout)

    def test_workflow_doctor_reports_misleading_hermes_claim_in_memory_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "misleading-memory-repo")
            project_path = repo / ".specify/memory/project.md"
            project_text = project_path.read_text(encoding="utf-8") + "\nHermes is implemented.\n"
            write(project_path, project_text)
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("claims Hermes is implemented", result.stdout)

    def test_workflow_doctor_reports_missing_active_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-active-repo")
            (repo / ".specify/state/active.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- continuity-state health: fail", result.stdout)
            self.assertIn("Continuity-state error: Missing continuity-state file `.specify/state/active.md`.", result.stdout)

    def test_workflow_doctor_reports_empty_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "empty-handoff-repo")
            write(repo / ".specify/state/handoff.md", "# Handoff\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Continuity-state error: `.specify/state/handoff.md` is missing a next-step handoff signal.", result.stdout)

    def test_workflow_doctor_reports_missing_progress_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-progress-repo")
            (repo / ".specify/state/progress.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Continuity-state error: Missing continuity-state file `.specify/state/progress.md`.", result.stdout)

    def test_workflow_doctor_reports_empty_session_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "empty-session-repo")
            write(repo / ".specify/state/session.log.md", "# Session Log\n\n## Entries\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Continuity-state error: `.specify/state/session.log.md` is missing session entries.", result.stdout)

    def test_workflow_doctor_reports_missing_migration_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-migration-repo")
            (repo / ".specify/state/migration.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Continuity-state error: Missing continuity-state file `.specify/state/migration.md`.", result.stdout)

    def test_workflow_doctor_reports_invalid_active_pointer_without_no_active_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "bad-active-pointer-repo")
            write(
                repo / ".specify/state/active.md",
                "# Active State\n\n"
                "## Current task\n"
                "Keep going.\n\n"
                "## Active spec/task pointer\n"
                "Follow the thing.\n\n"
                "## Current focus\n"
                "- Keep moving.\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not declare a valid spec/task pointer or an explicit no-active-spec note", result.stdout)

    def test_workflow_doctor_reports_migration_state_inconsistent_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "migration-mismatch-repo")
            write(
                repo / ".specify/state/migration.md",
                "# Migration State\n\n"
                "## Current state\n"
                "- Status: coexist\n"
                "- Phase: milestone-999-imaginary\n"
                "- Legacy preserved: yes\n"
                "- Canonical continuity: `.specify/*`\n"
                "- Legacy continuity: `.ai/*` preserved during coexistence\n",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match manifest migration status", result.stdout)
            self.assertIn("does not match manifest migration phase", result.stdout)
            self.assertIn("does not match manifest value `no`", result.stdout)

    def test_workflow_doctor_reports_misleading_hermes_claim_in_migration_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "misleading-migration-repo")
            migration_path = repo / ".specify/state/migration.md"
            migration_text = migration_path.read_text(encoding="utf-8") + "\n- Hermes is implemented.\n"
            write(migration_path, migration_text)
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("claims Hermes is implemented", result.stdout)

    def test_roots_command_reads_repo_owned_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root1 = Path(temp_dir) / "root1"
            root2 = Path(temp_dir) / "root2"
            root1.mkdir()
            root2.mkdir()
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root1, root2])
            result = self.run_cli(ROOT, "roots", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Config path: {config.resolve()}", result.stdout)
            self.assertIn("Status: pass", result.stdout)
            self.assertIn("Summary: All 2 configured roots are usable.", result.stdout)
            self.assertIn(f"ok       {root1.resolve()}", result.stdout)
            self.assertIn(f"ok       {root2.resolve()}", result.stdout)

    def test_roots_command_fails_for_missing_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing-roots.json"
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(missing)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Status: fail", result.stdout)
            self.assertIn("Missing roots config", result.stdout)
            self.assertTrue(result.stdout.strip().endswith("FAIL"))

    def test_roots_command_detects_invalid_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "roots.json"
            write(config, "{ invalid json\n")
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Status: fail", result.stdout)
            self.assertIn("Invalid roots config", result.stdout)
            self.assertTrue(result.stdout.strip().endswith("FAIL"))

    def test_roots_validate_fails_when_configured_root_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_root = Path(temp_dir) / "missing-root"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [missing_root])
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Status: warning", result.stdout)
            self.assertIn(f"missing  {missing_root.resolve()}", result.stdout)
            self.assertTrue(result.stdout.strip().endswith("FAIL"))

    def test_roots_validate_detects_duplicate_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root, root])
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Status: fail", result.stdout)
            self.assertIn("duplicate workspace root", result.stdout)

    def test_roots_validate_detects_non_directory_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_root = Path(temp_dir) / "not-a-dir"
            write(file_root, "hello\n")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [file_root])
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Status: warning", result.stdout)
            self.assertIn(f"not-dir  {file_root.resolve()}", result.stdout)
            self.assertIn("not a directory", result.stdout)

    def test_roots_validate_detects_missing_roots_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "roots.json"
            write(config, json.dumps({"schema_version": "1.0.0"}, indent=2) + "\n")
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required `roots` key", result.stdout)

    def test_roots_validate_detects_wrong_roots_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "roots.json"
            write(config, json.dumps({"schema_version": "1.0.0", "roots": "nope"}, indent=2) + "\n")
            result = self.run_cli(ROOT, "roots", "--validate", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("`roots` must be a JSON array", result.stdout)

    def test_workflow_status_includes_roots_health_for_valid_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "status-repo")
            root = Path(temp_dir) / "workspace-root"
            root.mkdir()
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])
            result = self.run_cli(repo, "status", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Roots health", result.stdout)
            self.assertIn("- Status: pass", result.stdout)
            self.assertIn(f"- Config path: `{config.resolve()}`", result.stdout)
            self.assertIn("All 1 configured root is usable.", result.stdout)

    def test_health_overview_reports_warning_when_roots_need_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "overview-roots-warning-repo")
            missing_root = Path(temp_dir) / "missing-root"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [missing_root])
            result = self.run_cli(repo, "status", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Health overview", result.stdout)
            self.assertIn("- Overall health: warning", result.stdout)
            self.assertIn("roots=warning", result.stdout)
            self.assertIn("- Default-root operations safe: no", result.stdout)
            self.assertIn("- Pre-Hermes readiness: needs-review", result.stdout)

    def test_workflow_status_surfaces_missing_roots_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "status-missing-roots-repo")
            missing = Path(temp_dir) / "missing-roots.json"
            result = self.run_cli(repo, "status", env={"WORKFLOW_ROOTS_FILE": str(missing)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Roots health", result.stdout)
            self.assertIn("- Status: fail", result.stdout)
            self.assertIn("Missing roots config", result.stdout)

    def test_workflow_status_surfaces_invalid_roots_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "status-invalid-roots-repo")
            config = Path(temp_dir) / "roots.json"
            write(config, json.dumps({"schema_version": "0.9.0", "roots": []}, indent=2) + "\n")
            result = self.run_cli(repo, "status", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Roots health", result.stdout)
            self.assertIn("- Status: fail", result.stdout)
            self.assertIn("expected schema_version", result.stdout)

    def test_workflow_doctor_reports_roots_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-roots-warning-repo")
            missing_root = Path(temp_dir) / "missing-root"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [missing_root])
            result = self.run_cli(repo, "doctor", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- roots health: warning", result.stdout)
            self.assertIn("Roots warning: Configured root is missing on disk", result.stdout)

    def test_workflow_doctor_reports_roots_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-roots-fail-repo")
            config = Path(temp_dir) / "roots.json"
            write(config, "{ invalid json\n")
            result = self.run_cli(repo, "doctor", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- roots health: fail", result.stdout)
            self.assertIn("Roots error: Invalid roots config", result.stdout)

    def test_workflow_doctor_write_report_includes_roots_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-report-repo")
            missing_root = Path(temp_dir) / "missing-root"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [missing_root])
            result = self.run_cli(repo, "doctor", "--write-report", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            drift = (repo / ".specify/state/drift.md").read_text(encoding="utf-8")
            self.assertIn("## Roots health", drift)
            self.assertIn("- Status: warning", drift)
            self.assertIn(f"- Config path: `{config.resolve()}`", drift)
            self.assertIn("- Default root-based operations safe: no", drift)
            self.assertIn("Configured root is missing on disk", drift)

    def test_workflow_status_surfaces_missing_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-lock-repo")
            (repo / ".workflow/mirror-lock.json").unlink()
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Mirror-lock/shim health", result.stdout)
            self.assertIn("Missing mirror lockfile", result.stdout)

    def test_workflow_doctor_reports_invalid_lockfile_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "invalid-lock-repo")
            write(repo / ".workflow/mirror-lock.json", "{ invalid json\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- mirror-lock/shim health: fail", result.stdout)
            self.assertIn("Mirror-lock/shim error: Invalid mirror lockfile", result.stdout)

    def test_workflow_status_surfaces_agents_checksum_mismatch_as_sync_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "agents-mismatch-repo")
            agents = repo / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\nAdditional change.\n", encoding="utf-8")
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Mirror-lock/shim health", result.stdout)
            self.assertIn("workflow sync` is needed", result.stdout)
            self.assertIn("- Sync needed: yes", result.stdout)
            self.assertIn("Health overview", result.stdout)
            self.assertIn("- Overall health: warning", result.stdout)
            self.assertIn("mirror-lock/shim=warning", result.stdout)
            self.assertIn("- Pre-Hermes readiness: needs-review", result.stdout)

    def test_workflow_doctor_surfaces_agents_checksum_mismatch_as_sync_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-agents-mismatch-repo")
            agents = repo / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\nAdditional change.\n", encoding="utf-8")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- health overview: warning", result.stdout)
            self.assertIn("- sync needed: yes", result.stdout)
            self.assertIn("- mirror-lock/shim health: warning", result.stdout)
            self.assertIn("- workflow sync needed: yes", result.stdout)
            self.assertIn(
                "Mirror-lock/shim warning: `AGENTS.md` has changed since the last `workflow sync`; mirror lock is stale.",
                result.stdout,
            )
            self.assertIn("Mirror-lock/shim warning: `CLAUDE.md` is stale relative to `AGENTS.md`", result.stdout)
            self.assertIn("Mirror-lock/shim warning: `GEMINI.md` is stale relative to `AGENTS.md`", result.stdout)

    def test_workflow_doctor_returns_to_pass_after_syncing_agents_checksum_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "doctor-sync-recovery-repo")
            agents = repo / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\nAdditional change.\n", encoding="utf-8")

            drift_result = self.run_cli(repo, "doctor")
            self.assertNotEqual(drift_result.returncode, 0)
            self.assertIn("- mirror-lock/shim health: warning", drift_result.stdout)
            self.assertIn("- workflow sync needed: yes", drift_result.stdout)

            sync_result = self.run_cli(repo, "sync")
            self.assertEqual(sync_result.returncode, 0, sync_result.stderr)
            self.assertIn("- updated CLAUDE.md", sync_result.stdout)
            self.assertIn("- updated GEMINI.md", sync_result.stdout)
            self.assertIn("- updated .workflow/mirror-lock.json", sync_result.stdout)

            healthy_result = self.run_cli(repo, "doctor")
            self.assertEqual(healthy_result.returncode, 0, healthy_result.stdout)
            self.assertIn("- health overview: pass", healthy_result.stdout)
            self.assertIn("- mirror-lock/shim health: pass", healthy_result.stdout)
            self.assertIn("- workflow sync needed: no", healthy_result.stdout)
            self.assertTrue(healthy_result.stdout.rstrip().endswith("PASS"))

    def test_workflow_doctor_reports_missing_generated_shim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-shim-repo")
            (repo / "CLAUDE.md").unlink()
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mirror-lock/shim error: Missing generated shim `CLAUDE.md`.", result.stdout)

    def test_workflow_status_surfaces_missing_generated_gemini_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-gemini-adapter-repo")
            (repo / ".gemini/agents/research-orchestrator.md").unlink()
            result = self.run_cli(repo, "status")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Mirror-lock/shim health", result.stdout)
            self.assertIn(
                "Missing generated Gemini adapter `.gemini/agents/research-orchestrator.md`.",
                result.stdout,
            )
            self.assertIn("- Overall health: fail", result.stdout)

    def test_workflow_doctor_reports_generated_gemini_adapter_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "drifted-gemini-adapter-repo")
            adapter = repo / ".gemini/agents/research-orchestrator.md"
            adapter.write_text(
                adapter.read_text(encoding="utf-8").replace(
                    "Read and follow that canonical capability file",
                    "Ignore the canonical capability file",
                ),
                encoding="utf-8",
            )
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Mirror-lock/shim error: `.gemini/agents/research-orchestrator.md` is drifting from the generated Gemini adapter render.",
                result.stdout,
            )

    def test_workflow_doctor_reports_shim_not_managed_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "plain-shim-repo")
            write(repo / "CLAUDE.md", "# manual file\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mirror-lock/shim error: `CLAUDE.md` is not in the managed shim format.", result.stdout)

    def test_workflow_doctor_reports_managed_shim_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "drifted-shim-repo")
            claude = repo / "CLAUDE.md"
            text = claude.read_text(encoding="utf-8").replace("Describe what this project is and why it exists.", "Manual drift.")
            claude.write_text(text, encoding="utf-8")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mirror-lock/shim error: `CLAUDE.md` is drifting from the current `AGENTS.md` render.", result.stdout)

    def test_workflow_doctor_reports_missing_lock_entry_for_shim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "missing-lock-entry-repo")
            lock_path = repo / ".workflow/mirror-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            del lock["shims"]["CLAUDE.md"]
            write(lock_path, json.dumps(lock, indent=2) + "\n")
            result = self.run_cli(repo, "doctor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- mirror-lock/shim health: warning", result.stdout)
            self.assertIn("missing an entry for `CLAUDE.md`", result.stdout)

    def test_workflow_doctor_write_report_includes_manifest_and_mirror_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "artifact-report-repo")
            agents = repo / "AGENTS.md"
            agents.write_text(agents.read_text(encoding="utf-8") + "\nAdditional change.\n", encoding="utf-8")
            result = self.run_cli(repo, "doctor", "--write-report")
            self.assertNotEqual(result.returncode, 0)
            drift = (repo / ".specify/state/drift.md").read_text(encoding="utf-8")
            self.assertIn("## Manifest health", drift)
            self.assertIn("Manifest matches the current v2 repo model.", drift)
            self.assertIn("## Mirror-lock/shim health", drift)
            self.assertIn("- Status: warning", drift)
            self.assertIn("- Sync needed: yes", drift)
            self.assertIn("workflow sync", drift)

    def test_workflow_doctor_write_report_includes_memory_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "memory-report-repo")
            write(repo / ".specify/memory/project.md", "")
            result = self.run_cli(repo, "doctor", "--write-report")
            self.assertNotEqual(result.returncode, 0)
            drift = (repo / ".specify/state/drift.md").read_text(encoding="utf-8")
            self.assertIn("## Memory health", drift)
            self.assertIn("- Status: fail", drift)
            self.assertIn("Memory file `.specify/memory/project.md` is empty.", drift)

    def test_workflow_doctor_write_report_includes_continuity_state_health(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "continuity-report-repo")
            write(repo / ".specify/state/handoff.md", "# Handoff\n")
            result = self.run_cli(repo, "doctor", "--write-report")
            self.assertNotEqual(result.returncode, 0)
            drift = (repo / ".specify/state/drift.md").read_text(encoding="utf-8")
            self.assertIn("## Continuity-state health", drift)
            self.assertIn("- Status: fail", drift)
            self.assertIn("missing a next-step handoff signal", drift)

    def test_workflow_doctor_write_report_includes_command_help_docs_consistency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "command-docs-report-repo")
            result = self.run_cli(repo, "doctor", "--write-report")
            self.assertEqual(result.returncode, 0, result.stdout)
            drift = (repo / ".specify/state/drift.md").read_text(encoding="utf-8")
            self.assertIn("## Command/help/docs consistency", drift)
            self.assertIn("- Status: pass", drift)
            self.assertIn(f"- Path: `{ROOT}`", drift)
            self.assertIn(
                "- Subsystems: command/help/docs=pass, manifest=pass, mirror-lock/shim=pass, memory=pass, continuity-state=pass, roots=pass, role-contract=pass",
                drift,
            )

    def test_workflow_doctor_write_report_includes_health_overview_and_preserves_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "overview-report-repo")
            missing_root = Path(temp_dir) / "missing-root"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [missing_root])
            result = self.run_cli(repo, "doctor", "--write-report", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("- health overview: warning", result.stdout)
            self.assertIn("- pre-hermes readiness: needs-review", result.stdout)
            drift = (repo / ".specify/state/drift.md").read_text(encoding="utf-8")
            self.assertIn("## Health overview", drift)
            self.assertIn("- Overall health: warning", drift)
            self.assertIn("- Default-root operations safe: no", drift)
            self.assertIn("- Pre-Hermes readiness: needs-review", drift)
            self.assertIn("## Command/help/docs consistency", drift)
            self.assertIn("## Role-contract health", drift)
            self.assertIn("## Manifest health", drift)
            self.assertIn("## Mirror-lock/shim health", drift)
            self.assertIn("## Memory health", drift)
            self.assertIn("## Continuity-state health", drift)
            self.assertIn("## Roots health", drift)

    def test_workflow_list_uses_configured_roots_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root1 = Path(temp_dir) / "root1"
            root2 = Path(temp_dir) / "root2"
            root1.mkdir()
            root2.mkdir()
            self.create_v2_repo(root1, "v2-repo")
            build_legacy_repo(root2, "legacy-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root1, root2])
            result = self.run_cli(ROOT, "list", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"== {root1.resolve()}", result.stdout)
            self.assertIn(f"== {root2.resolve()}", result.stdout)
            self.assertIn("v2         v2-repo", result.stdout)
            self.assertIn("legacy     legacy-repo", result.stdout)

    def test_workflow_hermes_inventory_requires_explicit_dry_run(self) -> None:
        result = self.run_cli(ROOT, "hermes", "inventory")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("dry-run only", result.stderr)

    def test_workflow_hermes_inventory_classifies_repo_states_and_missing_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root1 = Path(temp_dir) / "root1"
            root2 = Path(temp_dir) / "root2"
            missing_root = Path(temp_dir) / "missing-root"
            root1.mkdir()
            root2.mkdir()
            self.create_v2_repo(root1, "v2-repo")
            build_legacy_repo(root1, "legacy-repo")
            build_mixed_repo(root1, "mixed-repo")
            build_unmanaged_repo(root1, "unmanaged-repo")
            build_error_repo(root1, "error-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root1, missing_root, root2])

            result = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertIn("workflow hermes inventory :: mode=dry-run", result.stdout)
            self.assertIn(f"Roots source: {config.resolve()}", result.stdout)
            self.assertIn("Read-only: yes", result.stdout)
            self.assertIn("Repo classifications: v2=1, legacy=1, mixed=1, unmanaged=1, error=1", result.stdout)
            self.assertIn(f"== {root1.resolve()}", result.stdout)
            self.assertIn("v2         v2-repo", result.stdout)
            self.assertIn("legacy     legacy-repo", result.stdout)
            self.assertIn("mixed      mixed-repo", result.stdout)
            self.assertIn("unmanaged  unmanaged-repo", result.stdout)
            self.assertIn("error      error-repo :: Invalid `.workflow/workflow.json`", result.stdout)
            self.assertIn(f"== {missing_root.resolve()}", result.stdout)
            self.assertIn("missing-root", result.stdout)
            self.assertIn("Configured root is missing on disk", result.stdout)
            self.assertIn(f"== {root2.resolve()}", result.stdout)
            self.assertIn("(no project candidates)", result.stdout)

    def test_workflow_hermes_inventory_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root1 = Path(temp_dir) / "root1"
            root2 = Path(temp_dir) / "root2"
            root1.mkdir()
            root2.mkdir()
            repo_b = self.create_v2_repo(root1, "b-repo")
            repo_a = build_legacy_repo(root1, "a-repo")
            repo_c = build_unmanaged_repo(root2, "c-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root2, root1])
            before = {
                "a-repo": self.snapshot_tree(repo_a),
                "b-repo": self.snapshot_tree(repo_b),
                "c-repo": self.snapshot_tree(repo_c),
            }

            first = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            second = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stderr, "")
            self.assertEqual(second.stderr, "")
            self.assertEqual(first.stdout, second.stdout)
            self.assertLess(first.stdout.find(f"== {root2.resolve()}"), first.stdout.find(f"== {root1.resolve()}"))
            self.assertLess(first.stdout.find("legacy     a-repo"), first.stdout.find("v2         b-repo"))

            after = {
                "a-repo": self.snapshot_tree(repo_a),
                "b-repo": self.snapshot_tree(repo_b),
                "c-repo": self.snapshot_tree(repo_c),
            }
            self.assertEqual(before, after)

    def test_workflow_hermes_inventory_json_requires_explicit_dry_run(self) -> None:
        result = self.run_cli(ROOT, "hermes", "inventory", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("dry-run only", result.stderr)

    def test_workflow_hermes_inventory_json_is_valid_and_reuses_roots_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_b = Path(temp_dir) / "b-root"
            root_a = Path(temp_dir) / "a-root"
            missing_root = Path(temp_dir) / "c-missing-root"
            invalid_root = Path(temp_dir) / "d-invalid-root.txt"
            root_b.mkdir()
            root_a.mkdir()
            invalid_root.write_text("not-a-directory\n", encoding="utf-8")
            self.create_v2_repo(root_b, "b-v2-repo")
            build_error_repo(root_b, "a-error-repo")
            build_unmanaged_repo(root_a, "e-unmanaged-repo")
            build_mixed_repo(root_a, "c-mixed-repo")
            build_legacy_repo(root_a, "b-legacy-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root_b, invalid_root, missing_root, root_a])

            result = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            payload = verify_hermes_inventory_json_stdout(
                result.stdout,
                expected_roots_config_path=config,
            )

            self.assertEqual(payload["classification_counts"], {
                "v2": 1,
                "legacy": 1,
                "mixed": 1,
                "unmanaged": 1,
                "error": 1,
            })
            root_classifications = {item["path"]: item["classification"] for item in payload["roots"]}
            self.assertEqual(root_classifications[str(root_a.resolve())], "configured-root")
            self.assertEqual(root_classifications[str(root_b.resolve())], "configured-root")
            self.assertEqual(root_classifications[str(missing_root.resolve())], "missing-root")
            self.assertEqual(root_classifications[str(invalid_root.resolve())], "invalid-root")
            self.assertTrue(any("missing on disk" in warning for warning in payload["warnings"]))
            self.assertTrue(any("not a directory" in warning for warning in payload["warnings"]))
            self.assertEqual(payload["errors"], [])

    def test_workflow_hermes_inventory_json_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root2 = Path(temp_dir) / "z-root"
            root1 = Path(temp_dir) / "a-root"
            missing_root = Path(temp_dir) / "m-missing-root"
            root2.mkdir()
            root1.mkdir()
            repo_b = self.create_v2_repo(root2, "b-v2-repo")
            repo_a = build_legacy_repo(root2, "a-legacy-repo")
            repo_c = build_unmanaged_repo(root1, "c-unmanaged-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root2, missing_root, root1])
            before = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }

            first = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            second = self.run_cli(
                ROOT,
                "hermes",
                "inventory",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stderr, "")
            self.assertEqual(second.stderr, "")
            self.assertEqual(first.stdout, second.stdout)
            payload = verify_hermes_inventory_json_stdout(first.stdout, expected_roots_config_path=config)
            self.assertEqual(
                [item["path"] for item in payload["roots"]],
                sorted(item["path"] for item in payload["roots"]),
            )
            configured_root = next(item for item in payload["roots"] if item["path"] == str(root2.resolve()))
            self.assertEqual(
                [project["name"] for project in configured_root["projects"]],
                ["a-legacy-repo", "b-v2-repo"],
            )

            after = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }
            self.assertEqual(before, after)

    def test_hermes_preflight_json_invariants_cover_valid_payload(self) -> None:
        payload = verify_hermes_preflight_json_payload(build_valid_hermes_preflight_payload())
        self.assertEqual(set(payload.keys()), set(EXPECTED_HERMES_PREFLIGHT_JSON_KEYS))
        self.assertEqual(set(payload["roots"][0].keys()), set(EXPECTED_HERMES_PREFLIGHT_ROOT_KEYS))
        self.assertEqual(
            set(payload["roots"][0]["projects"][0].keys()),
            set(EXPECTED_HERMES_PREFLIGHT_PROJECT_KEYS),
        )

    def test_hermes_analysis_json_invariants_cover_valid_payload(self) -> None:
        payload = verify_hermes_analysis_json_payload(build_valid_hermes_analysis_payload())
        self.assertEqual(set(payload.keys()), set(EXPECTED_HERMES_ANALYSIS_JSON_KEYS))
        self.assertEqual(set(payload["roots"][0].keys()), set(EXPECTED_HERMES_ANALYSIS_ROOT_KEYS))
        self.assertEqual(
            set(payload["roots"][0]["analyses"][0].keys()),
            set(EXPECTED_HERMES_ANALYSIS_PROJECT_KEYS),
        )

    def test_hermes_qwen_preview_json_invariants_cover_valid_payload(self) -> None:
        payload = verify_hermes_qwen_preview_json_payload(build_valid_hermes_qwen_preview_payload())
        self.assertEqual(set(payload.keys()), set(EXPECTED_HERMES_QWEN_PREVIEW_JSON_KEYS))
        self.assertEqual(set(payload["request_preview"].keys()), set(EXPECTED_HERMES_QWEN_PREVIEW_REQUEST_KEYS))
        self.assertEqual(set(payload["prompt_preview"].keys()), set(EXPECTED_HERMES_QWEN_PREVIEW_PROMPT_KEYS))

    def test_workflow_hermes_preflight_requires_explicit_dry_run(self) -> None:
        result = self.run_cli(ROOT, "hermes", "preflight")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("dry-run only", result.stderr)

    def test_workflow_hermes_preflight_text_and_json_are_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            self.create_v2_repo(root, "v2-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            text_result = self.run_cli(
                ROOT,
                "hermes",
                "preflight",
                "--dry-run",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(text_result.returncode, 0, text_result.stderr)
            self.assertEqual(text_result.stderr, "")
            self.assertIn("workflow hermes preflight :: mode=dry-run", text_result.stdout)
            self.assertIn("Read-only: yes", text_result.stdout)
            self.assertIn("target repo file body reads", text_result.stdout)

            json_result = self.run_cli(
                ROOT,
                "hermes",
                "preflight",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(json_result.returncode, 0, json_result.stderr)
            payload = verify_hermes_preflight_json_stdout(
                json_result.stdout,
                expected_roots_config_path=config,
            )
            self.assertEqual(payload["command"], "hermes_preflight")
            self.assertFalse(payload["target_repos_modified"])
            self.assertFalse(payload["target_repo_file_bodies_read"])

    def test_workflow_hermes_preflight_git_clean_dirty_and_not_git_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            clean_repo = self.create_v2_repo(root, "clean-v2-repo")
            dirty_repo = self.create_v2_repo(root, "dirty-v2-repo")
            not_git_repo = self.create_v2_repo(root, "not-git-v2-repo")
            self.init_clean_git_repo(clean_repo)
            self.init_clean_git_repo(dirty_repo)
            write(dirty_repo / "dirty.txt", "changed\n")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            result = self.run_cli(
                ROOT,
                "hermes",
                "preflight",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = verify_hermes_preflight_json_stdout(result.stdout, expected_roots_config_path=config)
            projects = {
                project["name"]: project
                for root_payload in payload["roots"]
                for project in root_payload["projects"]
            }
            self.assertEqual(projects["clean-v2-repo"]["git"]["status"], "clean")
            self.assertEqual(projects["clean-v2-repo"]["automation_readiness"], "ready")
            self.assertFalse(projects["clean-v2-repo"]["git"]["blocks_future_apply"])
            self.assertEqual(projects["dirty-v2-repo"]["git"]["status"], "dirty")
            self.assertEqual(projects["dirty-v2-repo"]["automation_readiness"], "blocked")
            self.assertTrue(projects["dirty-v2-repo"]["git"]["blocks_future_apply"])
            self.assertEqual(projects["not-git-v2-repo"]["git"]["status"], "not-git")
            self.assertEqual(projects["not-git-v2-repo"]["automation_readiness"], "blocked")
            self.assertTrue(projects["not-git-v2-repo"]["git"]["blocks_future_apply"])

    def test_workflow_hermes_preflight_classifies_fixture_mix_and_nested_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            missing_root = Path(temp_dir) / "missing-root"
            invalid_root = Path(temp_dir) / "invalid.txt"
            root.mkdir()
            invalid_root.write_text("not a directory\n", encoding="utf-8")
            v2_repo = self.create_v2_repo(root, "v2-repo")
            nested = self.create_v2_repo(v2_repo, "nested-v2-repo")
            build_legacy_repo(root, "legacy-repo")
            build_mixed_repo(root, "mixed-repo")
            build_unmanaged_repo(root, "unmanaged-repo")
            build_error_repo(root, "error-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root, missing_root, invalid_root])

            result = self.run_cli(
                ROOT,
                "hermes",
                "preflight",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = verify_hermes_preflight_json_stdout(result.stdout, expected_roots_config_path=config)
            root_classifications = {item["path"]: item["classification"] for item in payload["roots"]}
            self.assertEqual(root_classifications[str(root.resolve())], "configured-root")
            self.assertEqual(root_classifications[str(missing_root.resolve())], "missing-root")
            self.assertEqual(root_classifications[str(invalid_root.resolve())], "invalid-root")
            projects = {
                project["name"]: project
                for root_payload in payload["roots"]
                for project in root_payload["projects"]
            }
            self.assertEqual(projects["v2-repo"]["scaffold_classification"], "v2")
            self.assertIn("nested-workflows", projects["v2-repo"]["detected_flags"])
            self.assertIn("Nested workflow-managed", " ".join(projects["v2-repo"]["warnings"]))
            self.assertEqual(projects["legacy-repo"]["scaffold_classification"], "legacy")
            self.assertEqual(projects["mixed-repo"]["scaffold_classification"], "mixed")
            self.assertEqual(projects["unmanaged-repo"]["scaffold_classification"], "unmanaged")
            self.assertEqual(projects["error-repo"]["scaffold_classification"], "error")
            self.assertEqual(projects["error-repo"]["automation_readiness"], "blocked")
            self.assertTrue(nested.exists())

    def test_workflow_hermes_preflight_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root2 = Path(temp_dir) / "z-root"
            root1 = Path(temp_dir) / "a-root"
            root2.mkdir()
            root1.mkdir()
            repo_b = self.create_v2_repo(root2, "b-v2-repo")
            repo_a = build_legacy_repo(root2, "a-legacy-repo")
            repo_c = build_unmanaged_repo(root1, "c-unmanaged-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root2, root1])
            before = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }

            first = self.run_cli(
                ROOT,
                "hermes",
                "preflight",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            second = self.run_cli(
                ROOT,
                "hermes",
                "preflight",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            payload = verify_hermes_preflight_json_stdout(first.stdout, expected_roots_config_path=config)
            self.assertEqual([item["path"] for item in payload["roots"]], sorted(item["path"] for item in payload["roots"]))
            after = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }
            self.assertEqual(before, after)

    def test_workflow_hermes_analyze_requires_explicit_dry_run(self) -> None:
        result = self.run_cli(ROOT, "hermes", "analyze")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("dry-run only", result.stderr)

    def test_workflow_hermes_analyze_text_and_json_are_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = self.create_v2_repo(root, "v2-repo")
            self.init_clean_git_repo(repo)
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            text_result = self.run_cli(
                ROOT,
                "hermes",
                "analyze",
                "--dry-run",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(text_result.returncode, 0, text_result.stderr)
            self.assertEqual(text_result.stderr, "")
            self.assertIn("workflow hermes analyze :: mode=dry-run", text_result.stdout)
            self.assertIn("Input: deterministic in-memory preflight report", text_result.stdout)
            self.assertIn("no Qwen", text_result.stdout)
            self.assertIn("no connectivity probe", text_result.stdout)

            json_result = self.run_cli(
                ROOT,
                "hermes",
                "analyze",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(json_result.returncode, 0, json_result.stderr)
            payload = verify_hermes_analysis_json_stdout(
                json_result.stdout,
                expected_roots_config_path=config,
            )
            self.assertEqual(payload["command"], "hermes_analysis")
            self.assertFalse(payload["qwen_dashscope_enabled"])
            self.assertFalse(payload["live_response_parsing_enabled"])
            self.assertEqual(payload["analysis_counts"]["low"], 1)

    def test_workflow_hermes_analyze_dirty_and_not_git_do_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            clean_repo = self.create_v2_repo(root, "clean-v2-repo")
            dirty_repo = self.create_v2_repo(root, "dirty-v2-repo")
            not_git_repo = self.create_v2_repo(root, "not-git-v2-repo")
            self.init_clean_git_repo(clean_repo)
            self.init_clean_git_repo(dirty_repo)
            write(dirty_repo / "dirty.txt", "changed\n")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            result = self.run_cli(
                ROOT,
                "hermes",
                "analyze",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = verify_hermes_analysis_json_stdout(result.stdout, expected_roots_config_path=config)
            analyses = {
                analysis["name"]: analysis
                for root_payload in payload["roots"]
                for analysis in root_payload["analyses"]
            }
            self.assertEqual(analyses["clean-v2-repo"]["git_status"], "clean")
            self.assertFalse(analyses["clean-v2-repo"]["required_human_review"])
            self.assertEqual(analyses["dirty-v2-repo"]["git_status"], "dirty")
            self.assertTrue(analyses["dirty-v2-repo"]["required_human_review"])
            self.assertEqual(analyses["not-git-v2-repo"]["git_status"], "not-git")
            self.assertTrue(analyses["not-git-v2-repo"]["required_human_review"])
            self.assertEqual(payload["analysis_counts"]["blocked"], 2)

    def test_workflow_hermes_analyze_roots_config_failure_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "missing-roots.json"
            result = self.run_cli(
                ROOT,
                "hermes",
                "analyze",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertNotEqual(result.returncode, 0)
            payload = verify_hermes_analysis_json_stdout(result.stdout, expected_roots_config_path=config)
            self.assertTrue(payload["errors"])
            self.assertEqual(payload["roots"], [])

    def test_workflow_hermes_analyze_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root2 = Path(temp_dir) / "z-root"
            root1 = Path(temp_dir) / "a-root"
            root2.mkdir()
            root1.mkdir()
            repo_b = self.create_v2_repo(root2, "b-v2-repo")
            repo_a = build_legacy_repo(root2, "a-legacy-repo")
            repo_c = build_unmanaged_repo(root1, "c-unmanaged-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root2, root1])
            before = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }

            first = self.run_cli(
                ROOT,
                "hermes",
                "analyze",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            second = self.run_cli(
                ROOT,
                "hermes",
                "analyze",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            payload = verify_hermes_analysis_json_stdout(first.stdout, expected_roots_config_path=config)
            self.assertEqual([item["path"] for item in payload["roots"]], sorted(item["path"] for item in payload["roots"]))
            configured_root = next(item for item in payload["roots"] if item["path"] == str(root2.resolve()))
            self.assertEqual(
                [analysis["name"] for analysis in configured_root["analyses"]],
                ["a-legacy-repo", "b-v2-repo"],
            )
            after = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }
            self.assertEqual(before, after)

    def test_workflow_hermes_analyze_safety_flags_false_and_no_dashscope_helper_coupling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            self.create_v2_repo(root, "v2-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            original_probe = workflow_cli.probe_dashscope_connectivity
            original_request = workflow_cli.build_hermes_preflight_report
            calls = {"probe": 0, "preflight": 0}

            def fail_probe(*args: object, **kwargs: object) -> object:
                calls["probe"] += 1
                raise AssertionError("analyze must not call the DashScope connectivity probe")

            def counted_preflight() -> workflow_cli.HermesPreflightReport:
                calls["preflight"] += 1
                return original_request()

            workflow_cli.probe_dashscope_connectivity = fail_probe
            workflow_cli.build_hermes_preflight_report = counted_preflight
            cwd = Path.cwd()
            old_roots_file = os.environ.get("WORKFLOW_ROOTS_FILE")
            os.environ["WORKFLOW_ROOTS_FILE"] = str(config)
            try:
                os.chdir(ROOT)
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    exit_code = workflow_cli.hermes_analysis_command(dry_run=True, as_json=True)
            finally:
                workflow_cli.probe_dashscope_connectivity = original_probe
                workflow_cli.build_hermes_preflight_report = original_request
                if old_roots_file is None:
                    os.environ.pop("WORKFLOW_ROOTS_FILE", None)
                else:
                    os.environ["WORKFLOW_ROOTS_FILE"] = old_roots_file
                os.chdir(cwd)

            self.assertEqual(exit_code, 0)
            self.assertEqual(calls["probe"], 0)
            self.assertEqual(calls["preflight"], 1)
            payload = verify_hermes_analysis_json_stdout(stdout.getvalue(), expected_roots_config_path=config)
            for key in (
                "target_repos_modified",
                "qwen_dashscope_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "report_writing_enabled",
                "target_repo_file_bodies_read",
                "live_response_parsing_enabled",
            ):
                self.assertFalse(payload[key], key)
            combined_evidence = "\n".join(
                evidence
                for root_payload in payload["roots"]
                for analysis in root_payload["analyses"]
                for evidence in analysis["deterministic_evidence"]
            ).lower()
            self.assertNotIn("prompt", combined_evidence)
            self.assertNotIn("request_shape", combined_evidence)
            self.assertNotIn("response", combined_evidence)

    def test_workflow_hermes_analyze_source_stays_decoupled_from_qwen_payload_helpers(self) -> None:
        source = "\n".join(
            inspect.getsource(item)
            for item in (
                workflow_cli.hermes_analysis_command,
                workflow_cli.build_hermes_analysis_report,
                workflow_cli.hermes_analysis_payload,
                workflow_cli.render_hermes_analysis_text,
                workflow_cli._build_analysis_project,
            )
        )
        forbidden_helper_names = (
            "build_hermes_qwen_offline_request_shape",
            "build_hermes_qwen_offline_prompt_template",
            "build_hermes_qwen_offline_prompt_preview",
            "build_hermes_qwen_offline_response_shape",
            "build_hermes_qwen_offline_response_consumer_policy",
            "build_hermes_qwen_offline_consumer_decision_policy",
            "build_hermes_qwen_offline_escalation_policy",
            "parse_hermes_qwen_offline_simulated_response",
            "probe_dashscope_connectivity",
        )
        for helper_name in forbidden_helper_names:
            self.assertNotIn(helper_name, source)

    def test_workflow_hermes_qwen_preview_requires_explicit_dry_run(self) -> None:
        result = self.run_cli(ROOT, "hermes", "qwen-preview")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("dry-run only", result.stderr)

    def test_workflow_hermes_qwen_preview_text_and_json_are_parseable_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = self.create_v2_repo(root, "v2-repo")
            self.init_clean_git_repo(repo)
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            text_result = self.run_cli(
                ROOT,
                "hermes",
                "qwen-preview",
                "--dry-run",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(text_result.returncode, 0, text_result.stderr)
            self.assertEqual(text_result.stderr, "")
            self.assertIn("workflow hermes qwen-preview :: mode=dry-run", text_result.stdout)
            self.assertIn("Input: bounded deterministic Hermes analysis summary", text_result.stdout)
            self.assertIn("no network", text_result.stdout)
            self.assertIn("root paths, project paths", text_result.stdout)

            json_result = self.run_cli(
                ROOT,
                "hermes",
                "qwen-preview",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(json_result.returncode, 0, json_result.stderr)
            payload = verify_hermes_qwen_preview_json_stdout(json_result.stdout)
            self.assertEqual(payload["command"], "hermes_qwen_preview")
            self.assertEqual(payload["source"], "hermes_analysis")
            self.assertEqual(payload["analysis_summary"]["analysis_counts"]["low"], 1)
            self.assertFalse(payload["request_preview"]["root_paths_included"])
            self.assertFalse(payload["request_preview"]["project_paths_included"])
            self.assertLessEqual(
                payload["prompt_preview"]["assembled_prompt_char_count"],
                workflow_cli.HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS,
            )
            self.assertNotIn(str(root.resolve()), json_result.stdout)
            self.assertNotIn(str(repo.resolve()), json_result.stdout)
            self.assertNotIn("v2-repo", json_result.stdout)

    def test_workflow_hermes_qwen_preview_redacts_target_content_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = self.create_v2_repo(root, "target-repo-name-should-not-leak")
            unique_body = "UNIQUE_TARGET_BODY_SHOULD_NOT_APPEAR_12345"
            write(repo / "AGENTS.md", f"# Contract\n{unique_body}\n")
            write(repo / "CLAUDE.md", f"{unique_body}-CLAUDE\n")
            write(repo / "GEMINI.md", f"{unique_body}-GEMINI\n")
            write(repo / ".env", "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=secret-value-that-must-not-appear\n")
            source_dir = repo / "src"
            source_dir.mkdir()
            write(source_dir / "app.py", f"print('{unique_body}-SOURCE')\n")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            result = self.run_cli(
                ROOT,
                "hermes",
                "qwen-preview",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = verify_hermes_qwen_preview_json_stdout(result.stdout)
            self.assertFalse(payload["root_paths_included"])
            self.assertFalse(payload["project_paths_included"])
            self.assertFalse(payload["env_values_included"])
            self.assertFalse(payload["api_key_values_included"])
            self.assertFalse(payload["target_repo_file_bodies_read"])
            for forbidden in (
                unique_body,
                "secret-value-that-must-not-appear",
                str(root.resolve()),
                str(repo.resolve()),
                "target-repo-name-should-not-leak",
            ):
                self.assertNotIn(forbidden, result.stdout)

    def test_workflow_hermes_qwen_preview_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root2 = Path(temp_dir) / "z-root"
            root1 = Path(temp_dir) / "a-root"
            root2.mkdir()
            root1.mkdir()
            repo_b = self.create_v2_repo(root2, "b-v2-repo")
            repo_a = build_legacy_repo(root2, "a-legacy-repo")
            repo_c = build_unmanaged_repo(root1, "c-unmanaged-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root2, root1])
            before = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }

            first = self.run_cli(
                ROOT,
                "hermes",
                "qwen-preview",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            second = self.run_cli(
                ROOT,
                "hermes",
                "qwen-preview",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            payload = verify_hermes_qwen_preview_json_stdout(first.stdout)
            self.assertEqual(payload["source_summary"]["repo_candidate_count"], 3)
            self.assertNotIn(str(root1.resolve()), first.stdout)
            self.assertNotIn(str(root2.resolve()), first.stdout)
            after = {
                "a-legacy-repo": self.snapshot_tree(repo_a),
                "b-v2-repo": self.snapshot_tree(repo_b),
                "c-unmanaged-repo": self.snapshot_tree(repo_c),
            }
            self.assertEqual(before, after)

    def test_workflow_hermes_qwen_preview_roots_config_failure_exits_nonzero_without_path_leak(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "missing-roots.json"
            result = self.run_cli(
                ROOT,
                "hermes",
                "qwen-preview",
                "--dry-run",
                "--json",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertNotEqual(result.returncode, 0)
            payload = verify_hermes_qwen_preview_json_stdout(result.stdout)
            self.assertTrue(payload["errors"])
            self.assertEqual(payload["source_summary"]["roots_error_count"], 1)
            self.assertNotIn(str(config), result.stdout)

    def test_workflow_hermes_qwen_preview_safety_flags_false_and_no_connectivity_coupling(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            self.create_v2_repo(root, "v2-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])

            original_probe = workflow_cli.probe_dashscope_connectivity
            original_preflight = workflow_cli.build_hermes_preflight_report
            calls = {"probe": 0, "preflight": 0}

            def fail_probe(*args: object, **kwargs: object) -> object:
                calls["probe"] += 1
                raise AssertionError("qwen-preview must not call the DashScope connectivity probe")

            def counted_preflight() -> workflow_cli.HermesPreflightReport:
                calls["preflight"] += 1
                return original_preflight()

            workflow_cli.probe_dashscope_connectivity = fail_probe
            workflow_cli.build_hermes_preflight_report = counted_preflight
            cwd = Path.cwd()
            old_roots_file = os.environ.get("WORKFLOW_ROOTS_FILE")
            os.environ["WORKFLOW_ROOTS_FILE"] = str(config)
            try:
                os.chdir(ROOT)
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    exit_code = workflow_cli.hermes_qwen_preview_command(dry_run=True, as_json=True)
            finally:
                workflow_cli.probe_dashscope_connectivity = original_probe
                workflow_cli.build_hermes_preflight_report = original_preflight
                if old_roots_file is None:
                    os.environ.pop("WORKFLOW_ROOTS_FILE", None)
                else:
                    os.environ["WORKFLOW_ROOTS_FILE"] = old_roots_file
                os.chdir(cwd)

            self.assertEqual(exit_code, 0)
            self.assertEqual(calls["probe"], 0)
            self.assertEqual(calls["preflight"], 1)
            payload = verify_hermes_qwen_preview_json_stdout(stdout.getvalue())
            for key in (
                "target_repos_modified",
                "network_attempted",
                "qwen_dashscope_enabled",
                "request_execution_enabled",
                "prompt_execution_enabled",
                "connectivity_probe_enabled",
                "graphify_enabled",
                "migration_writes_enabled",
                "report_writing_enabled",
                "target_repo_file_bodies_read",
                "live_response_parsing_enabled",
                "root_paths_included",
                "project_paths_included",
                "env_values_included",
                "api_key_values_included",
                "authorization_headers_included",
            ):
                self.assertFalse(payload[key], key)
            self.assertFalse(payload["request_preview"]["network_calls_allowed"])
            self.assertFalse(payload["request_preview"]["target_repo_file_bodies_included"])

    def test_workflow_open_uses_configured_roots_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = self.create_v2_repo(root, "v2-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])
            result = self.run_cli(ROOT, "open", "v2-repo", env={"WORKFLOW_ROOTS_FILE": str(config)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Resolved path: {repo.resolve()}", result.stdout)
            self.assertIn("Classification\nv2", result.stdout)

    def test_workflow_open_explicit_roots_override_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            actual_root = Path(temp_dir) / "actual-root"
            actual_root.mkdir()
            repo = self.create_v2_repo(actual_root, "override-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [Path(temp_dir) / "missing-root"])
            result = self.run_cli(
                ROOT,
                "open",
                "override-repo",
                "--roots",
                str(actual_root),
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Resolved path: {repo.resolve()}", result.stdout)

    def test_project_status_matches_workflow_status_on_v2_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir))
            cli_result = self.run_cli(repo, "status")
            shell_result = self.run_shell(
                roots=[Path(temp_dir)],
                command=f"cd {shlex.quote(str(repo))}\nproject-status",
            )
            self.assertEqual(cli_result.returncode, 0, cli_result.stderr)
            self.assertEqual(shell_result.returncode, 0, shell_result.stderr)
            self.assertEqual(cli_result.stdout, shell_result.stdout)

    def test_project_sync_matches_workflow_sync_on_v2_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir))
            cli_result = self.run_cli(repo, "sync")
            shell_result = self.run_shell(
                roots=[Path(temp_dir)],
                command=f"cd {shlex.quote(str(repo))}\nproject-sync",
            )
            self.assertEqual(cli_result.returncode, 0, cli_result.stderr)
            self.assertEqual(shell_result.returncode, 0, shell_result.stderr)
            self.assertEqual(cli_result.stdout, shell_result.stdout)

    def test_project_save_writes_primary_and_coexistence_logs_for_v2_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = self.create_v2_repo(Path(temp_dir), "coexist-repo", coexistence=True)
            before_primary = (repo / ".specify/state/session.log.md").read_text(encoding="utf-8")
            before_legacy = (repo / ".ai/logs/session.log").read_text(encoding="utf-8")
            result = self.run_shell(
                roots=[Path(temp_dir)],
                command=f"cd {shlex.quote(str(repo))}\nproject-save",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after_primary = (repo / ".specify/state/session.log.md").read_text(encoding="utf-8")
            after_legacy = (repo / ".ai/logs/session.log").read_text(encoding="utf-8")
            self.assertNotEqual(before_primary, after_primary)
            self.assertNotEqual(before_legacy, after_legacy)
            self.assertIn("appended primary session marker", result.stdout)
            self.assertIn("coexistence mirror", result.stdout)

    def test_project_close_guides_v2_continuity_and_opens_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            repo = self.create_v2_repo(temp_root)
            open_log = temp_root / "open.log"
            fake_open = temp_root / "fake-open"
            write(fake_open, f"#!/bin/sh\necho \"$1\" >> {shlex.quote(str(open_log))}\n")
            fake_open.chmod(0o755)
            result = self.run_shell(
                roots=[temp_root],
                open_cmd=fake_open,
                command=f"cd {shlex.quote(str(repo))}\nproject-close",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(".specify/state/handoff.md", result.stdout)
            self.assertIn(".specify/state/active.md", result.stdout)
            self.assertIn(".specify/state/progress.md", result.stdout)
            self.assertTrue(open_log.exists())
            self.assertIn(".specify/state/handoff.md", open_log.read_text(encoding="utf-8"))

    def test_project_list_classifies_repo_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root1 = Path(temp_dir) / "root1"
            root2 = Path(temp_dir) / "root2"
            root1.mkdir()
            root2.mkdir()
            self.create_v2_repo(root1, "v2-repo")
            build_legacy_repo(root1, "legacy-repo")
            build_mixed_repo(root1, "mixed-repo")
            build_unmanaged_repo(root1, "unmanaged-repo")
            build_error_repo(root1, "error-repo")

            result = self.run_shell(roots=[root1, root2], command="project-list")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("v2         v2-repo", result.stdout)
            self.assertIn("legacy     legacy-repo", result.stdout)
            self.assertIn("mixed      mixed-repo", result.stdout)
            self.assertIn("unmanaged  unmanaged-repo", result.stdout)
            self.assertIn("error      error-repo", result.stdout)

    def test_project_list_uses_repo_owned_roots_config_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            self.create_v2_repo(root, "v2-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])
            result = self.run_shell(
                command="project-list",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("v2         v2-repo", result.stdout)

    def test_project_open_existing_v2_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = self.create_v2_repo(root, "v2-repo")
            result = self.run_shell(
                roots=[root],
                command="project-open v2-repo\npwd",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Classification\nv2", result.stdout)
            self.assertIn("`.specify/state/handoff.md`", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_existing_legacy_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = build_legacy_repo(root, "legacy-repo")
            result = self.run_shell(
                roots=[root],
                command="project-open legacy-repo\npwd",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Classification\nlegacy", result.stdout)
            self.assertIn("`.ai/handoffs/NEXT_STEP.md`", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_existing_mixed_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = build_mixed_repo(root, "mixed-repo")
            result = self.run_shell(
                roots=[root],
                command="project-open mixed-repo\npwd",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Classification\nmixed", result.stdout)
            self.assertIn("V2 handoff candidate", result.stdout)
            self.assertIn("Legacy handoff candidate", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_existing_unmanaged_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = build_unmanaged_repo(root, "unmanaged-repo")
            result = self.run_shell(
                roots=[root],
                command="project-open unmanaged-repo\npwd",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Classification\nunmanaged", result.stdout)
            self.assertIn("Initialize the repo with `workflow init`", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_existing_error_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = build_error_repo(root, "error-repo")
            result = self.run_shell(
                roots=[root],
                command="project-open error-repo\npwd",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Classification\nerror", result.stdout)
            self.assertIn("Invalid `.workflow/workflow.json`", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_uses_repo_owned_roots_config_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = self.create_v2_repo(root, "configured-repo")
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])
            result = self.run_shell(
                command="project-open configured-repo\npwd",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Classification\nv2", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_creates_new_v2_repo_without_legacy_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = root / "new-repo"
            result = self.run_shell(
                roots=[root],
                command=f"project-open new-repo --root {shlex.quote(str(root))}\npwd",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo / ".workflow/workflow.json").exists())
            self.assertTrue((repo / ".specify/state/handoff.md").exists())
            self.assertFalse((repo / ".ai").exists())
            agents_text = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(".specify/state/handoff.md", agents_text)
            self.assertNotIn(".ai/handoffs/NEXT_STEP.md", agents_text)
            self.assertIn("Classification\nv2", result.stdout)
            self.assertEqual(Path(result.stdout.strip().splitlines()[-1]).resolve(), repo.resolve())

    def test_project_open_creation_uses_repo_owned_roots_config_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "root"
            root.mkdir()
            repo = root / "brand-new-repo"
            config = Path(temp_dir) / "roots.json"
            write_roots_config(config, [root])
            result = self.run_shell(
                command=f"project-open brand-new-repo --root {shlex.quote(str(root))}\npwd",
                env={"WORKFLOW_ROOTS_FILE": str(config)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((repo / ".workflow/workflow.json").exists())
            self.assertIn("Created new v2 project: brand-new-repo", result.stdout)

    def test_project_add_root_points_to_repo_owned_config(self) -> None:
        result = self.run_shell(command="project-add-root /tmp/example-root")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(".workflow/roots.json", result.stdout)
        self.assertIn("workflow roots --validate", result.stdout)
        self.assertIn("does not edit shell startup files automatically", result.stdout)


if __name__ == "__main__":
    unittest.main()
