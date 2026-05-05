from __future__ import annotations

import json


EXPECTED_HERMES_QWEN_PREVIEW_SCHEMA_VERSION = "1.0.0"
EXPECTED_HERMES_QWEN_PREVIEW_COMMAND = "hermes_qwen_preview"
EXPECTED_HERMES_QWEN_PREVIEW_MODE = "offline_qwen_preview"
EXPECTED_HERMES_QWEN_PREVIEW_SOURCE = "hermes_analysis"
EXPECTED_HERMES_QWEN_PREVIEW_JSON_KEYS = (
    "schema_version",
    "command",
    "mode",
    "dry_run",
    "source",
    "source_schema_version",
    "intended_model",
    "selected_model",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "local_config_ready",
    "preview_limits",
    "source_summary",
    "analysis_summary",
    "request_preview",
    "prompt_preview",
    "warnings",
    "errors",
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
)
EXPECTED_HERMES_QWEN_PREVIEW_LIMIT_KEYS = (
    "max_section_chars",
    "max_assembled_prompt_chars",
    "max_evidence_categories",
)
EXPECTED_HERMES_QWEN_PREVIEW_SOURCE_SUMMARY_KEYS = (
    "source_command",
    "source_schema_version",
    "source_mode",
    "source_dry_run",
    "configured_root_count",
    "usable_root_count",
    "repo_candidate_count",
    "roots_status",
    "roots_warning_count",
    "roots_error_count",
)
EXPECTED_HERMES_QWEN_PREVIEW_ANALYSIS_SUMMARY_KEYS = (
    "summary",
    "analysis_counts",
    "readiness_counts",
    "git_status_counts",
    "scaffold_classification_counts",
    "migration_track_counts",
    "blocked_action_counts",
    "evidence_category_counts",
    "evidence_category_count",
)
EXPECTED_HERMES_QWEN_PREVIEW_REQUEST_KEYS = (
    "request_shape",
    "source_command",
    "source_schema_version",
    "source_mode",
    "source_dry_run",
    "intended_model",
    "selected_model",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "local_config_ready",
    "runtime_enabled",
    "network_calls_allowed",
    "request_execution_enabled",
    "qwen_dashscope_enabled",
    "input_kind",
    "root_paths_included",
    "project_paths_included",
    "env_values_included",
    "api_key_values_included",
    "authorization_headers_included",
    "target_repo_file_bodies_included",
)
EXPECTED_HERMES_QWEN_PREVIEW_PROMPT_KEYS = (
    "preview_type",
    "preview_only",
    "prompt_execution_enabled",
    "section_order",
    "section_char_counts",
    "sections",
    "assembled_prompt_preview",
    "assembled_prompt_char_count",
    "max_section_chars",
    "max_assembled_prompt_chars",
)
EXPECTED_HERMES_QWEN_PREVIEW_SECTION_ORDER = (
    "system_role",
    "task",
    "source_summary",
    "analysis_summary",
    "evidence_category_summary",
    "safety_constraints",
    "expected_output_shape",
    "redaction_policy",
)
EXPECTED_HERMES_QWEN_PREVIEW_ANALYSIS_COUNT_KEYS = (
    "low",
    "medium",
    "high",
    "requires_human_review",
    "blocked",
)
EXPECTED_HERMES_QWEN_PREVIEW_READINESS_KEYS = ("ready", "needs_review", "blocked")
EXPECTED_HERMES_QWEN_PREVIEW_GIT_STATUS_KEYS = ("clean", "dirty", "not-git")
EXPECTED_HERMES_QWEN_PREVIEW_SCAFFOLD_KEYS = ("v2", "legacy", "mixed", "unmanaged", "error")
ALLOWED_HERMES_QWEN_PREVIEW_ROOTS_STATUS = {"pass", "warn", "fail"}
ALLOWED_HERMES_QWEN_PREVIEW_MODEL_POLICY_STATUS = {
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
}
FORBIDDEN_HERMES_QWEN_PREVIEW_TEXT_FRAGMENTS = (
    "/tmp/",
    "<private-user-home>/",
    "Authorization:",
    "Bearer ",
    "DASHSCOPE_API_KEY" "=",
    "DASHSCOPE_API_KEY_WORKFLOW_MANAGER=",
    "sk-",
    "api_key_prefix",
    "api_key_suffix",
    "project_source_code",
    "target_repo_file_contents",
    "memory_file_bodies",
    "state_file_bodies",
    "chain_of_thought",
)


def _assert_json_object(label: str, payload: object) -> dict:
    if not isinstance(payload, dict):
        raise AssertionError(f"{label} must be a JSON object.")
    return payload


def _assert_exact_keys(label: str, payload: dict, expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise AssertionError(f"{label} keys drifted. Missing keys: {missing}. Unexpected keys: {unexpected}.")


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError(f"{label} must be a string.")
    return value


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise AssertionError(f"{label} must be a boolean.")
    return value


def _assert_integer(label: str, value: object) -> int:
    if not isinstance(value, int):
        raise AssertionError(f"{label} must be an integer.")
    return value


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AssertionError(f"{label} must be a list of strings.")
    return list(value)


def _assert_count_map(label: str, value: object, expected_keys: tuple[str, ...] | None = None) -> dict:
    payload = _assert_json_object(label, value)
    if expected_keys is not None:
        _assert_exact_keys(label, payload, expected_keys)
    for key, count in payload.items():
        if not isinstance(key, str):
            raise AssertionError(f"{label} keys must be strings.")
        if not isinstance(count, int) or count < 0:
            raise AssertionError(f"{label}.{key} must be a non-negative integer.")
    return payload


def _assert_no_forbidden_text(payload: dict) -> None:
    rendered = json.dumps(payload, sort_keys=True)
    for fragment in FORBIDDEN_HERMES_QWEN_PREVIEW_TEXT_FRAGMENTS:
        if fragment in rendered:
            raise AssertionError(f"Hermes Qwen preview leaked forbidden text fragment `{fragment}`.")


def verify_hermes_qwen_preview_json_payload(payload: object) -> dict:
    payload = _assert_json_object("Hermes Qwen preview payload", payload)
    _assert_exact_keys("Hermes Qwen preview payload", payload, EXPECTED_HERMES_QWEN_PREVIEW_JSON_KEYS)

    if _assert_string("Hermes Qwen preview payload.schema_version", payload["schema_version"]) != EXPECTED_HERMES_QWEN_PREVIEW_SCHEMA_VERSION:
        raise AssertionError("Hermes Qwen preview schema version drifted.")
    if _assert_string("Hermes Qwen preview payload.command", payload["command"]) != EXPECTED_HERMES_QWEN_PREVIEW_COMMAND:
        raise AssertionError("Hermes Qwen preview command drifted.")
    if _assert_string("Hermes Qwen preview payload.mode", payload["mode"]) != EXPECTED_HERMES_QWEN_PREVIEW_MODE:
        raise AssertionError("Hermes Qwen preview mode drifted.")
    if _assert_bool("Hermes Qwen preview payload.dry_run", payload["dry_run"]) is not True:
        raise AssertionError("Hermes Qwen preview must remain dry-run.")
    if _assert_string("Hermes Qwen preview payload.source", payload["source"]) != EXPECTED_HERMES_QWEN_PREVIEW_SOURCE:
        raise AssertionError("Hermes Qwen preview source must remain Hermes analysis.")
    if _assert_string("Hermes Qwen preview payload.intended_model", payload["intended_model"]) != "qwen3.6-plus":
        raise AssertionError("Hermes Qwen preview intended model drifted.")
    _assert_string("Hermes Qwen preview payload.selected_model", payload["selected_model"])
    if _assert_string("Hermes Qwen preview payload.model_policy_status", payload["model_policy_status"]) not in ALLOWED_HERMES_QWEN_PREVIEW_MODEL_POLICY_STATUS:
        raise AssertionError("Hermes Qwen preview model policy status drifted.")
    _assert_bool("Hermes Qwen preview payload.model_policy_ready", payload["model_policy_ready"])
    _assert_bool("Hermes Qwen preview payload.model_policy_requires_update", payload["model_policy_requires_update"])
    _assert_bool("Hermes Qwen preview payload.local_config_ready", payload["local_config_ready"])

    limits = _assert_json_object("Hermes Qwen preview payload.preview_limits", payload["preview_limits"])
    _assert_exact_keys("Hermes Qwen preview payload.preview_limits", limits, EXPECTED_HERMES_QWEN_PREVIEW_LIMIT_KEYS)
    for key in EXPECTED_HERMES_QWEN_PREVIEW_LIMIT_KEYS:
        if _assert_integer(f"Hermes Qwen preview payload.preview_limits.{key}", limits[key]) <= 0:
            raise AssertionError(f"Hermes Qwen preview payload.preview_limits.{key} must be positive.")

    source_summary = _assert_json_object("Hermes Qwen preview payload.source_summary", payload["source_summary"])
    _assert_exact_keys("Hermes Qwen preview payload.source_summary", source_summary, EXPECTED_HERMES_QWEN_PREVIEW_SOURCE_SUMMARY_KEYS)
    if source_summary["source_command"] != "hermes_analysis":
        raise AssertionError("Hermes Qwen preview source summary must stay analysis-derived.")
    if source_summary["source_mode"] != "analysis":
        raise AssertionError("Hermes Qwen preview source mode must stay analysis.")
    if source_summary["source_dry_run"] is not True:
        raise AssertionError("Hermes Qwen preview source must remain dry-run.")
    if source_summary["roots_status"] not in ALLOWED_HERMES_QWEN_PREVIEW_ROOTS_STATUS:
        raise AssertionError("Hermes Qwen preview roots status vocabulary drifted.")
    for key in (
        "configured_root_count",
        "usable_root_count",
        "repo_candidate_count",
        "roots_warning_count",
        "roots_error_count",
    ):
        if _assert_integer(f"Hermes Qwen preview payload.source_summary.{key}", source_summary[key]) < 0:
            raise AssertionError(f"Hermes Qwen preview payload.source_summary.{key} must be non-negative.")

    analysis_summary = _assert_json_object("Hermes Qwen preview payload.analysis_summary", payload["analysis_summary"])
    _assert_exact_keys(
        "Hermes Qwen preview payload.analysis_summary",
        analysis_summary,
        EXPECTED_HERMES_QWEN_PREVIEW_ANALYSIS_SUMMARY_KEYS,
    )
    _assert_string("Hermes Qwen preview payload.analysis_summary.summary", analysis_summary["summary"])
    _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.analysis_counts",
        analysis_summary["analysis_counts"],
        EXPECTED_HERMES_QWEN_PREVIEW_ANALYSIS_COUNT_KEYS,
    )
    _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.readiness_counts",
        analysis_summary["readiness_counts"],
        EXPECTED_HERMES_QWEN_PREVIEW_READINESS_KEYS,
    )
    _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.git_status_counts",
        analysis_summary["git_status_counts"],
        EXPECTED_HERMES_QWEN_PREVIEW_GIT_STATUS_KEYS,
    )
    _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.scaffold_classification_counts",
        analysis_summary["scaffold_classification_counts"],
        EXPECTED_HERMES_QWEN_PREVIEW_SCAFFOLD_KEYS,
    )
    _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.migration_track_counts",
        analysis_summary["migration_track_counts"],
    )
    _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.blocked_action_counts",
        analysis_summary["blocked_action_counts"],
    )
    evidence_counts = _assert_count_map(
        "Hermes Qwen preview payload.analysis_summary.evidence_category_counts",
        analysis_summary["evidence_category_counts"],
    )
    if len(evidence_counts) > limits["max_evidence_categories"]:
        raise AssertionError("Hermes Qwen preview evidence categories exceeded the governed cap.")
    if analysis_summary["evidence_category_count"] != len(evidence_counts):
        raise AssertionError("Hermes Qwen preview evidence_category_count must match evidence_category_counts.")
    for key in evidence_counts:
        if not key.startswith("preflight."):
            raise AssertionError("Hermes Qwen preview evidence categories must stay preflight-derived.")

    request_preview = _assert_json_object("Hermes Qwen preview payload.request_preview", payload["request_preview"])
    _assert_exact_keys("Hermes Qwen preview payload.request_preview", request_preview, EXPECTED_HERMES_QWEN_PREVIEW_REQUEST_KEYS)
    for key in (
        "runtime_enabled",
        "network_calls_allowed",
        "request_execution_enabled",
        "qwen_dashscope_enabled",
        "root_paths_included",
        "project_paths_included",
        "env_values_included",
        "api_key_values_included",
        "authorization_headers_included",
        "target_repo_file_bodies_included",
    ):
        if request_preview[key] is not False:
            raise AssertionError(f"Hermes Qwen preview request_preview.{key} must remain false.")
    if request_preview["source_command"] != "hermes_analysis" or request_preview["source_mode"] != "analysis":
        raise AssertionError("Hermes Qwen preview request source must remain analysis-derived.")
    if request_preview["input_kind"] != "bounded-analysis-summary":
        raise AssertionError("Hermes Qwen preview request input kind drifted.")

    prompt_preview = _assert_json_object("Hermes Qwen preview payload.prompt_preview", payload["prompt_preview"])
    _assert_exact_keys("Hermes Qwen preview payload.prompt_preview", prompt_preview, EXPECTED_HERMES_QWEN_PREVIEW_PROMPT_KEYS)
    if prompt_preview["preview_type"] != "bounded_prompt_preview":
        raise AssertionError("Hermes Qwen preview prompt type drifted.")
    if prompt_preview["preview_only"] is not True:
        raise AssertionError("Hermes Qwen preview prompt must remain preview-only.")
    if prompt_preview["prompt_execution_enabled"] is not False:
        raise AssertionError("Hermes Qwen preview prompt execution must remain disabled.")
    if tuple(prompt_preview["section_order"]) != EXPECTED_HERMES_QWEN_PREVIEW_SECTION_ORDER:
        raise AssertionError("Hermes Qwen preview section order drifted.")
    section_counts = _assert_count_map("Hermes Qwen preview payload.prompt_preview.section_char_counts", prompt_preview["section_char_counts"])
    sections = _assert_json_object("Hermes Qwen preview payload.prompt_preview.sections", prompt_preview["sections"])
    _assert_exact_keys("Hermes Qwen preview payload.prompt_preview.sections", sections, EXPECTED_HERMES_QWEN_PREVIEW_SECTION_ORDER)
    for key in EXPECTED_HERMES_QWEN_PREVIEW_SECTION_ORDER:
        text = _assert_string(f"Hermes Qwen preview payload.prompt_preview.sections.{key}", sections[key])
        if not text.strip():
            raise AssertionError(f"Hermes Qwen preview section `{key}` must not be empty.")
        if section_counts[key] != len(text):
            raise AssertionError(f"Hermes Qwen preview section count for `{key}` drifted.")
        if len(text) > limits["max_section_chars"]:
            raise AssertionError(f"Hermes Qwen preview section `{key}` exceeded the governed section budget.")
    assembled = _assert_string(
        "Hermes Qwen preview payload.prompt_preview.assembled_prompt_preview",
        prompt_preview["assembled_prompt_preview"],
    )
    if prompt_preview["assembled_prompt_char_count"] != len(assembled):
        raise AssertionError("Hermes Qwen preview assembled prompt char count drifted.")
    if len(assembled) > limits["max_assembled_prompt_chars"]:
        raise AssertionError("Hermes Qwen preview assembled prompt exceeded the governed budget.")
    for key in EXPECTED_HERMES_QWEN_PREVIEW_SECTION_ORDER:
        if sections[key] not in assembled:
            raise AssertionError(f"Hermes Qwen preview assembled prompt omitted section `{key}`.")

    _assert_string_list("Hermes Qwen preview payload.warnings", payload["warnings"])
    _assert_string_list("Hermes Qwen preview payload.errors", payload["errors"])
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
        if _assert_bool(f"Hermes Qwen preview payload.{key}", payload[key]) is not False:
            raise AssertionError(f"Hermes Qwen preview payload.{key} must remain false.")

    _assert_no_forbidden_text(payload)
    return payload


def verify_hermes_qwen_preview_json_stdout(stdout: str) -> dict:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Hermes Qwen preview stdout is not valid JSON: {exc}") from exc
    return verify_hermes_qwen_preview_json_payload(payload)
