from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
from workflow_manager.dashscope_response_consumer import (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
)
from workflow_manager.dashscope_consumer_decision import (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_MODEL_POLICY_STATUSES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
)


DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_ESCALATION_TYPE = "acceptance_threshold_escalation_report_policy"
DASHSCOPE_OFFLINE_ESCALATION_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_ESCALATION_MODE = "offline_escalation_policy_only"
DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_FIELDS = (
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
)
DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES = (
    "explanatory_only_acceptance",
    "human_review_required",
    "deterministic_recheck_required",
    "unsafe_rejection",
    "missing_evidence_block",
    "policy_violation_block",
)
DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS = (
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
)
DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS = DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS
DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_HUMAN_REVIEW_RULES = {
    "reject_unsafe": "human_review_required",
    "blocked_by_policy_violation": "human_review_required",
    "escalate_human_review": "human_review_required",
    "low_confidence": "human_review_required",
    "deterministic_mismatch": "human_review_required",
    "model_policy_mismatch": "human_review_required",
}
DASHSCOPE_OFFLINE_ESCALATION_CONFIDENCE_MESSAGING_POLICY = {
    "confidence_is_advisory_only": True,
    "high_confidence_cannot_override_missing_evidence": True,
    "high_confidence_cannot_authorize_writes": True,
    "low_confidence_handling": "human_review_required",
    "missing_confidence_handling": "deterministic_recheck_required",
}
DASHSCOPE_OFFLINE_ESCALATION_BLOCKED_ACTION_SUMMARY_POLICY = {
    "summarize_only": True,
    "authorizes_target_repo_writes": False,
    "authorizes_migration_writes": False,
    "authorizes_report_writing": False,
    "authorizes_ready_to_migrate": False,
}
DASHSCOPE_OFFLINE_ESCALATION_READY_TO_MIGRATE_CLAIM_POLICY = {
    "deterministic_gates_required": True,
    "unauthorized_claim_handling": "block",
    "message_must_state_not_ready": True,
}
DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY = (
    "Deterministic Hermes inventory/status/doctor JSON remains the source of truth. Any future Qwen output and any "
    "downstream escalation wording are explanatory only, cannot authorize writes, cannot authorize migration, cannot "
    "authorize report writing, and cannot override deterministic classifications or readiness gates."
)
DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT = (
    "api-key values",
    ".env values",
    "raw secrets or partial secret fragments",
    "credentials",
    "tokens",
    "hidden reasoning or chain-of-thought",
    "live model response text",
    "network results",
    "arbitrary project source code",
    "target-repo file contents",
    "write-authorizing claims or instructions",
    "migration-write authorization",
    "ready-to-migrate authorization",
    "Graphify execution instructions",
    "report-writing instructions",
    "claims that Qwen output is source of truth",
)
DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_KEYS = (
    "example_name",
    "decision_inputs",
    "decision_state",
    "acceptance_threshold_category",
    "accepted_explanatory_only",
    "escalation_fields",
    "example_reason",
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


def _normalize_consumer_decision_policy(
    payload: dict[str, object] | object,
) -> dict[str, object]:
    decision_policy = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline DashScope/Qwen escalation consumer-decision policy",
        decision_policy,
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS,
    )

    if _assert_string("consumer-decision source", decision_policy["source"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE:
        raise ValueError("Offline escalation policy requires hermes_inventory consumer-decision input.")
    if _assert_string("consumer-decision mode", decision_policy["mode"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE:
        raise ValueError("Offline escalation policy requires offline_consumer_decision_policy_only mode.")
    if (
        _assert_string("consumer-decision version", decision_policy["consumer_decision_policy_version"])
        != DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION
    ):
        raise ValueError("Offline escalation policy received an unexpected consumer-decision policy version.")
    if _assert_string("consumer-decision type", decision_policy["decision_type"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE:
        raise ValueError("Offline escalation policy requires consumer_decision_human_review_policy input.")
    if _assert_string("consumer-decision intended_model", decision_policy["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline escalation policy requires the governed intended model.")
    if not _assert_bool("consumer-decision response_explanatory_only", decision_policy["response_explanatory_only"]):
        raise ValueError("Offline escalation policy requires response_explanatory_only=true.")
    if _assert_bool("consumer-decision live_response_parsing_enabled", decision_policy["live_response_parsing_enabled"]):
        raise ValueError("Offline escalation policy requires live_response_parsing_enabled=false.")
    if _assert_bool("consumer-decision runtime_enabled", decision_policy["runtime_enabled"]):
        raise ValueError("Offline escalation policy requires runtime_enabled=false.")
    if _assert_bool("consumer-decision network_calls_allowed", decision_policy["network_calls_allowed"]):
        raise ValueError("Offline escalation policy requires network_calls_allowed=false.")
    if _assert_bool("consumer-decision qwen_dashscope_enabled", decision_policy["qwen_dashscope_enabled"]):
        raise ValueError("Offline escalation policy requires qwen_dashscope_enabled=false.")
    if _assert_bool("consumer-decision graphify_enabled", decision_policy["graphify_enabled"]):
        raise ValueError("Offline escalation policy requires graphify_enabled=false.")
    if _assert_bool("consumer-decision migration_writes_enabled", decision_policy["migration_writes_enabled"]):
        raise ValueError("Offline escalation policy requires migration_writes_enabled=false.")

    input_summary = _assert_json_object("consumer-decision input_summary", decision_policy["input_summary"])
    _assert_exact_keys(
        "Offline DashScope/Qwen escalation input summary",
        input_summary,
        DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
    )
    if _assert_string("consumer-decision input_summary.source_command", input_summary["source_command"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE:
        raise ValueError("Offline escalation policy requires hermes_inventory as the source command.")
    if _assert_string("consumer-decision input_summary.source_mode", input_summary["source_mode"]) != "inventory":
        raise ValueError("Offline escalation policy requires inventory mode.")
    if not _assert_bool("consumer-decision input_summary.source_dry_run", input_summary["source_dry_run"]):
        raise ValueError("Offline escalation policy requires dry-run consumer-decision input.")

    return decision_policy


def _normalize_decision_inputs(label: str, value: object) -> dict[str, object]:
    decision_inputs = _assert_json_object(label, value)
    _assert_exact_keys(label, decision_inputs, DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS)

    evidence_validation_result = _assert_string(
        f"{label}.evidence_validation_result",
        decision_inputs["evidence_validation_result"],
    )
    if evidence_validation_result not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS:
        raise ValueError(f"{label}.evidence_validation_result has an unsupported value `{evidence_validation_result}`.")

    missing_evidence_fields = _assert_string_list(
        f"{label}.missing_evidence_fields",
        decision_inputs["missing_evidence_fields"],
    )
    _assert_unique_strings(f"{label}.missing_evidence_fields", missing_evidence_fields)
    unsupported_missing_fields = [
        field
        for field in missing_evidence_fields
        if field not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE
    ]
    if unsupported_missing_fields:
        raise ValueError(
            f"{label}.missing_evidence_fields contains unsupported fields: {unsupported_missing_fields}."
        )

    unknown_evidence_references = _assert_string_list(
        f"{label}.unknown_evidence_references",
        decision_inputs["unknown_evidence_references"],
    )
    _assert_unique_strings(f"{label}.unknown_evidence_references", unknown_evidence_references)

    forbidden_content_flags = _assert_string_list(
        f"{label}.forbidden_content_flags",
        decision_inputs["forbidden_content_flags"],
    )
    _assert_unique_strings(f"{label}.forbidden_content_flags", forbidden_content_flags)
    allowed_flags = set(
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS
        + DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS
    )
    unsupported_forbidden_flags = [
        flag
        for flag in forbidden_content_flags
        if flag not in allowed_flags
    ]
    if unsupported_forbidden_flags:
        raise ValueError(
            f"{label}.forbidden_content_flags contains unsupported flags: {unsupported_forbidden_flags}."
        )

    confidence_state = _assert_string(f"{label}.confidence_state", decision_inputs["confidence_state"])
    if confidence_state not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES:
        raise ValueError(f"{label}.confidence_state has an unsupported value `{confidence_state}`.")

    model_policy_status = _assert_string(f"{label}.model_policy_status", decision_inputs["model_policy_status"])
    if model_policy_status not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_MODEL_POLICY_STATUSES:
        raise ValueError(f"{label}.model_policy_status has an unsupported value `{model_policy_status}`.")

    deterministic_reference_categories = _assert_string_list(
        f"{label}.deterministic_reference_categories",
        decision_inputs["deterministic_reference_categories"],
    )
    _assert_unique_strings(f"{label}.deterministic_reference_categories", deterministic_reference_categories)
    unsupported_categories = [
        category
        for category in deterministic_reference_categories
        if category not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES
    ]
    if unsupported_categories:
        raise ValueError(
            f"{label}.deterministic_reference_categories contains unsupported categories: {unsupported_categories}."
        )

    return {
        "evidence_validation_result": evidence_validation_result,
        "missing_evidence_fields": missing_evidence_fields,
        "unknown_evidence_references": unknown_evidence_references,
        "forbidden_content_flags": forbidden_content_flags,
        "source_of_truth_override_flag": _assert_bool(
            f"{label}.source_of_truth_override_flag",
            decision_inputs["source_of_truth_override_flag"],
        ),
        "migration_write_authorization_flag": _assert_bool(
            f"{label}.migration_write_authorization_flag",
            decision_inputs["migration_write_authorization_flag"],
        ),
        "ready_to_migrate_claim_flag": _assert_bool(
            f"{label}.ready_to_migrate_claim_flag",
            decision_inputs["ready_to_migrate_claim_flag"],
        ),
        "confidence_state": confidence_state,
        "required_human_review_flag": _assert_bool(
            f"{label}.required_human_review_flag",
            decision_inputs["required_human_review_flag"],
        ),
        "blocked_actions_present": _assert_bool(
            f"{label}.blocked_actions_present",
            decision_inputs["blocked_actions_present"],
        ),
        "deterministic_reference_categories": deterministic_reference_categories,
        "model_policy_status": model_policy_status,
        "deterministic_mismatch_flag": _assert_bool(
            f"{label}.deterministic_mismatch_flag",
            decision_inputs["deterministic_mismatch_flag"],
        ),
    }


def _derive_consumer_decision_state(decision_inputs: dict[str, object]) -> tuple[str, bool, bool]:
    missing_evidence_fields = list(decision_inputs["missing_evidence_fields"])
    unknown_evidence_references = list(decision_inputs["unknown_evidence_references"])
    forbidden_content_flags = list(decision_inputs["forbidden_content_flags"])
    source_of_truth_override_flag = bool(decision_inputs["source_of_truth_override_flag"])
    migration_write_authorization_flag = bool(decision_inputs["migration_write_authorization_flag"])
    ready_to_migrate_claim_flag = bool(decision_inputs["ready_to_migrate_claim_flag"])
    confidence_state = str(decision_inputs["confidence_state"])
    required_human_review_flag = bool(decision_inputs["required_human_review_flag"])
    model_policy_status = str(decision_inputs["model_policy_status"])
    deterministic_mismatch_flag = bool(decision_inputs["deterministic_mismatch_flag"])

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


def _derive_acceptance_threshold_category(decision_state: str) -> str:
    mapping = {
        "accept_explanatory_only": "explanatory_only_acceptance",
        "escalate_human_review": "human_review_required",
        "requires_deterministic_recheck": "deterministic_recheck_required",
        "reject_unsafe": "unsafe_rejection",
        "blocked_by_missing_evidence": "missing_evidence_block",
        "blocked_by_policy_violation": "policy_violation_block",
    }
    return mapping[decision_state]


def _derive_blocked_reason(decision_state: str, decision_inputs: dict[str, object]) -> str:
    forbidden_flags = set(decision_inputs["forbidden_content_flags"])

    if decision_inputs["source_of_truth_override_flag"] or "source_of_truth_override" in forbidden_flags:
        return "source-of-truth-override"
    if decision_inputs["migration_write_authorization_flag"] or "migration_write_instructions" in forbidden_flags:
        return "migration-write-authorization"
    if decision_inputs["ready_to_migrate_claim_flag"] or "ready_to_migrate_without_deterministic_gates" in forbidden_flags:
        return "ready-to-migrate-claim-without-deterministic-gates"
    if "hidden_reasoning" in forbidden_flags or "chain_of_thought" in forbidden_flags:
        return "hidden-reasoning-or-chain-of-thought"
    if forbidden_flags.intersection({"api_key_material", "raw_env", "env_values", "credentials", "tokens"}):
        return "secret-like-content"
    if forbidden_flags.intersection({"project_source_code", "target_repo_file_contents"}):
        return "target-repo-or-source-content"
    if forbidden_flags.intersection(set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS)):
        return "policy-violation"
    if decision_inputs["missing_evidence_fields"]:
        return "missing-deterministic-evidence"
    if decision_inputs["unknown_evidence_references"]:
        return "unknown-evidence-reference"
    if decision_inputs["deterministic_mismatch_flag"]:
        return "deterministic-mismatch"
    if decision_inputs["model_policy_status"] == "mismatch":
        return "model-policy-mismatch"
    if decision_inputs["confidence_state"] == "missing":
        return "missing-confidence"
    if decision_inputs["confidence_state"] == "low":
        return "low-confidence"
    if decision_state == "accept_explanatory_only":
        return "explanatory-only-acceptance"
    return "human-review-required"


def _derive_blocked_actions_summary(decision_inputs: dict[str, object]) -> str:
    if decision_inputs["blocked_actions_present"]:
        return (
            "Blocked actions remain blocked. Do not authorize target-repo writes, migration writes, ready-to-migrate "
            "claims, Graphify actions, or report writing."
        )
    return (
        "No additional blocked actions were surfaced. This message still cannot authorize target-repo writes, "
        "migration writes, ready-to-migrate claims, Graphify actions, or report writing."
    )


def _derive_allowed_human_message(
    decision_state: str,
    decision_inputs: dict[str, object],
    example_reason: str,
) -> str:
    if decision_state == "accept_explanatory_only":
        prefix = "Accept only as explanatory output."
    elif decision_state == "blocked_by_missing_evidence":
        prefix = "Blocked pending deterministic recheck because deterministic evidence is missing."
    elif decision_state == "blocked_by_policy_violation":
        prefix = "Blocked for policy violation and escalate to human review."
    elif decision_state == "reject_unsafe":
        prefix = "Blocked as unsafe and escalate to human review."
    elif decision_state == "requires_deterministic_recheck":
        prefix = "Do not accept. Deterministic recheck is required before trust."
    else:
        prefix = "Do not accept. Human review is required before trust."

    confidence_note = ""
    if decision_inputs["confidence_state"] == "low":
        confidence_note = " Low confidence stays advisory only."
    elif decision_inputs["confidence_state"] == "missing":
        confidence_note = " Missing confidence requires deterministic recheck."

    return (
        f"{prefix} {example_reason}{confidence_note} Deterministic Hermes inventory/status/doctor data remains the "
        "source of truth. Do not authorize writes, migration, Graphify actions, or report writing from this message."
    )


def _derive_escalation_fields(decision_state: str, decision_inputs: dict[str, object], example_reason: str) -> dict[str, object]:
    human_review_required = decision_state in {
        "reject_unsafe",
        "blocked_by_policy_violation",
        "escalate_human_review",
    }
    deterministic_recheck_required = decision_state in {
        "blocked_by_missing_evidence",
        "requires_deterministic_recheck",
    }
    blocked = decision_state in {
        "reject_unsafe",
        "blocked_by_missing_evidence",
        "blocked_by_policy_violation",
    }
    return {
        "decision_state": decision_state,
        "human_review_required": human_review_required,
        "deterministic_recheck_required": deterministic_recheck_required,
        "blocked": blocked,
        "blocked_reason": _derive_blocked_reason(decision_state, decision_inputs),
        "evidence_status": str(decision_inputs["evidence_validation_result"]),
        "confidence_status": str(decision_inputs["confidence_state"]),
        "blocked_actions_summary": _derive_blocked_actions_summary(decision_inputs),
        "allowed_human_message": _derive_allowed_human_message(decision_state, decision_inputs, example_reason),
        "forbidden_message_content": list(DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT),
        "source_of_truth_policy": DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
        "redaction_policy": (
            "Keep API-key values, .env values, raw secrets, partial secret fragments, source code, target-repo file "
            f"contents, and live model text out of escalation messages while keeping {DASHSCOPE_INTENDED_MODEL} explicit "
            "as non-secret intended model metadata."
        ),
        "report_writing_enabled": False,
        "runtime_enabled": False,
        "network_calls_allowed": False,
        "live_response_parsing_enabled": False,
    }


def _normalize_source_decision_example(index: int, candidate_example: dict[str, object] | object) -> dict[str, object]:
    example = _assert_json_object(f"Offline escalation source decision example #{index + 1}", candidate_example)
    _assert_exact_keys(
        f"Offline escalation source decision example #{index + 1}",
        example,
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS,
    )

    example_name = _assert_string(
        f"source decision example #{index + 1}.example_name",
        example["example_name"],
    )
    decision_inputs = _normalize_decision_inputs(
        f"source decision example `{example_name}` decision_inputs",
        example["decision_inputs"],
    )
    expected_decision_state = _assert_string(
        f"source decision example `{example_name}` expected_decision_state",
        example["expected_decision_state"],
    )
    if expected_decision_state not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES:
        raise ValueError(
            f"Offline escalation source decision example `{example_name}` has unsupported decision state "
            f"`{expected_decision_state}`."
        )
    requires_human_review = _assert_bool(
        f"source decision example `{example_name}` requires_human_review",
        example["requires_human_review"],
    )
    requires_deterministic_recheck = _assert_bool(
        f"source decision example `{example_name}` requires_deterministic_recheck",
        example["requires_deterministic_recheck"],
    )
    decision_reason = _assert_string(
        f"source decision example `{example_name}` decision_reason",
        example["decision_reason"],
    )
    if not decision_reason.strip():
        raise ValueError(f"Offline escalation source decision example `{example_name}` must include a decision_reason.")

    derived_state, derived_human_review, derived_recheck = _derive_consumer_decision_state(decision_inputs)
    if expected_decision_state != derived_state:
        raise ValueError(
            f"Offline escalation source decision example `{example_name}` expected `{expected_decision_state}` but the "
            f"governed decision rules classify it as `{derived_state}`."
        )
    if requires_human_review != derived_human_review:
        raise ValueError(
            f"Offline escalation source decision example `{example_name}` drifted on requires_human_review."
        )
    if requires_deterministic_recheck != derived_recheck:
        raise ValueError(
            f"Offline escalation source decision example `{example_name}` drifted on requires_deterministic_recheck."
        )

    return {
        "example_name": example_name,
        "decision_inputs": decision_inputs,
        "expected_decision_state": expected_decision_state,
        "requires_human_review": requires_human_review,
        "requires_deterministic_recheck": requires_deterministic_recheck,
        "decision_reason": decision_reason,
    }


def _build_escalation_example_from_decision_example(source_example: dict[str, object]) -> dict[str, object]:
    decision_state = str(source_example["expected_decision_state"])
    decision_inputs = dict(source_example["decision_inputs"])
    example_reason = str(source_example["decision_reason"])
    return {
        "example_name": str(source_example["example_name"]),
        "decision_inputs": decision_inputs,
        "decision_state": decision_state,
        "acceptance_threshold_category": _derive_acceptance_threshold_category(decision_state),
        "accepted_explanatory_only": decision_state == "accept_explanatory_only",
        "escalation_fields": _derive_escalation_fields(decision_state, decision_inputs, example_reason),
        "example_reason": example_reason,
    }


def _normalize_escalation_example(index: int, candidate_example: dict[str, object] | object) -> dict[str, object]:
    example = _assert_json_object(f"Offline escalation simulated example #{index + 1}", candidate_example)
    _assert_exact_keys(
        f"Offline escalation simulated example #{index + 1}",
        example,
        DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_KEYS,
    )

    example_name = _assert_string(
        f"simulated escalation example #{index + 1}.example_name",
        example["example_name"],
    )
    example_reason = _assert_string(
        f"simulated escalation example `{example_name}` example_reason",
        example["example_reason"],
    )
    if not example_reason.strip():
        raise ValueError(f"Offline escalation simulated example `{example_name}` must include an example_reason.")

    decision_inputs = _normalize_decision_inputs(
        f"simulated escalation example `{example_name}` decision_inputs",
        example["decision_inputs"],
    )
    decision_state = _assert_string(
        f"simulated escalation example `{example_name}` decision_state",
        example["decision_state"],
    )
    if decision_state not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES:
        raise ValueError(
            f"Offline escalation simulated example `{example_name}` has unsupported decision_state `{decision_state}`."
        )

    derived_decision_state, _, _ = _derive_consumer_decision_state(decision_inputs)
    if decision_state != derived_decision_state:
        raise ValueError(
            f"Offline escalation simulated example `{example_name}` expected decision_state `{decision_state}` but the "
            f"governed decision rules classify it as `{derived_decision_state}`."
        )

    acceptance_threshold_category = _assert_string(
        f"simulated escalation example `{example_name}` acceptance_threshold_category",
        example["acceptance_threshold_category"],
    )
    expected_category = _derive_acceptance_threshold_category(decision_state)
    if acceptance_threshold_category != expected_category:
        raise ValueError(
            f"Offline escalation simulated example `{example_name}` expected acceptance_threshold_category "
            f"`{acceptance_threshold_category}` but the governed escalation rules classify it as `{expected_category}`."
        )

    accepted_explanatory_only = _assert_bool(
        f"simulated escalation example `{example_name}` accepted_explanatory_only",
        example["accepted_explanatory_only"],
    )
    expected_accepted = decision_state == "accept_explanatory_only"
    if accepted_explanatory_only != expected_accepted:
        raise ValueError(
            f"Offline escalation simulated example `{example_name}` drifted on accepted_explanatory_only."
        )

    escalation_fields = _assert_json_object(
        f"simulated escalation example `{example_name}` escalation_fields",
        example["escalation_fields"],
    )
    _assert_exact_keys(
        f"simulated escalation example `{example_name}` escalation_fields",
        escalation_fields,
        DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
    )

    expected_fields = _derive_escalation_fields(decision_state, decision_inputs, example_reason)
    if escalation_fields != expected_fields:
        raise ValueError(
            f"Offline escalation simulated example `{example_name}` drifted from the governed escalation-field rules."
        )

    return {
        "example_name": example_name,
        "decision_inputs": decision_inputs,
        "decision_state": decision_state,
        "acceptance_threshold_category": acceptance_threshold_category,
        "accepted_explanatory_only": accepted_explanatory_only,
        "escalation_fields": expected_fields,
        "example_reason": example_reason,
    }


def sanitize_dashscope_escalation_examples(
    source_decision_examples: list[dict[str, object]],
    candidate_examples: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    normalized_source_examples = [
        _normalize_source_decision_example(index, example)
        for index, example in enumerate(source_decision_examples)
    ]
    _assert_unique_strings(
        "Offline escalation source decision example names",
        [example["example_name"] for example in normalized_source_examples],
    )

    if candidate_examples is None:
        return [
            _build_escalation_example_from_decision_example(example)
            for example in normalized_source_examples
        ]

    if not isinstance(candidate_examples, list):
        raise ValueError("Offline escalation simulated examples must be a list.")

    normalized_examples = [
        _normalize_escalation_example(index, example)
        for index, example in enumerate(candidate_examples)
    ]
    _assert_unique_strings(
        "Offline escalation simulated example names",
        [example["example_name"] for example in normalized_examples],
    )
    return normalized_examples


@dataclass(frozen=True)
class DashScopeOfflineEscalationPolicy:
    escalation_policy_version: str
    escalation_type: str
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
    report_writing_enabled: bool
    consumer_decision_policy_version: str
    decision_type: str
    decision_mode: str
    response_explanatory_only: bool
    live_response_parsing_enabled: bool
    allowed_acceptance_threshold_categories: tuple[str, ...]
    allowed_escalation_fields: tuple[str, ...]
    required_escalation_fields: tuple[str, ...]
    required_human_review_rules: dict[str, str]
    confidence_messaging_policy: dict[str, object]
    blocked_action_summary_policy: dict[str, object]
    ready_to_migrate_claim_policy: dict[str, object]
    source_of_truth_policy: str
    forbidden_message_content: tuple[str, ...]
    redaction_policy: str
    escalation_examples_in_memory_only: bool
    simulated_escalation_examples: tuple[dict[str, object], ...]
    input_summary: dict[str, object]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "escalation_policy_version": self.escalation_policy_version,
            "escalation_type": self.escalation_type,
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
            "report_writing_enabled": self.report_writing_enabled,
            "consumer_decision_policy_version": self.consumer_decision_policy_version,
            "decision_type": self.decision_type,
            "decision_mode": self.decision_mode,
            "response_explanatory_only": self.response_explanatory_only,
            "live_response_parsing_enabled": self.live_response_parsing_enabled,
            "allowed_acceptance_threshold_categories": list(self.allowed_acceptance_threshold_categories),
            "allowed_escalation_fields": list(self.allowed_escalation_fields),
            "required_escalation_fields": list(self.required_escalation_fields),
            "required_human_review_rules": dict(self.required_human_review_rules),
            "confidence_messaging_policy": dict(self.confidence_messaging_policy),
            "blocked_action_summary_policy": dict(self.blocked_action_summary_policy),
            "ready_to_migrate_claim_policy": dict(self.ready_to_migrate_claim_policy),
            "source_of_truth_policy": self.source_of_truth_policy,
            "forbidden_message_content": list(self.forbidden_message_content),
            "redaction_policy": self.redaction_policy,
            "escalation_examples_in_memory_only": self.escalation_examples_in_memory_only,
            "simulated_escalation_examples": [dict(example) for example in self.simulated_escalation_examples],
            "input_summary": dict(self.input_summary),
        }


def build_hermes_qwen_offline_escalation_policy(
    consumer_decision_policy: dict[str, object] | object,
    *,
    candidate_examples: list[dict[str, object]] | None = None,
) -> DashScopeOfflineEscalationPolicy:
    decision_policy_payload = _normalize_consumer_decision_policy(consumer_decision_policy)
    simulated_escalation_examples = sanitize_dashscope_escalation_examples(
        [
            _assert_json_object("consumer-decision simulated_decision_examples[]", example)
            for example in decision_policy_payload["simulated_decision_examples"]
        ],
        candidate_examples,
    )

    return DashScopeOfflineEscalationPolicy(
        escalation_policy_version=DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION,
        escalation_type=DASHSCOPE_OFFLINE_ESCALATION_TYPE,
        source=DASHSCOPE_OFFLINE_ESCALATION_SOURCE,
        mode=DASHSCOPE_OFFLINE_ESCALATION_MODE,
        intended_model=DASHSCOPE_INTENDED_MODEL,
        selected_model=_assert_string("consumer-decision selected_model", decision_policy_payload["selected_model"]),
        model_policy_status=_assert_string(
            "consumer-decision model_policy_status",
            decision_policy_payload["model_policy_status"],
        ),
        model_policy_ready=_assert_bool(
            "consumer-decision model_policy_ready",
            decision_policy_payload["model_policy_ready"],
        ),
        model_policy_requires_update=_assert_bool(
            "consumer-decision model_policy_requires_update",
            decision_policy_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool(
            "consumer-decision local_config_ready",
            decision_policy_payload["local_config_ready"],
        ),
        runtime_enabled=False,
        network_calls_allowed=False,
        qwen_dashscope_enabled=False,
        graphify_enabled=False,
        migration_writes_enabled=False,
        report_writing_enabled=False,
        consumer_decision_policy_version=DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION,
        decision_type=DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
        decision_mode=DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
        response_explanatory_only=True,
        live_response_parsing_enabled=False,
        allowed_acceptance_threshold_categories=DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
        allowed_escalation_fields=DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
        required_escalation_fields=DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS,
        required_human_review_rules=DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_HUMAN_REVIEW_RULES,
        confidence_messaging_policy=DASHSCOPE_OFFLINE_ESCALATION_CONFIDENCE_MESSAGING_POLICY,
        blocked_action_summary_policy=DASHSCOPE_OFFLINE_ESCALATION_BLOCKED_ACTION_SUMMARY_POLICY,
        ready_to_migrate_claim_policy=DASHSCOPE_OFFLINE_ESCALATION_READY_TO_MIGRATE_CLAIM_POLICY,
        source_of_truth_policy=DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
        forbidden_message_content=DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT,
        redaction_policy=_assert_string("consumer-decision redaction_policy", decision_policy_payload["redaction_policy"]),
        escalation_examples_in_memory_only=True,
        simulated_escalation_examples=tuple(simulated_escalation_examples),
        input_summary=_assert_json_object("consumer-decision input_summary", decision_policy_payload["input_summary"]),
    )
