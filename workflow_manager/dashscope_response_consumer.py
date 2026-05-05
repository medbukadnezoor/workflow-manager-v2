from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
from workflow_manager.dashscope_response import (
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_SOURCE,
    DASHSCOPE_OFFLINE_RESPONSE_TYPE,
)


DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE = "evidence_slot_response_consumer_policy"
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE = "offline_response_consumer_policy_only"
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS = (
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
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES = (
    "hermes_inventory_summary",
    "hermes_classification_counts",
    "hermes_root_classification_counts",
    "hermes_warning_count",
    "hermes_error_count",
    "status_health_overview",
    "doctor_result_status",
    "roots_health",
    "manifest_health",
    "mirror_lock_shim_health",
    "continuity_state_health",
    "memory_health",
    "command_help_docs_health",
    "json_contract_policy",
    "dashscope_readiness_policy",
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE = (
    "risk_summary",
    "recommended_next_step",
    "required_human_review",
    "blocked_actions",
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_REQUIRED_EVIDENCE_RULES = {
    "analysis_summary": "May be explanatory, but must not invent facts or override deterministic Hermes evidence.",
    "risk_summary": "Must include at least one deterministic evidence reference.",
    "recommended_next_step": "Must include at least one deterministic evidence reference.",
    "required_human_review": "Any human-review requirement must cite deterministic evidence.",
    "blocked_actions": "Must be grounded in deterministic safety flags, governed policies, or explicit health findings.",
}
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FORBIDDEN_EVIDENCE_REFERENCES = (
    "api-key values",
    ".env values",
    "raw secrets",
    "partial secret prefixes or suffixes",
    "credentials",
    "tokens",
    "hidden reasoning or chain-of-thought",
    "target-repo file contents",
    "project source code",
    "generated shim contents",
    "memory or state file bodies",
    "full AGENTS/CLAUDE/GEMINI contents from target repos",
    "arbitrary local file paths outside governed metadata",
    "claims that Qwen output is source of truth",
    "claims that migration writes are authorized",
    "claims that a repo is ready to migrate without deterministic gates",
    "write-capable shell commands",
    "Graphify execution instructions",
    "report-writing instructions",
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY_KEYS = (
    "deterministic_hermes_data_is_source_of_truth",
    "qwen_output_is_explanatory_only",
    "source_of_truth_override_handling",
    "migration_write_authorization_handling",
    "classification_change_handling",
    "invented_evidence_reference_handling",
    "missing_evidence_handling",
    "uncertainty_handling",
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY = {
    "deterministic_hermes_data_is_source_of_truth": True,
    "qwen_output_is_explanatory_only": True,
    "source_of_truth_override_handling": "reject",
    "migration_write_authorization_handling": "reject",
    "classification_change_handling": "reject",
    "invented_evidence_reference_handling": "reject",
    "missing_evidence_handling": "reject",
    "uncertainty_handling": "preserve-explicitly",
}
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_UNGROUNDED_RECOMMENDATION_POLICY = (
    "Reject recommendations, blocked actions, and human-review requirements when deterministic evidence references are "
    "missing, unknown, or replaced with explanatory-only text."
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_UNCERTAINTY_POLICY = (
    "Preserve uncertainty explicitly, do not invent evidence references, do not treat missing evidence as proof, and "
    "do not change deterministic Hermes classifications based on Qwen text."
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_KEYS = (
    "example_name",
    "grounding_status",
    "expected_consumer_action",
    "response_fields_present",
    "evidence_references",
    "invalid_evidence_references",
    "forbidden_or_unexpected_fields",
    "consumer_reason",
)
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EXAMPLE_ACTIONS = ("accept", "reject")
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_GROUNDING_STATUSES = ("grounded", "ungrounded")
DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_DEFAULT_SIMULATED_EXAMPLES: tuple[dict[str, object], ...] = (
    {
        "example_name": "valid_grounded_explanatory_response",
        "grounding_status": "grounded",
        "expected_consumer_action": "accept",
        "response_fields_present": [
            "analysis_summary",
            "risk_summary",
            "recommended_next_step",
            "blocked_actions",
            "required_human_review",
            "confidence",
        ],
        "evidence_references": {
            "risk_summary": ["hermes_warning_count"],
            "recommended_next_step": ["status_health_overview"],
            "required_human_review": ["doctor_result_status"],
            "blocked_actions": ["dashscope_readiness_policy"],
        },
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": [],
        "consumer_reason": (
            "Accept as explanatory-only because every governed recommendation field is grounded in deterministic evidence."
        ),
    },
    {
        "example_name": "missing_evidence_for_recommendation",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["recommended_next_step"],
        "evidence_references": {},
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": [],
        "consumer_reason": "Reject because recommended_next_step lacks deterministic evidence references.",
    },
    {
        "example_name": "unknown_evidence_reference",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["risk_summary"],
        "evidence_references": {},
        "invalid_evidence_references": ["repo_text_body"],
        "forbidden_or_unexpected_fields": [],
        "consumer_reason": "Reject because repo_text_body is not a governed deterministic evidence reference.",
    },
    {
        "example_name": "source_of_truth_override_claim",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["source_of_truth_policy"],
        "evidence_references": {},
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["source_of_truth_override"],
        "consumer_reason": "Reject because explanatory Qwen output cannot override deterministic Hermes classifications.",
    },
    {
        "example_name": "migration_write_authorization",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["blocked_actions"],
        "evidence_references": {
            "blocked_actions": ["dashscope_readiness_policy"],
        },
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["migration_write_instructions"],
        "consumer_reason": "Reject because migration-write authorization is out of scope for explanatory-only output.",
    },
    {
        "example_name": "target_repo_modification_instruction",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["blocked_actions"],
        "evidence_references": {
            "blocked_actions": ["dashscope_readiness_policy"],
        },
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["target_repo_modification_instructions"],
        "consumer_reason": "Reject because target-repo modification instructions remain blocked.",
    },
    {
        "example_name": "hidden_reasoning_output",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["analysis_summary"],
        "evidence_references": {},
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["hidden_reasoning"],
        "consumer_reason": "Reject because hidden reasoning or chain-of-thought output is forbidden.",
    },
    {
        "example_name": "secret_like_content",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["redaction_policy"],
        "evidence_references": {},
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["api_key_material"],
        "consumer_reason": "Reject because secret-like content must never enter the governed consumer path.",
    },
    {
        "example_name": "target_repo_file_contents",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["analysis_summary"],
        "evidence_references": {},
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["target_repo_file_contents"],
        "consumer_reason": "Reject because target-repo file contents are not governed deterministic evidence.",
    },
    {
        "example_name": "unsafe_extra_field",
        "grounding_status": "ungrounded",
        "expected_consumer_action": "reject",
        "response_fields_present": ["analysis_summary"],
        "evidence_references": {},
        "invalid_evidence_references": [],
        "forbidden_or_unexpected_fields": ["response_notes"],
        "consumer_reason": "Reject because extra response fields are outside the governed output slots.",
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


def _normalize_response_shape(payload: DashScopeOfflineResponseConsumerPolicy | dict[str, object] | object) -> dict[str, object]:
    response_shape = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline DashScope/Qwen response-consumer policy response shape",
        response_shape,
        DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS,
    )

    if _assert_string("response shape source", response_shape["source"]) != DASHSCOPE_OFFLINE_RESPONSE_SOURCE:
        raise ValueError("Offline response-consumer policy requires hermes_inventory response-shape input.")
    if _assert_string("response shape mode", response_shape["mode"]) != DASHSCOPE_OFFLINE_RESPONSE_MODE:
        raise ValueError("Offline response-consumer policy requires offline_response_shape_only mode.")
    if _assert_string("response shape version", response_shape["response_shape_version"]) != DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION:
        raise ValueError("Offline response-consumer policy received an unexpected response-shape version.")
    if _assert_string("response shape type", response_shape["response_type"]) != DASHSCOPE_OFFLINE_RESPONSE_TYPE:
        raise ValueError("Offline response-consumer policy requires explanatory_response_shape input.")
    if _assert_string("response shape intended_model", response_shape["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline response-consumer policy requires the governed intended model.")
    if not _assert_bool("response shape response_explanatory_only", response_shape["response_explanatory_only"]):
        raise ValueError("Offline response-consumer policy requires response_explanatory_only=true.")
    if _assert_bool("response shape live_response_parsing_enabled", response_shape["live_response_parsing_enabled"]):
        raise ValueError("Offline response-consumer policy requires live_response_parsing_enabled=false.")
    if _assert_bool("response shape runtime_enabled", response_shape["runtime_enabled"]):
        raise ValueError("Offline response-consumer policy requires runtime_enabled=false.")
    if _assert_bool("response shape network_calls_allowed", response_shape["network_calls_allowed"]):
        raise ValueError("Offline response-consumer policy requires network_calls_allowed=false.")
    if _assert_bool("response shape qwen_dashscope_enabled", response_shape["qwen_dashscope_enabled"]):
        raise ValueError("Offline response-consumer policy requires qwen_dashscope_enabled=false.")
    if _assert_bool("response shape graphify_enabled", response_shape["graphify_enabled"]):
        raise ValueError("Offline response-consumer policy requires graphify_enabled=false.")
    if _assert_bool("response shape migration_writes_enabled", response_shape["migration_writes_enabled"]):
        raise ValueError("Offline response-consumer policy requires migration_writes_enabled=false.")

    response_fields = _assert_string_list("response shape allowed_response_fields", response_shape["allowed_response_fields"])
    if tuple(response_fields) != DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS:
        raise ValueError("Offline response-consumer policy received drifted allowed response fields.")
    required_fields = _assert_string_list("response shape required_response_fields", response_shape["required_response_fields"])
    if tuple(required_fields) != DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS:
        raise ValueError("Offline response-consumer policy received drifted required response fields.")

    input_summary = _assert_json_object("response shape input_summary", response_shape["input_summary"])
    _assert_exact_keys(
        "Offline DashScope/Qwen response-consumer policy input summary",
        input_summary,
        DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
    )
    if _assert_string("response shape input_summary.source_command", input_summary["source_command"]) != DASHSCOPE_OFFLINE_RESPONSE_SOURCE:
        raise ValueError("Offline response-consumer policy requires hermes_inventory as the source command.")
    if _assert_string("response shape input_summary.source_mode", input_summary["source_mode"]) != "inventory":
        raise ValueError("Offline response-consumer policy requires inventory mode.")
    if not _assert_bool("response shape input_summary.source_dry_run", input_summary["source_dry_run"]):
        raise ValueError("Offline response-consumer policy requires dry-run response-shape input.")

    return response_shape


def _normalize_simulated_example(index: int, candidate_example: dict[str, object] | object) -> dict[str, object]:
    example = _assert_json_object(f"Offline response-consumer simulated example #{index + 1}", candidate_example)
    _assert_exact_keys(
        f"Offline response-consumer simulated example #{index + 1}",
        example,
        DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_KEYS,
    )

    example_name = _assert_string(f"simulated example #{index + 1}.example_name", example["example_name"])
    grounding_status = _assert_string(
        f"simulated example #{index + 1}.grounding_status",
        example["grounding_status"],
    )
    if grounding_status not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_GROUNDING_STATUSES:
        raise ValueError(
            f"Offline response-consumer simulated example `{example_name}` has unsupported grounding status `{grounding_status}`."
        )

    expected_consumer_action = _assert_string(
        f"simulated example #{index + 1}.expected_consumer_action",
        example["expected_consumer_action"],
    )
    if expected_consumer_action not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EXAMPLE_ACTIONS:
        raise ValueError(
            f"Offline response-consumer simulated example `{example_name}` has unsupported consumer action `{expected_consumer_action}`."
        )

    response_fields_present = _assert_string_list(
        f"simulated example #{index + 1}.response_fields_present",
        example["response_fields_present"],
    )
    _assert_unique_strings(f"simulated example `{example_name}` response_fields_present", response_fields_present)
    unexpected_response_fields = [
        field for field in response_fields_present if field not in DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS
    ]
    if unexpected_response_fields:
        raise ValueError(
            "Offline response-consumer simulated example `"
            + example_name
            + "` contains unsupported response fields: "
            + ", ".join(unexpected_response_fields)
            + "."
        )

    evidence_references_payload = _assert_json_object(
        f"simulated example #{index + 1}.evidence_references",
        example["evidence_references"],
    )
    normalized_evidence_references: dict[str, list[str]] = {}
    for field_name, references_value in evidence_references_payload.items():
        if field_name not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE:
            raise ValueError(
                "Offline response-consumer simulated example `"
                + example_name
                + "` uses evidence references for unsupported field `"
                + field_name
                + "`."
            )
        if field_name not in response_fields_present:
            raise ValueError(
                "Offline response-consumer simulated example `"
                + example_name
                + "` cites evidence for field `"
                + field_name
                + "` without including that field in response_fields_present."
            )
        references = _assert_string_list(
            f"simulated example #{index + 1}.evidence_references.{field_name}",
            references_value,
        )
        if not references:
            raise ValueError(
                f"Offline response-consumer simulated example `{example_name}` must not use empty evidence reference lists."
            )
        _assert_unique_strings(f"simulated example `{example_name}` evidence references for `{field_name}`", references)
        unknown_references = [
            reference
            for reference in references
            if reference not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES
        ]
        if unknown_references:
            raise ValueError(
                "Offline response-consumer simulated example `"
                + example_name
                + "` contains unknown evidence references: "
                + ", ".join(unknown_references)
                + "."
            )
        normalized_evidence_references[field_name] = references

    invalid_evidence_references = _assert_string_list(
        f"simulated example #{index + 1}.invalid_evidence_references",
        example["invalid_evidence_references"],
    )
    _assert_unique_strings(f"simulated example `{example_name}` invalid_evidence_references", invalid_evidence_references)
    misplaced_valid_references = [
        reference
        for reference in invalid_evidence_references
        if reference in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES
    ]
    if misplaced_valid_references:
        raise ValueError(
            "Offline response-consumer simulated example `"
            + example_name
            + "` lists governed evidence references as invalid: "
            + ", ".join(misplaced_valid_references)
            + "."
        )

    forbidden_or_unexpected_fields = _assert_string_list(
        f"simulated example #{index + 1}.forbidden_or_unexpected_fields",
        example["forbidden_or_unexpected_fields"],
    )
    _assert_unique_strings(
        f"simulated example `{example_name}` forbidden_or_unexpected_fields",
        forbidden_or_unexpected_fields,
    )
    misplaced_allowed_fields = [
        field for field in forbidden_or_unexpected_fields if field in DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS
    ]
    if misplaced_allowed_fields:
        raise ValueError(
            "Offline response-consumer simulated example `"
            + example_name
            + "` misclassifies allowed response fields as forbidden/unexpected: "
            + ", ".join(misplaced_allowed_fields)
            + "."
        )

    consumer_reason = _assert_string(f"simulated example #{index + 1}.consumer_reason", example["consumer_reason"])
    missing_required_evidence_fields = [
        field
        for field in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE
        if field in response_fields_present and field not in normalized_evidence_references
    ]
    rejection_triggers = []
    if grounding_status == "ungrounded":
        rejection_triggers.append("ungrounded")
    if missing_required_evidence_fields:
        rejection_triggers.append("missing-required-evidence")
    if invalid_evidence_references:
        rejection_triggers.append("invalid-evidence-reference")
    if forbidden_or_unexpected_fields:
        rejection_triggers.append("forbidden-or-unexpected-field")

    if expected_consumer_action == "accept" and rejection_triggers:
        details = []
        if missing_required_evidence_fields:
            details.append(
                "missing deterministic evidence references for: "
                + ", ".join(missing_required_evidence_fields)
            )
        if invalid_evidence_references:
            details.append(
                "invalid evidence references: "
                + ", ".join(invalid_evidence_references)
            )
        if forbidden_or_unexpected_fields:
            details.append(
                "forbidden or unexpected fields: "
                + ", ".join(forbidden_or_unexpected_fields)
            )
        if grounding_status == "ungrounded":
            details.append("grounding status is ungrounded")
        raise ValueError(
            "Offline response-consumer simulated example `"
            + example_name
            + "` cannot be accepted because it includes rejection triggers: "
            + "; ".join(details)
            + "."
        )
    if expected_consumer_action == "reject" and not rejection_triggers:
        raise ValueError(
            f"Offline response-consumer simulated example `{example_name}` must include a rejection trigger."
        )

    return {
        "example_name": example_name,
        "grounding_status": grounding_status,
        "expected_consumer_action": expected_consumer_action,
        "response_fields_present": response_fields_present,
        "evidence_references": normalized_evidence_references,
        "invalid_evidence_references": invalid_evidence_references,
        "forbidden_or_unexpected_fields": forbidden_or_unexpected_fields,
        "consumer_reason": consumer_reason,
    }


def sanitize_dashscope_response_consumer_examples(
    candidate_examples: list[dict[str, object]] | None,
) -> list[dict[str, object]]:
    source_examples = list(DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_DEFAULT_SIMULATED_EXAMPLES) if candidate_examples is None else candidate_examples
    if not isinstance(source_examples, list):
        raise ValueError("Offline DashScope/Qwen response-consumer simulated examples must be a list of objects.")

    normalized = [
        _normalize_simulated_example(index, example)
        for index, example in enumerate(source_examples)
    ]
    if not normalized:
        raise ValueError("Offline DashScope/Qwen response-consumer policy requires at least one simulated example.")

    example_names = [example["example_name"] for example in normalized]
    _assert_unique_strings("Offline response-consumer simulated example names", example_names)
    return normalized


@dataclass(frozen=True)
class DashScopeOfflineResponseConsumerPolicy:
    response_consumer_policy_version: str
    consumer_type: str
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
    response_shape_version: str
    response_type: str
    response_mode: str
    response_explanatory_only: bool
    live_response_parsing_enabled: bool
    allowed_evidence_reference_categories: tuple[str, ...]
    response_fields_requiring_evidence: tuple[str, ...]
    required_evidence_rules: dict[str, str]
    forbidden_evidence_references: tuple[str, ...]
    consumer_authority_policy: dict[str, object]
    ungrounded_recommendation_policy: str
    uncertainty_policy: str
    simulated_examples_in_memory_only: bool
    simulated_examples: list[dict[str, object]]
    redaction_policy: str
    input_summary: dict[str, object]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "response_consumer_policy_version": self.response_consumer_policy_version,
            "consumer_type": self.consumer_type,
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
            "response_shape_version": self.response_shape_version,
            "response_type": self.response_type,
            "response_mode": self.response_mode,
            "response_explanatory_only": self.response_explanatory_only,
            "live_response_parsing_enabled": self.live_response_parsing_enabled,
            "allowed_evidence_reference_categories": list(self.allowed_evidence_reference_categories),
            "response_fields_requiring_evidence": list(self.response_fields_requiring_evidence),
            "required_evidence_rules": dict(self.required_evidence_rules),
            "forbidden_evidence_references": list(self.forbidden_evidence_references),
            "consumer_authority_policy": dict(self.consumer_authority_policy),
            "ungrounded_recommendation_policy": self.ungrounded_recommendation_policy,
            "uncertainty_policy": self.uncertainty_policy,
            "simulated_examples_in_memory_only": self.simulated_examples_in_memory_only,
            "simulated_examples": [
                {
                    "example_name": example["example_name"],
                    "grounding_status": example["grounding_status"],
                    "expected_consumer_action": example["expected_consumer_action"],
                    "response_fields_present": list(example["response_fields_present"]),
                    "evidence_references": {
                        key: list(value) for key, value in example["evidence_references"].items()
                    },
                    "invalid_evidence_references": list(example["invalid_evidence_references"]),
                    "forbidden_or_unexpected_fields": list(example["forbidden_or_unexpected_fields"]),
                    "consumer_reason": example["consumer_reason"],
                }
                for example in self.simulated_examples
            ],
            "redaction_policy": self.redaction_policy,
            "input_summary": dict(self.input_summary),
        }


def build_hermes_qwen_offline_response_consumer_policy(
    response_shape: DashScopeOfflineResponseConsumerPolicy | dict[str, object] | object,
    *,
    candidate_examples: list[dict[str, object]] | None = None,
) -> DashScopeOfflineResponseConsumerPolicy:
    response_payload = _normalize_response_shape(response_shape)
    simulated_examples = sanitize_dashscope_response_consumer_examples(candidate_examples)

    return DashScopeOfflineResponseConsumerPolicy(
        response_consumer_policy_version=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION,
        consumer_type=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
        source=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE,
        mode=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
        intended_model=_assert_string("response shape intended_model", response_payload["intended_model"]),
        selected_model=_assert_string("response shape selected_model", response_payload["selected_model"]),
        model_policy_status=_assert_string("response shape model_policy_status", response_payload["model_policy_status"]),
        model_policy_ready=_assert_bool("response shape model_policy_ready", response_payload["model_policy_ready"]),
        model_policy_requires_update=_assert_bool(
            "response shape model_policy_requires_update",
            response_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool("response shape local_config_ready", response_payload["local_config_ready"]),
        runtime_enabled=False,
        network_calls_allowed=False,
        qwen_dashscope_enabled=False,
        graphify_enabled=False,
        migration_writes_enabled=False,
        response_shape_version=_assert_string(
            "response shape response_shape_version",
            response_payload["response_shape_version"],
        ),
        response_type=_assert_string("response shape response_type", response_payload["response_type"]),
        response_mode=_assert_string("response shape mode", response_payload["mode"]),
        response_explanatory_only=True,
        live_response_parsing_enabled=False,
        allowed_evidence_reference_categories=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
        response_fields_requiring_evidence=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
        required_evidence_rules=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_REQUIRED_EVIDENCE_RULES,
        forbidden_evidence_references=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FORBIDDEN_EVIDENCE_REFERENCES,
        consumer_authority_policy=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY,
        ungrounded_recommendation_policy=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_UNGROUNDED_RECOMMENDATION_POLICY,
        uncertainty_policy=DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_UNCERTAINTY_POLICY,
        simulated_examples_in_memory_only=True,
        simulated_examples=simulated_examples,
        redaction_policy=_assert_string("response shape redaction_policy", response_payload["redaction_policy"]),
        input_summary=_assert_json_object("response shape input_summary", response_payload["input_summary"]),
    )
