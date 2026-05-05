from __future__ import annotations

from pathlib import Path

from workflow_manager.dashscope_env import (
    DASHSCOPE_ACTIVE_ENV_KEYS,
    DASHSCOPE_DISALLOWED_ENV_KEYS,
    DASHSCOPE_ENV_KEY_CATEGORIES,
    DASHSCOPE_FALLBACK_ONLY_ENV_KEYS,
    DASHSCOPE_FALLBACK_MODEL_ENV_KEYS,
    DASHSCOPE_GENERIC_API_KEY_POLICY,
    DASHSCOPE_IGNORED_ENV_KEYS,
    DASHSCOPE_INTENDED_MODEL,
    DASHSCOPE_LOCAL_ENV_KEYS,
    DASHSCOPE_MODEL_PRECEDENCE_POLICY,
    DASHSCOPE_MODEL_SELECTION_POLICY,
    DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS,
    DASHSCOPE_PRECEDENCE_POLICY,
    DASHSCOPE_REDACTED_VALUE,
    DASHSCOPE_RESERVED_ENV_KEYS,
    DashScopeLocalReadiness,
)

EXPECTED_ACTIVE_SECRET_ENV_KEYS = DASHSCOPE_ACTIVE_ENV_KEYS
EXPECTED_LOCAL_SECRET_ENV_KEYS = EXPECTED_ACTIVE_SECRET_ENV_KEYS
EXPECTED_GOVERNED_SECRET_ENV_KEYS = DASHSCOPE_LOCAL_ENV_KEYS
EXPECTED_FALLBACK_ONLY_SECRET_ENV_KEYS = DASHSCOPE_FALLBACK_ONLY_ENV_KEYS
EXPECTED_OPTIONAL_MODEL_ENV_KEYS = DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS
EXPECTED_FALLBACK_MODEL_ENV_KEYS = DASHSCOPE_FALLBACK_MODEL_ENV_KEYS
EXPECTED_RESERVED_SECRET_ENV_KEYS = DASHSCOPE_RESERVED_ENV_KEYS
EXPECTED_IGNORED_SECRET_ENV_KEYS = DASHSCOPE_IGNORED_ENV_KEYS
EXPECTED_DISALLOWED_SECRET_ENV_KEYS = DASHSCOPE_DISALLOWED_ENV_KEYS
EXPECTED_DASHSCOPE_ENV_KEY_CATEGORIES = DASHSCOPE_ENV_KEY_CATEGORIES
EXPECTED_DASHSCOPE_PRECEDENCE_POLICY = DASHSCOPE_PRECEDENCE_POLICY
EXPECTED_DASHSCOPE_GENERIC_API_KEY_POLICY = DASHSCOPE_GENERIC_API_KEY_POLICY
EXPECTED_DASHSCOPE_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_MODEL_PRECEDENCE_POLICY = DASHSCOPE_MODEL_PRECEDENCE_POLICY
EXPECTED_DASHSCOPE_MODEL_SELECTION_POLICY = DASHSCOPE_MODEL_SELECTION_POLICY
ALLOWED_MODEL_POLICY_STATUSES = ("default", "explicit-match", "fallback-match", "mismatch")
EXPECTED_ENV_IGNORE_PATTERNS = (".env", ".env.*", "!.env.example")
EXPECTED_ENV_EXAMPLE_VALUES = {
    "DASHSCOPE_API_KEY_WORKFLOW_MANAGER": "<set-locally>",
}
EXPECTED_ENV_EXAMPLE_NOTES = (
    "local-only",
    "DashScope",
    "does not make DashScope network calls",
)
EXPECTED_SECRET_SAFE_GENERATED_FILES = (
    "CLAUDE.md",
    "GEMINI.md",
    ".workflow/mirror-lock.json",
    ".specify/state/drift.md",
)
EXPECTED_DASHSCOPE_LOCAL_READINESS_KEYS = (
    "env_path",
    "env_exists",
    "expected_variable_names",
    "active_variable_names",
    "fallback_only_variable_names",
    "optional_model_variable_names",
    "fallback_model_variable_names",
    "reserved_variable_names",
    "ignored_variable_names",
    "disallowed_variable_names",
    "present_variable_names",
    "missing_variable_names",
    "present_model_variable_names",
    "missing_model_variable_names",
    "variable_categories",
    "non_empty_flags",
    "selected_api_key_name",
    "selected_api_key_category",
    "precedence_policy",
    "generic_api_key_policy",
    "intended_model_name",
    "selected_model_name",
    "selected_model_variable_name",
    "selected_model_variable_category",
    "model_precedence_policy",
    "model_selection_policy",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "redacted_values",
    "all_values_redacted",
    "local_config_ready",
    "runtime_enabled",
    "network_calls_allowed",
)


def _parse_env_assignments(path: Path) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        assignments[key.strip()] = value.strip()
    return assignments


def inspect_env_file_keys(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(_parse_env_assignments(path).keys())


def verify_dashscope_local_readiness_contract(readiness: DashScopeLocalReadiness | dict) -> dict:
    payload = readiness.to_safe_dict() if hasattr(readiness, "to_safe_dict") else dict(readiness)
    actual_keys = set(payload.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_LOCAL_READINESS_KEYS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope local readiness payload keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if payload["expected_variable_names"] != list(EXPECTED_ACTIVE_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed expected active variable names.")
    if payload["active_variable_names"] != list(EXPECTED_ACTIVE_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed active variable names.")
    if payload["fallback_only_variable_names"] != list(EXPECTED_FALLBACK_ONLY_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed fallback-only variable names.")
    if payload["optional_model_variable_names"] != list(EXPECTED_OPTIONAL_MODEL_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed optional model variable names.")
    if payload["fallback_model_variable_names"] != list(EXPECTED_FALLBACK_MODEL_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed fallback model variable names.")
    if payload["reserved_variable_names"] != list(EXPECTED_RESERVED_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed reserved variable names.")
    if payload["ignored_variable_names"] != list(EXPECTED_IGNORED_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed ignored variable names.")
    if payload["disallowed_variable_names"] != list(EXPECTED_DISALLOWED_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness must keep the governed disallowed variable names.")
    if not isinstance(payload["env_exists"], bool):
        raise AssertionError("DashScope local readiness.env_exists must be a boolean.")
    if not isinstance(payload["present_variable_names"], list) or not all(
        isinstance(item, str) for item in payload["present_variable_names"]
    ):
        raise AssertionError("DashScope local readiness.present_variable_names must be a list of strings.")
    if any(item not in EXPECTED_GOVERNED_SECRET_ENV_KEYS for item in payload["present_variable_names"]):
        raise AssertionError("DashScope local readiness.present_variable_names must stay within the governed key set.")
    expected_present_order = [
        key for key in EXPECTED_GOVERNED_SECRET_ENV_KEYS if key in set(payload["present_variable_names"])
    ]
    if payload["present_variable_names"] != expected_present_order:
        raise AssertionError("DashScope local readiness.present_variable_names must follow the governed precedence order.")
    if not isinstance(payload["missing_variable_names"], list) or not all(
        isinstance(item, str) for item in payload["missing_variable_names"]
    ):
        raise AssertionError("DashScope local readiness.missing_variable_names must be a list of strings.")
    if any(item not in EXPECTED_ACTIVE_SECRET_ENV_KEYS for item in payload["missing_variable_names"]):
        raise AssertionError("DashScope local readiness.missing_variable_names must stay within the governed active key set.")
    if not isinstance(payload["present_model_variable_names"], list) or not all(
        isinstance(item, str) for item in payload["present_model_variable_names"]
    ):
        raise AssertionError("DashScope local readiness.present_model_variable_names must be a list of strings.")
    expected_present_model_order = [
        key for key in (EXPECTED_OPTIONAL_MODEL_ENV_KEYS + EXPECTED_FALLBACK_MODEL_ENV_KEYS)
        if key in set(payload["present_model_variable_names"])
    ]
    if payload["present_model_variable_names"] != expected_present_model_order:
        raise AssertionError("DashScope local readiness.present_model_variable_names must follow the governed model precedence order.")
    if not isinstance(payload["missing_model_variable_names"], list) or not all(
        isinstance(item, str) for item in payload["missing_model_variable_names"]
    ):
        raise AssertionError("DashScope local readiness.missing_model_variable_names must be a list of strings.")
    expected_missing_model_order = [
        key for key in (EXPECTED_OPTIONAL_MODEL_ENV_KEYS + EXPECTED_FALLBACK_MODEL_ENV_KEYS)
        if key not in set(payload["present_model_variable_names"])
    ]
    if payload["missing_model_variable_names"] != expected_missing_model_order:
        raise AssertionError("DashScope local readiness.missing_model_variable_names must follow the governed model precedence order.")

    variable_categories = payload["variable_categories"]
    if not isinstance(variable_categories, dict):
        raise AssertionError("DashScope local readiness.variable_categories must be an object.")
    if variable_categories != EXPECTED_DASHSCOPE_ENV_KEY_CATEGORIES:
        raise AssertionError("DashScope local readiness.variable_categories drifted from the governed policy.")

    non_empty_flags = payload["non_empty_flags"]
    if not isinstance(non_empty_flags, dict):
        raise AssertionError("DashScope local readiness.non_empty_flags must be an object.")
    if set(non_empty_flags.keys()) != set(EXPECTED_GOVERNED_SECRET_ENV_KEYS):
        raise AssertionError("DashScope local readiness.non_empty_flags must cover the governed key set.")
    if not all(isinstance(value, bool) for value in non_empty_flags.values()):
        raise AssertionError("DashScope local readiness.non_empty_flags values must be booleans.")

    redacted_values = payload["redacted_values"]
    if not isinstance(redacted_values, dict):
        raise AssertionError("DashScope local readiness.redacted_values must be an object.")
    if not set(redacted_values.keys()).issubset(set(payload["present_variable_names"])):
        raise AssertionError("DashScope local readiness.redacted_values must only describe present keys.")
    if not all(value == DASHSCOPE_REDACTED_VALUE for value in redacted_values.values()):
        raise AssertionError("DashScope local readiness.redacted_values must stay fully redacted.")

    selected_api_key_name = payload["selected_api_key_name"]
    selected_api_key_category = payload["selected_api_key_category"]
    if selected_api_key_name is not None and selected_api_key_name not in EXPECTED_GOVERNED_SECRET_ENV_KEYS:
        raise AssertionError("DashScope local readiness.selected_api_key_name must stay within the governed key set.")
    if selected_api_key_category is not None and selected_api_key_category not in {"active", "fallback-only"}:
        raise AssertionError("DashScope local readiness.selected_api_key_category must stay policy-governed.")
    if selected_api_key_name is None and selected_api_key_category is not None:
        raise AssertionError("DashScope local readiness.selected_api_key_category requires a selected key name.")
    if selected_api_key_name is not None and variable_categories[selected_api_key_name] != selected_api_key_category:
        raise AssertionError("DashScope local readiness.selected_api_key_category drifted from the governed category map.")
    if payload["precedence_policy"] != EXPECTED_DASHSCOPE_PRECEDENCE_POLICY:
        raise AssertionError("DashScope local readiness.precedence_policy drifted from the governed rule.")
    if payload["generic_api_key_policy"] != EXPECTED_DASHSCOPE_GENERIC_API_KEY_POLICY:
        raise AssertionError("DashScope local readiness.generic_api_key_policy drifted from the governed rule.")
    if payload["intended_model_name"] != EXPECTED_DASHSCOPE_INTENDED_MODEL:
        raise AssertionError("DashScope local readiness.intended_model_name must keep the governed intended model.")
    if payload["model_precedence_policy"] != EXPECTED_DASHSCOPE_MODEL_PRECEDENCE_POLICY:
        raise AssertionError("DashScope local readiness.model_precedence_policy drifted from the governed rule.")
    if payload["model_selection_policy"] != EXPECTED_DASHSCOPE_MODEL_SELECTION_POLICY:
        raise AssertionError("DashScope local readiness.model_selection_policy drifted from the governed rule.")
    if payload["selected_model_variable_name"] is not None and payload["selected_model_variable_name"] not in (
        EXPECTED_OPTIONAL_MODEL_ENV_KEYS + EXPECTED_FALLBACK_MODEL_ENV_KEYS
    ):
        raise AssertionError("DashScope local readiness.selected_model_variable_name must stay within the governed model key set.")
    if payload["selected_model_variable_category"] is not None and payload["selected_model_variable_category"] not in {"optional", "fallback-only"}:
        raise AssertionError("DashScope local readiness.selected_model_variable_category must stay policy-governed.")
    if payload["selected_model_variable_name"] is None and payload["selected_model_variable_category"] is not None:
        raise AssertionError("DashScope local readiness.selected_model_variable_category requires a selected model variable.")
    if payload["selected_model_variable_name"] is not None and variable_categories[payload["selected_model_variable_name"]] != payload["selected_model_variable_category"]:
        raise AssertionError("DashScope local readiness.selected_model_variable_category drifted from the governed category map.")
    if payload["model_policy_status"] not in ALLOWED_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope local readiness.model_policy_status drifted from the governed policy states.")
    if not isinstance(payload["model_policy_ready"], bool):
        raise AssertionError("DashScope local readiness.model_policy_ready must be a boolean.")
    if not isinstance(payload["model_policy_requires_update"], bool):
        raise AssertionError("DashScope local readiness.model_policy_requires_update must be a boolean.")
    if payload["selected_model_variable_name"] is None:
        if payload["selected_model_name"] != EXPECTED_DASHSCOPE_INTENDED_MODEL:
            raise AssertionError("DashScope local readiness must use the governed intended model when no model env variable is present.")
        if payload["model_policy_status"] != "default" or payload["model_policy_ready"] is not True or payload["model_policy_requires_update"] is not False:
            raise AssertionError("DashScope local readiness default model-policy state drifted.")
    else:
        selected_model_name = payload["selected_model_name"]
        if selected_model_name == EXPECTED_DASHSCOPE_INTENDED_MODEL:
            expected_status = "explicit-match" if payload["selected_model_variable_name"] in EXPECTED_OPTIONAL_MODEL_ENV_KEYS else "fallback-match"
            if payload["model_policy_status"] != expected_status or payload["model_policy_ready"] is not True or payload["model_policy_requires_update"] is not False:
                raise AssertionError("DashScope local readiness matching model-variable policy drifted.")
        else:
            if payload["model_policy_status"] != "mismatch" or payload["model_policy_ready"] is not False or payload["model_policy_requires_update"] is not True:
                raise AssertionError("DashScope local readiness mismatch model-policy state drifted.")
    if payload["all_values_redacted"] is not True:
        raise AssertionError("DashScope local readiness.all_values_redacted must remain true.")
    if payload["runtime_enabled"] is not False:
        raise AssertionError("DashScope local readiness.runtime_enabled must remain false.")
    if payload["network_calls_allowed"] is not False:
        raise AssertionError("DashScope local readiness.network_calls_allowed must remain false.")

    expected_ready = (
        payload["env_exists"]
        and all(non_empty_flags[key] for key in EXPECTED_ACTIVE_SECRET_ENV_KEYS)
    )
    if payload["local_config_ready"] != expected_ready:
        raise AssertionError("DashScope local readiness.local_config_ready drifted from the governed boolean rule.")

    return payload


def verify_env_secret_hygiene_files(repo_root: Path) -> dict:
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        raise AssertionError("Secret hygiene guardrails require a repo-owned `.gitignore`.")

    ignore_lines = tuple(
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    for pattern in EXPECTED_ENV_IGNORE_PATTERNS:
        if pattern not in ignore_lines:
            raise AssertionError(f"`.gitignore` must include the secret-hygiene rule `{pattern}`.")

    env_example_path = repo_root / ".env.example"
    if not env_example_path.exists():
        raise AssertionError("Secret hygiene guardrails require a placeholder-only `.env.example`.")

    env_example_text = env_example_path.read_text(encoding="utf-8")
    env_example_assignments = _parse_env_assignments(env_example_path)
    if tuple(env_example_assignments.keys()) != EXPECTED_LOCAL_SECRET_ENV_KEYS:
        raise AssertionError(
            "`.env.example` must declare only the governed DashScope placeholder key set."
        )

    for key, expected_value in EXPECTED_ENV_EXAMPLE_VALUES.items():
        actual_value = env_example_assignments.get(key)
        if actual_value != expected_value:
            raise AssertionError(
                f"`.env.example` key `{key}` must keep the placeholder value `{expected_value}`."
            )

    env_example_text_lower = env_example_text.lower()
    for note in EXPECTED_ENV_EXAMPLE_NOTES:
        if note.lower() not in env_example_text_lower:
            raise AssertionError(f"`.env.example` must document `{note}`.")
    if (
        "DASHSCOPE_API_KEY" "=" in env_example_text
        or "QWEN_MODEL=" in env_example_text
        or "DASHSCOPE_MODEL=" in env_example_text
    ):
        raise AssertionError("`.env.example` must keep generic or future DashScope/Qwen keys as comments only.")

    return {
        "gitignore_path": gitignore_path,
        "ignored_patterns": list(EXPECTED_ENV_IGNORE_PATTERNS),
        "env_example_path": env_example_path,
        "env_example_keys": list(env_example_assignments.keys()),
        "env_example_values": dict(env_example_assignments),
    }


def assert_secret_absent_from_text(label: str, text: str, secret_value: str) -> None:
    if secret_value and secret_value in text:
        raise AssertionError(f"{label} must not include a raw secret value.")


def assert_secret_absent_from_path(path: Path, secret_value: str) -> None:
    if not path.exists():
        raise AssertionError(f"Expected generated file `{path}` to exist for secret-hygiene validation.")
    assert_secret_absent_from_text(str(path), path.read_text(encoding="utf-8"), secret_value)
