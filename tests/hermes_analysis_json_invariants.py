from __future__ import annotations

import json
from pathlib import Path


EXPECTED_HERMES_ANALYSIS_JSON_SCHEMA_VERSION = "1.0.0"
EXPECTED_HERMES_ANALYSIS_JSON_COMMAND = "hermes_analysis"
EXPECTED_HERMES_ANALYSIS_JSON_MODE = "analysis"
EXPECTED_HERMES_ANALYSIS_JSON_KEYS = (
    "schema_version",
    "command",
    "mode",
    "dry_run",
    "roots_config_path",
    "summary",
    "analysis_counts",
    "roots",
    "warnings",
    "errors",
    "target_repos_modified",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
    "report_writing_enabled",
    "target_repo_file_bodies_read",
    "live_response_parsing_enabled",
)
EXPECTED_HERMES_ANALYSIS_COUNTS_KEYS = (
    "low",
    "medium",
    "high",
    "requires_human_review",
    "blocked",
)
EXPECTED_HERMES_ANALYSIS_ROOT_KEYS = (
    "path",
    "classification",
    "project_count",
    "issues",
    "analyses",
)
EXPECTED_HERMES_ANALYSIS_PROJECT_KEYS = (
    "name",
    "path",
    "root",
    "scaffold_classification",
    "automation_readiness",
    "migration_track",
    "migration_risk",
    "git_status",
    "deterministic_evidence",
    "inferred_recommendation",
    "blocked_actions",
    "required_human_review",
)
ALLOWED_HERMES_ANALYSIS_ROOT_CLASSIFICATIONS = {
    "configured-root",
    "missing-root",
    "invalid-root",
}
ALLOWED_HERMES_ANALYSIS_SCAFFOLD_CLASSIFICATIONS = {
    "v2",
    "legacy",
    "mixed",
    "unmanaged",
    "error",
}
ALLOWED_HERMES_ANALYSIS_READINESS = {"ready", "needs_review", "blocked"}
ALLOWED_HERMES_ANALYSIS_MIGRATION_RISK = {"low", "medium", "high"}
ALLOWED_HERMES_ANALYSIS_GIT_STATUSES = {"clean", "dirty", "not-git"}
FORBIDDEN_HERMES_ANALYSIS_EVIDENCE_TOKENS = (
    "prompt",
    "request_shape",
    "response_shape",
    "parsed_response",
    "qwen_payload",
    "dashscope_payload",
    "file_body",
    "source_body",
    "docs_body",
    "continuity_body",
)


def _assert_json_object(label: str, payload: object) -> dict:
    if not isinstance(payload, dict):
        raise AssertionError(f"{label} must be a JSON object.")
    return payload


def _assert_exact_keys(label: str, payload: dict, expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    raise AssertionError(f"{label} keys drifted. Missing keys: {missing}. Unexpected keys: {unexpected}.")


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError(f"{label} must be a string.")
    return value


def _assert_integer(label: str, value: object) -> int:
    if not isinstance(value, int):
        raise AssertionError(f"{label} must be an integer.")
    return value


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise AssertionError(f"{label} must be a boolean.")
    return value


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AssertionError(f"{label} must be a list of strings.")
    return list(value)


def verify_hermes_analysis_json_payload(
    payload: object,
    *,
    expected_roots_config_path: Path | None = None,
) -> dict:
    payload = _assert_json_object("Hermes analysis payload", payload)
    _assert_exact_keys("Hermes analysis payload", payload, EXPECTED_HERMES_ANALYSIS_JSON_KEYS)

    if _assert_string("Hermes analysis payload.schema_version", payload["schema_version"]) != EXPECTED_HERMES_ANALYSIS_JSON_SCHEMA_VERSION:
        raise AssertionError("Hermes analysis payload.schema_version drifted.")
    if _assert_string("Hermes analysis payload.command", payload["command"]) != EXPECTED_HERMES_ANALYSIS_JSON_COMMAND:
        raise AssertionError("Hermes analysis payload.command drifted.")
    if _assert_string("Hermes analysis payload.mode", payload["mode"]) != EXPECTED_HERMES_ANALYSIS_JSON_MODE:
        raise AssertionError("Hermes analysis payload.mode drifted.")
    if _assert_bool("Hermes analysis payload.dry_run", payload["dry_run"]) is not True:
        raise AssertionError("Hermes analysis payload.dry_run must remain true.")

    roots_config_path = payload["roots_config_path"]
    if roots_config_path is not None and not isinstance(roots_config_path, str):
        raise AssertionError("Hermes analysis payload.roots_config_path must be a string or null.")
    if expected_roots_config_path is not None and roots_config_path != str(expected_roots_config_path.resolve()):
        raise AssertionError("Hermes analysis payload.roots_config_path drifted.")

    _assert_string("Hermes analysis payload.summary", payload["summary"])
    analysis_counts = _assert_json_object("Hermes analysis payload.analysis_counts", payload["analysis_counts"])
    _assert_exact_keys("Hermes analysis payload.analysis_counts", analysis_counts, EXPECTED_HERMES_ANALYSIS_COUNTS_KEYS)
    for key in EXPECTED_HERMES_ANALYSIS_COUNTS_KEYS:
        _assert_integer(f"Hermes analysis payload.analysis_counts.{key}", analysis_counts[key])

    _assert_string_list("Hermes analysis payload.warnings", payload["warnings"])
    _assert_string_list("Hermes analysis payload.errors", payload["errors"])
    for key in (
        "target_repos_modified",
        "qwen_dashscope_enabled",
        "graphify_enabled",
        "migration_writes_enabled",
        "report_writing_enabled",
        "target_repo_file_bodies_read",
        "live_response_parsing_enabled",
    ):
        if _assert_bool(f"Hermes analysis payload.{key}", payload[key]) is not False:
            raise AssertionError(f"Hermes analysis payload.{key} must remain false.")

    roots = payload["roots"]
    if not isinstance(roots, list):
        raise AssertionError("Hermes analysis payload.roots must be a list.")
    root_paths: list[str] = []
    for root in roots:
        root_payload = _assert_json_object("Hermes analysis root payload", root)
        _assert_exact_keys("Hermes analysis root payload", root_payload, EXPECTED_HERMES_ANALYSIS_ROOT_KEYS)
        root_path = _assert_string("Hermes analysis root payload.path", root_payload["path"])
        root_paths.append(root_path)
        if _assert_string("Hermes analysis root payload.classification", root_payload["classification"]) not in ALLOWED_HERMES_ANALYSIS_ROOT_CLASSIFICATIONS:
            raise AssertionError("Hermes analysis root classification vocabulary drifted.")
        _assert_integer("Hermes analysis root payload.project_count", root_payload["project_count"])
        _assert_string_list("Hermes analysis root payload.issues", root_payload["issues"])
        analyses = root_payload["analyses"]
        if not isinstance(analyses, list):
            raise AssertionError("Hermes analysis root payload.analyses must be a list.")
        if root_payload["project_count"] != len(analyses):
            raise AssertionError("Hermes analysis root payload.project_count must match analyses length.")
        analysis_order: list[tuple[str, str]] = []
        for analysis in analyses:
            analysis_payload = _assert_json_object("Hermes analysis project payload", analysis)
            _assert_exact_keys(
                "Hermes analysis project payload",
                analysis_payload,
                EXPECTED_HERMES_ANALYSIS_PROJECT_KEYS,
            )
            project_name = _assert_string("Hermes analysis project payload.name", analysis_payload["name"])
            project_path = _assert_string("Hermes analysis project payload.path", analysis_payload["path"])
            analysis_order.append((project_name, project_path))
            if _assert_string("Hermes analysis project payload.root", analysis_payload["root"]) != root_path:
                raise AssertionError("Hermes analysis project payload.root must match parent root.")
            if _assert_string(
                "Hermes analysis project payload.scaffold_classification",
                analysis_payload["scaffold_classification"],
            ) not in ALLOWED_HERMES_ANALYSIS_SCAFFOLD_CLASSIFICATIONS:
                raise AssertionError("Hermes analysis project scaffold classification vocabulary drifted.")
            if _assert_string(
                "Hermes analysis project payload.automation_readiness",
                analysis_payload["automation_readiness"],
            ) not in ALLOWED_HERMES_ANALYSIS_READINESS:
                raise AssertionError("Hermes analysis automation readiness vocabulary drifted.")
            _assert_string("Hermes analysis project payload.migration_track", analysis_payload["migration_track"])
            if _assert_string(
                "Hermes analysis project payload.migration_risk",
                analysis_payload["migration_risk"],
            ) not in ALLOWED_HERMES_ANALYSIS_MIGRATION_RISK:
                raise AssertionError("Hermes analysis migration risk vocabulary drifted.")
            if _assert_string(
                "Hermes analysis project payload.git_status",
                analysis_payload["git_status"],
            ) not in ALLOWED_HERMES_ANALYSIS_GIT_STATUSES:
                raise AssertionError("Hermes analysis git status vocabulary drifted.")
            evidence = _assert_string_list(
                "Hermes analysis project payload.deterministic_evidence",
                analysis_payload["deterministic_evidence"],
            )
            if not evidence or any(not item.startswith("preflight.") for item in evidence):
                raise AssertionError("Hermes analysis evidence must remain preflight-derived.")
            combined_evidence = "\n".join(evidence).lower()
            if any(token in combined_evidence for token in FORBIDDEN_HERMES_ANALYSIS_EVIDENCE_TOKENS):
                raise AssertionError("Hermes analysis evidence must not reference prompts, responses, payloads, or file bodies.")
            _assert_string(
                "Hermes analysis project payload.inferred_recommendation",
                analysis_payload["inferred_recommendation"],
            )
            blocked_actions = _assert_string_list(
                "Hermes analysis project payload.blocked_actions",
                analysis_payload["blocked_actions"],
            )
            if "Qwen/DashScope analysis" not in blocked_actions:
                raise AssertionError("Hermes analysis must explicitly keep Qwen/DashScope analysis blocked.")
            if "live response parsing" not in blocked_actions:
                raise AssertionError("Hermes analysis must explicitly keep live response parsing blocked.")
            _assert_bool(
                "Hermes analysis project payload.required_human_review",
                analysis_payload["required_human_review"],
            )
        if analysis_order != sorted(analysis_order):
            raise AssertionError("Hermes analysis projects must be ordered by name/path.")
    if root_paths != sorted(root_paths):
        raise AssertionError("Hermes analysis roots must be ordered by path.")
    return payload


def verify_hermes_analysis_json_stdout(
    stdout: str,
    *,
    expected_roots_config_path: Path | None = None,
) -> dict:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Hermes analysis stdout must be valid JSON: {exc}") from exc
    return verify_hermes_analysis_json_payload(
        payload,
        expected_roots_config_path=expected_roots_config_path,
    )
