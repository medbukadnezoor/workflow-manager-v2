from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
from workflow_manager.dashscope_response_consumer import (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
)


DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE = "consumer_decision_human_review_policy"
DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE = "offline_consumer_decision_policy_only"
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS = (
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
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES = (
    "accept_explanatory_only",
    "reject_unsafe",
    "escalate_human_review",
    "requires_deterministic_recheck",
    "blocked_by_missing_evidence",
    "blocked_by_policy_violation",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS = (
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
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_REQUIRED_HUMAN_REVIEW_RULES = {
    "ambiguous_or_partial_evidence": "escalate_human_review",
    "migration_readiness_claim": "escalate_human_review",
    "target_repo_write_recommendation": "escalate_human_review",
    "deterministic_mismatch": "escalate_human_review",
    "model_policy_mismatch": "escalate_human_review",
    "unknown_or_unsafe_output_field": "escalate_human_review",
    "low_confidence": "escalate_human_review",
    "unresolved_recheck_requirement": "escalate_human_review",
}
DASHSCOPE_OFFLINE_CONSUMER_DECISION_CONFIDENCE_POLICY = {
    "confidence_is_advisory_only": True,
    "high_confidence_does_not_override_deterministic_evidence": True,
    "low_confidence_handling": "escalate_human_review",
    "missing_confidence_handling": "requires_deterministic_recheck",
    "missing_evidence_override_handling": "blocked_by_missing_evidence",
}
DASHSCOPE_OFFLINE_CONSUMER_DECISION_READY_TO_MIGRATE_CLAIM_POLICY = {
    "deterministic_gates_required": True,
    "qwen_cannot_authorize_migration": True,
    "ready_to_migrate_without_gates_handling": "reject_unsafe",
}
DASHSCOPE_OFFLINE_CONSUMER_DECISION_AUTHORITY_POLICY = {
    "deterministic_hermes_data_is_source_of_truth": True,
    "qwen_output_is_explanatory_only": True,
    "source_of_truth_override_handling": "reject_unsafe",
    "migration_write_authorization_handling": "reject_unsafe",
    "classification_change_handling": "reject_unsafe",
    "missing_evidence_handling": "blocked_by_missing_evidence",
    "unknown_evidence_handling": "requires_deterministic_recheck",
    "deterministic_mismatch_handling": "escalate_human_review",
    "confidence_is_advisory_only": True,
}
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES = (
    "high",
    "medium",
    "low",
    "missing",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS = (
    "grounded",
    "missing-evidence",
    "unknown-evidence",
    "policy-violation",
    "deterministic-mismatch",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS = (
    "api_key_material",
    "raw_env",
    "env_values",
    "credentials",
    "tokens",
    "hidden_reasoning",
    "chain_of_thought",
    "migration_write_instructions",
    "target_repo_modification_instructions",
    "write_commands",
    "graphify_execution_instructions",
    "report_writing_instructions",
    "source_of_truth_override",
    "ready_to_migrate_without_deterministic_gates",
    "project_source_code",
    "target_repo_file_contents",
    "generated_shim_contents",
    "memory_state_file_bodies",
    "full_agents_claude_gemini_contents",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS = (
    "response_notes",
    "unknown_output_field",
    "unsafe_extra_field",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FORBIDDEN_FLAGS = (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS
    + DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS = (
    "example_name",
    "decision_inputs",
    "expected_decision_state",
    "requires_human_review",
    "requires_deterministic_recheck",
    "decision_reason",
)
DASHSCOPE_OFFLINE_CONSUMER_DECISION_DEFAULT_SIMULATED_EXAMPLES: tuple[dict[str, object], ...] = (
    {
        "example_name": "valid_grounded_explanatory_response",
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
                "doctor_result_status",
                "dashscope_readiness_policy",
            ],
            "model_policy_status": "default",
            "deterministic_mismatch_flag": False,
        },
        "expected_decision_state": "accept_explanatory_only",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": (
            "Accept only as explanatory output because the response stays grounded in deterministic evidence and does not "
            "attempt to override governed Hermes authority."
        ),
    },
    {
        "example_name": "missing_evidence_for_recommendation",
        "decision_inputs": {
            "evidence_validation_result": "missing-evidence",
            "missing_evidence_fields": ["recommended_next_step"],
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
        "decision_reason": "Block because a governed recommendation field is missing deterministic evidence.",
    },
    {
        "example_name": "unknown_evidence_reference",
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
            "deterministic_reference_categories": ["hermes_warning_count"],
            "model_policy_status": "default",
            "deterministic_mismatch_flag": False,
        },
        "expected_decision_state": "requires_deterministic_recheck",
        "requires_human_review": False,
        "requires_deterministic_recheck": True,
        "decision_reason": "Recheck because an evidence reference falls outside the governed deterministic vocabulary.",
    },
    {
        "example_name": "source_of_truth_override_claim",
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
        "expected_decision_state": "reject_unsafe",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Reject because Qwen output cannot override deterministic Hermes source-of-truth data.",
    },
    {
        "example_name": "migration_write_authorization",
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
        "expected_decision_state": "reject_unsafe",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Reject because migration-write authorization is outside explanatory-only consumer authority.",
    },
    {
        "example_name": "ready_to_migrate_without_gates",
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
        "expected_decision_state": "reject_unsafe",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Reject because migration readiness cannot be claimed without deterministic gates.",
    },
    {
        "example_name": "hidden_reasoning_output",
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
        "expected_decision_state": "reject_unsafe",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Reject because hidden reasoning and chain-of-thought output remain forbidden.",
    },
    {
        "example_name": "secret_like_content",
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
        "expected_decision_state": "reject_unsafe",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Reject because secret-like content must never enter governed consumer-decision handling.",
    },
    {
        "example_name": "target_repo_file_contents",
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
        "expected_decision_state": "reject_unsafe",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Reject because target-repo file contents are not allowed in governed consumer decisions.",
    },
    {
        "example_name": "low_confidence_requires_human_review",
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
        "expected_decision_state": "escalate_human_review",
        "requires_human_review": True,
        "requires_deterministic_recheck": False,
        "decision_reason": "Escalate because low confidence is advisory only and cannot justify acceptance.",
    },
    {
        "example_name": "missing_confidence_requires_recheck",
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
        "expected_decision_state": "requires_deterministic_recheck",
        "requires_human_review": False,
        "requires_deterministic_recheck": True,
        "decision_reason": "Recheck because missing confidence must not be treated as positive evidence.",
    },
    {
        "example_name": "confidence_cannot_override_missing_evidence",
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
        "expected_decision_state": "blocked_by_missing_evidence",
        "requires_human_review": False,
        "requires_deterministic_recheck": False,
        "decision_reason": "Block because high confidence cannot override missing deterministic evidence.",
    },
    {
        "example_name": "deterministic_mismatch_requires_human_review",
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
            "deterministic_reference_categories": ["status_health_overview", "doctor_result_status"],
            "model_policy_status": "default",
            "deterministic_mismatch_flag": True,
        },
        "expected_decision_state": "escalate_human_review",
        "requires_human_review": True,
        "requires_deterministic_recheck": False,
        "decision_reason": "Escalate because Qwen explanations must not disagree with deterministic Hermes findings.",
    },
    {
        "example_name": "unsafe_extra_field",
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
        "expected_decision_state": "blocked_by_policy_violation",
        "requires_human_review": True,
        "requires_deterministic_recheck": False,
        "decision_reason": "Block because unsafe extra output fields remain outside the governed response contract.",
    },
)


def _assert_json_object(label: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object.")
    return dict(value)


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean.")
    return value


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string.")
    return value


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings.")
    return list(value)


def _assert_exact_keys(label: str, payload: dict[str, object], expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    parts = [f"{label} keys drifted."]
    if missing:
        parts.append(f"Missing keys: {missing}.")
    if unexpected:
        parts.append(f"Unexpected keys: {unexpected}.")
    raise ValueError(" ".join(parts))


def _assert_unique_strings(label: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must not contain duplicates.")


def _normalize_response_consumer_policy(
    payload: DashScopeOfflineConsumerDecisionPolicy | dict[str, object] | object,
) -> dict[str, object]:
    consumer_policy = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline DashScope/Qwen consumer-decision response-consumer policy",
        consumer_policy,
        DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS,
    )

    if _assert_string("response-consumer source", consumer_policy["source"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE:
        raise ValueError("Offline consumer-decision policy requires hermes_inventory response-consumer input.")
    if _assert_string("response-consumer mode", consumer_policy["mode"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE:
        raise ValueError("Offline consumer-decision policy requires offline_response_consumer_policy_only mode.")
    if (
        _assert_string("response-consumer version", consumer_policy["response_consumer_policy_version"])
        != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION
    ):
        raise ValueError("Offline consumer-decision policy received an unexpected response-consumer policy version.")
    if _assert_string("response-consumer type", consumer_policy["consumer_type"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE:
        raise ValueError("Offline consumer-decision policy requires evidence_slot_response_consumer_policy input.")
    if _assert_string("response-consumer intended_model", consumer_policy["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline consumer-decision policy requires the governed intended model.")
    if not _assert_bool("response-consumer response_explanatory_only", consumer_policy["response_explanatory_only"]):
        raise ValueError("Offline consumer-decision policy requires response_explanatory_only=true.")
    if _assert_bool("response-consumer live_response_parsing_enabled", consumer_policy["live_response_parsing_enabled"]):
        raise ValueError("Offline consumer-decision policy requires live_response_parsing_enabled=false.")
    if _assert_bool("response-consumer runtime_enabled", consumer_policy["runtime_enabled"]):
        raise ValueError("Offline consumer-decision policy requires runtime_enabled=false.")
    if _assert_bool("response-consumer network_calls_allowed", consumer_policy["network_calls_allowed"]):
        raise ValueError("Offline consumer-decision policy requires network_calls_allowed=false.")
    if _assert_bool("response-consumer qwen_dashscope_enabled", consumer_policy["qwen_dashscope_enabled"]):
        raise ValueError("Offline consumer-decision policy requires qwen_dashscope_enabled=false.")
    if _assert_bool("response-consumer graphify_enabled", consumer_policy["graphify_enabled"]):
        raise ValueError("Offline consumer-decision policy requires graphify_enabled=false.")
    if _assert_bool("response-consumer migration_writes_enabled", consumer_policy["migration_writes_enabled"]):
        raise ValueError("Offline consumer-decision policy requires migration_writes_enabled=false.")

    evidence_categories = _assert_string_list(
        "response-consumer allowed_evidence_reference_categories",
        consumer_policy["allowed_evidence_reference_categories"],
    )
    if tuple(evidence_categories) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES:
        raise ValueError("Offline consumer-decision policy received drifted evidence reference categories.")

    required_fields = _assert_string_list(
        "response-consumer response_fields_requiring_evidence",
        consumer_policy["response_fields_requiring_evidence"],
    )
    if tuple(required_fields) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE:
        raise ValueError("Offline consumer-decision policy received drifted evidence-required response fields.")

    input_summary = _assert_json_object("response-consumer input_summary", consumer_policy["input_summary"])
    _assert_exact_keys(
        "Offline DashScope/Qwen consumer-decision input summary",
        input_summary,
        DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
    )
    if _assert_string("response-consumer input_summary.source_command", input_summary["source_command"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE:
        raise ValueError("Offline consumer-decision policy requires hermes_inventory as the source command.")
    if _assert_string("response-consumer input_summary.source_mode", input_summary["source_mode"]) != "inventory":
        raise ValueError("Offline consumer-decision policy requires inventory mode.")
    if not _assert_bool("response-consumer input_summary.source_dry_run", input_summary["source_dry_run"]):
        raise ValueError("Offline consumer-decision policy requires dry-run response-consumer input.")

    return consumer_policy


def _derive_decision_state(decision_inputs: dict[str, object]) -> tuple[str, bool, bool]:
    missing_evidence_fields = _assert_string_list(
        "decision_inputs.missing_evidence_fields",
        decision_inputs["missing_evidence_fields"],
    )
    unknown_evidence_references = _assert_string_list(
        "decision_inputs.unknown_evidence_references",
        decision_inputs["unknown_evidence_references"],
    )
    forbidden_content_flags = _assert_string_list(
        "decision_inputs.forbidden_content_flags",
        decision_inputs["forbidden_content_flags"],
    )
    source_of_truth_override_flag = _assert_bool(
        "decision_inputs.source_of_truth_override_flag",
        decision_inputs["source_of_truth_override_flag"],
    )
    migration_write_authorization_flag = _assert_bool(
        "decision_inputs.migration_write_authorization_flag",
        decision_inputs["migration_write_authorization_flag"],
    )
    ready_to_migrate_claim_flag = _assert_bool(
        "decision_inputs.ready_to_migrate_claim_flag",
        decision_inputs["ready_to_migrate_claim_flag"],
    )
    confidence_state = _assert_string("decision_inputs.confidence_state", decision_inputs["confidence_state"])
    required_human_review_flag = _assert_bool(
        "decision_inputs.required_human_review_flag",
        decision_inputs["required_human_review_flag"],
    )
    model_policy_status = _assert_string("decision_inputs.model_policy_status", decision_inputs["model_policy_status"])
    deterministic_mismatch_flag = _assert_bool(
        "decision_inputs.deterministic_mismatch_flag",
        decision_inputs["deterministic_mismatch_flag"],
    )

    reject_flags = set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS)
    policy_violation_flags = set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS)

    if source_of_truth_override_flag or "source_of_truth_override" in forbidden_content_flags:
        return "reject_unsafe", False, False
    if migration_write_authorization_flag or "migration_write_instructions" in forbidden_content_flags:
        return "reject_unsafe", False, False
    if ready_to_migrate_claim_flag or "ready_to_migrate_without_deterministic_gates" in forbidden_content_flags:
        return "reject_unsafe", False, False
    if any(flag in reject_flags for flag in forbidden_content_flags):
        return "reject_unsafe", False, False
    if any(flag in policy_violation_flags for flag in forbidden_content_flags):
        return "blocked_by_policy_violation", True, False
    if missing_evidence_fields:
        return "blocked_by_missing_evidence", False, False
    if unknown_evidence_references:
        return "requires_deterministic_recheck", False, True
    if deterministic_mismatch_flag:
        return "escalate_human_review", True, False
    if model_policy_status == "mismatch":
        return "escalate_human_review", True, False
    if confidence_state == "missing":
        return "requires_deterministic_recheck", False, True
    if confidence_state == "low":
        return "escalate_human_review", True, False
    if required_human_review_flag:
        return "escalate_human_review", True, False
    return "accept_explanatory_only", False, False


def _normalize_simulated_decision_example(index: int, candidate_example: dict[str, object] | object) -> dict[str, object]:
    example = _assert_json_object(f"Offline consumer-decision simulated example #{index + 1}", candidate_example)
    _assert_exact_keys(
        f"Offline consumer-decision simulated example #{index + 1}",
        example,
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS,
    )

    example_name = _assert_string(f"simulated example #{index + 1}.example_name", example["example_name"])
    decision_inputs = _assert_json_object(
        f"simulated example #{index + 1}.decision_inputs",
        example["decision_inputs"],
    )
    _assert_exact_keys(
        f"simulated example `{example_name}` decision_inputs",
        decision_inputs,
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    )

    evidence_validation_result = _assert_string(
        f"simulated example `{example_name}` decision_inputs.evidence_validation_result",
        decision_inputs["evidence_validation_result"],
    )
    if evidence_validation_result not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` has unsupported evidence validation result "
            f"`{evidence_validation_result}`."
        )

    missing_evidence_fields = _assert_string_list(
        f"simulated example `{example_name}` decision_inputs.missing_evidence_fields",
        decision_inputs["missing_evidence_fields"],
    )
    _assert_unique_strings(
        f"simulated example `{example_name}` missing_evidence_fields",
        missing_evidence_fields,
    )
    unsupported_missing_fields = [
        field
        for field in missing_evidence_fields
        if field not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE
    ]
    if unsupported_missing_fields:
        raise ValueError(
            "Offline consumer-decision simulated example `"
            + example_name
            + "` contains unsupported missing-evidence fields: "
            + ", ".join(unsupported_missing_fields)
            + "."
        )

    unknown_evidence_references = _assert_string_list(
        f"simulated example `{example_name}` decision_inputs.unknown_evidence_references",
        decision_inputs["unknown_evidence_references"],
    )
    _assert_unique_strings(
        f"simulated example `{example_name}` unknown_evidence_references",
        unknown_evidence_references,
    )

    forbidden_content_flags = _assert_string_list(
        f"simulated example `{example_name}` decision_inputs.forbidden_content_flags",
        decision_inputs["forbidden_content_flags"],
    )
    _assert_unique_strings(
        f"simulated example `{example_name}` forbidden_content_flags",
        forbidden_content_flags,
    )
    unsupported_forbidden_flags = [
        flag
        for flag in forbidden_content_flags
        if flag not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FORBIDDEN_FLAGS
    ]
    if unsupported_forbidden_flags:
        raise ValueError(
            "Offline consumer-decision simulated example `"
            + example_name
            + "` contains unsupported forbidden flags: "
            + ", ".join(unsupported_forbidden_flags)
            + "."
        )

    confidence_state = _assert_string(
        f"simulated example `{example_name}` decision_inputs.confidence_state",
        decision_inputs["confidence_state"],
    )
    if confidence_state not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` has unsupported confidence state `{confidence_state}`."
        )

    model_policy_status = _assert_string(
        f"simulated example `{example_name}` decision_inputs.model_policy_status",
        decision_inputs["model_policy_status"],
    )
    if model_policy_status not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_MODEL_POLICY_STATUSES:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` has unsupported model policy status `{model_policy_status}`."
        )

    deterministic_reference_categories = _assert_string_list(
        f"simulated example `{example_name}` decision_inputs.deterministic_reference_categories",
        decision_inputs["deterministic_reference_categories"],
    )
    _assert_unique_strings(
        f"simulated example `{example_name}` deterministic_reference_categories",
        deterministic_reference_categories,
    )
    unsupported_categories = [
        category
        for category in deterministic_reference_categories
        if category not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES
    ]
    if unsupported_categories:
        raise ValueError(
            "Offline consumer-decision simulated example `"
            + example_name
            + "` contains unsupported deterministic reference categories: "
            + ", ".join(unsupported_categories)
            + "."
        )

    expected_decision_state = _assert_string(
        f"simulated example `{example_name}` expected_decision_state",
        example["expected_decision_state"],
    )
    if expected_decision_state not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` has unsupported decision state `{expected_decision_state}`."
        )
    requires_human_review = _assert_bool(
        f"simulated example `{example_name}` requires_human_review",
        example["requires_human_review"],
    )
    requires_deterministic_recheck = _assert_bool(
        f"simulated example `{example_name}` requires_deterministic_recheck",
        example["requires_deterministic_recheck"],
    )
    decision_reason = _assert_string(
        f"simulated example `{example_name}` decision_reason",
        example["decision_reason"],
    )
    if not decision_reason.strip():
        raise ValueError(f"Offline consumer-decision simulated example `{example_name}` must include a decision_reason.")

    derived_state, derived_human_review, derived_recheck = _derive_decision_state(decision_inputs)
    if expected_decision_state != derived_state:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` expected `{expected_decision_state}` but the "
            f"governed decision rules classify it as `{derived_state}`."
        )
    if requires_human_review != derived_human_review:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` drifted on requires_human_review."
        )
    if requires_deterministic_recheck != derived_recheck:
        raise ValueError(
            f"Offline consumer-decision simulated example `{example_name}` drifted on requires_deterministic_recheck."
        )

    return {
        "example_name": example_name,
        "decision_inputs": {
            "evidence_validation_result": evidence_validation_result,
            "missing_evidence_fields": missing_evidence_fields,
            "unknown_evidence_references": unknown_evidence_references,
            "forbidden_content_flags": forbidden_content_flags,
            "source_of_truth_override_flag": _assert_bool(
                f"simulated example `{example_name}` decision_inputs.source_of_truth_override_flag",
                decision_inputs["source_of_truth_override_flag"],
            ),
            "migration_write_authorization_flag": _assert_bool(
                f"simulated example `{example_name}` decision_inputs.migration_write_authorization_flag",
                decision_inputs["migration_write_authorization_flag"],
            ),
            "ready_to_migrate_claim_flag": _assert_bool(
                f"simulated example `{example_name}` decision_inputs.ready_to_migrate_claim_flag",
                decision_inputs["ready_to_migrate_claim_flag"],
            ),
            "confidence_state": confidence_state,
            "required_human_review_flag": _assert_bool(
                f"simulated example `{example_name}` decision_inputs.required_human_review_flag",
                decision_inputs["required_human_review_flag"],
            ),
            "blocked_actions_present": _assert_bool(
                f"simulated example `{example_name}` decision_inputs.blocked_actions_present",
                decision_inputs["blocked_actions_present"],
            ),
            "deterministic_reference_categories": deterministic_reference_categories,
            "model_policy_status": model_policy_status,
            "deterministic_mismatch_flag": _assert_bool(
                f"simulated example `{example_name}` decision_inputs.deterministic_mismatch_flag",
                decision_inputs["deterministic_mismatch_flag"],
            ),
        },
        "expected_decision_state": expected_decision_state,
        "requires_human_review": requires_human_review,
        "requires_deterministic_recheck": requires_deterministic_recheck,
        "decision_reason": decision_reason,
    }


def sanitize_dashscope_consumer_decision_examples(
    candidate_examples: list[dict[str, object]] | None,
) -> list[dict[str, object]]:
    source_examples = (
        list(DASHSCOPE_OFFLINE_CONSUMER_DECISION_DEFAULT_SIMULATED_EXAMPLES)
        if candidate_examples is None
        else candidate_examples
    )
    if not isinstance(source_examples, list):
        raise ValueError("Offline consumer-decision simulated examples must be a list.")

    normalized_examples = [
        _normalize_simulated_decision_example(index, example)
        for index, example in enumerate(source_examples)
    ]
    _assert_unique_strings(
        "Offline consumer-decision simulated example names",
        [example["example_name"] for example in normalized_examples],
    )
    return normalized_examples


@dataclass(frozen=True)
class DashScopeOfflineConsumerDecisionPolicy:
    consumer_decision_policy_version: str
    decision_type: str
    source: str
    mode: str
    intended_model: str
    selected_model: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    local_config_ready: bool
    runtime_enabled: bool
    network_calls_allowed: bool
    qwen_dashscope_enabled: bool
    graphify_enabled: bool
    migration_writes_enabled: bool
    response_consumer_policy_version: str
    consumer_policy_type: str
    consumer_policy_mode: str
    response_explanatory_only: bool
    live_response_parsing_enabled: bool
    allowed_decision_states: tuple[str, ...]
    allowed_decision_inputs: tuple[str, ...]
    required_human_review_rules: dict[str, str]
    confidence_policy: dict[str, object]
    ready_to_migrate_claim_policy: dict[str, object]
    decision_authority_policy: dict[str, object]
    decision_examples_in_memory_only: bool
    simulated_decision_examples: tuple[dict[str, object], ...]
    redaction_policy: str
    input_summary: dict[str, object]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "consumer_decision_policy_version": self.consumer_decision_policy_version,
            "decision_type": self.decision_type,
            "source": self.source,
            "mode": self.mode,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "local_config_ready": self.local_config_ready,
            "runtime_enabled": self.runtime_enabled,
            "network_calls_allowed": self.network_calls_allowed,
            "qwen_dashscope_enabled": self.qwen_dashscope_enabled,
            "graphify_enabled": self.graphify_enabled,
            "migration_writes_enabled": self.migration_writes_enabled,
            "response_consumer_policy_version": self.response_consumer_policy_version,
            "consumer_policy_type": self.consumer_policy_type,
            "consumer_policy_mode": self.consumer_policy_mode,
            "response_explanatory_only": self.response_explanatory_only,
            "live_response_parsing_enabled": self.live_response_parsing_enabled,
            "allowed_decision_states": list(self.allowed_decision_states),
            "allowed_decision_inputs": list(self.allowed_decision_inputs),
            "required_human_review_rules": dict(self.required_human_review_rules),
            "confidence_policy": dict(self.confidence_policy),
            "ready_to_migrate_claim_policy": dict(self.ready_to_migrate_claim_policy),
            "decision_authority_policy": dict(self.decision_authority_policy),
            "decision_examples_in_memory_only": self.decision_examples_in_memory_only,
            "simulated_decision_examples": [dict(example) for example in self.simulated_decision_examples],
            "redaction_policy": self.redaction_policy,
            "input_summary": dict(self.input_summary),
        }


def build_hermes_qwen_offline_consumer_decision_policy(
    response_consumer_policy: DashScopeOfflineConsumerDecisionPolicy | dict[str, object] | object,
    *,
    candidate_examples: list[dict[str, object]] | None = None,
) -> DashScopeOfflineConsumerDecisionPolicy:
    consumer_policy_payload = _normalize_response_consumer_policy(response_consumer_policy)
    simulated_examples = sanitize_dashscope_consumer_decision_examples(candidate_examples)

    return DashScopeOfflineConsumerDecisionPolicy(
        consumer_decision_policy_version=DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION,
        decision_type=DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
        source=DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE,
        mode=DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
        intended_model=DASHSCOPE_INTENDED_MODEL,
        selected_model=_assert_string("response-consumer selected_model", consumer_policy_payload["selected_model"]),
        model_policy_status=_assert_string(
            "response-consumer model_policy_status",
            consumer_policy_payload["model_policy_status"],
        ),
        model_policy_ready=_assert_bool(
            "response-consumer model_policy_ready",
            consumer_policy_payload["model_policy_ready"],
        ),
        model_policy_requires_update=_assert_bool(
            "response-consumer model_policy_requires_update",
            consumer_policy_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool(
            "response-consumer local_config_ready",
            consumer_policy_payload["local_config_ready"],
        ),
        runtime_enabled=False,
        network_calls_allowed=False,
        qwen_dashscope_enabled=False,
        graphify_enabled=False,
        migration_writes_enabled=False,
        response_consumer_policy_version=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION,
        consumer_policy_type=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
        consumer_policy_mode=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
        response_explanatory_only=True,
        live_response_parsing_enabled=False,
        allowed_decision_states=DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
        allowed_decision_inputs=DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
        required_human_review_rules=DASHSCOPE_OFFLINE_CONSUMER_DECISION_REQUIRED_HUMAN_REVIEW_RULES,
        confidence_policy=DASHSCOPE_OFFLINE_CONSUMER_DECISION_CONFIDENCE_POLICY,
        ready_to_migrate_claim_policy=DASHSCOPE_OFFLINE_CONSUMER_DECISION_READY_TO_MIGRATE_CLAIM_POLICY,
        decision_authority_policy=DASHSCOPE_OFFLINE_CONSUMER_DECISION_AUTHORITY_POLICY,
        decision_examples_in_memory_only=True,
        simulated_decision_examples=tuple(simulated_examples),
        redaction_policy=_assert_string("response-consumer redaction_policy", consumer_policy_payload["redaction_policy"]),
        input_summary=_assert_json_object("response-consumer input_summary", consumer_policy_payload["input_summary"]),
    )
