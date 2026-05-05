from __future__ import annotations

import json
from pathlib import Path


EXPECTED_HERMES_PREFLIGHT_JSON_SCHEMA_VERSION = "1.0.0"
EXPECTED_HERMES_PREFLIGHT_JSON_COMMAND = "hermes_preflight"
EXPECTED_HERMES_PREFLIGHT_JSON_MODE = "preflight"
EXPECTED_HERMES_PREFLIGHT_JSON_KEYS = (
    "schema_version",
    "command",
    "mode",
    "dry_run",
    "roots_config_path",
    "summary",
    "roots_info",
    "readiness_counts",
    "roots",
    "warnings",
    "errors",
    "target_repos_modified",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
    "report_writing_enabled",
    "target_repo_file_bodies_read",
)
EXPECTED_HERMES_PREFLIGHT_ROOTS_INFO_KEYS = (
    "configured_root_count",
    "usable_root_count",
    "missing_root_count",
    "invalid_root_count",
    "project_count",
)
EXPECTED_HERMES_PREFLIGHT_READINESS_KEYS = ("ready", "needs_review", "blocked")
EXPECTED_HERMES_PREFLIGHT_ROOT_KEYS = (
    "path",
    "classification",
    "exists",
    "is_directory",
    "project_count",
    "issues",
    "projects",
)
EXPECTED_HERMES_PREFLIGHT_PROJECT_KEYS = (
    "name",
    "path",
    "root",
    "scaffold_classification",
    "automation_readiness",
    "migration_track",
    "migration_risk",
    "git",
    "detected_flags",
    "blocking_reasons",
    "warnings",
    "next_safe_action",
)
EXPECTED_HERMES_PREFLIGHT_GIT_KEYS = (
    "is_git_repo",
    "is_dirty",
    "status",
    "dirty_path_count",
    "blocks_future_apply",
)
ALLOWED_HERMES_PREFLIGHT_ROOT_CLASSIFICATIONS = {
    "configured-root",
    "missing-root",
    "invalid-root",
}
ALLOWED_HERMES_PREFLIGHT_SCAFFOLD_CLASSIFICATIONS = {
    "v2",
    "legacy",
    "mixed",
    "unmanaged",
    "error",
}
ALLOWED_HERMES_PREFLIGHT_READINESS = {"ready", "needs_review", "blocked"}
ALLOWED_HERMES_PREFLIGHT_MIGRATION_RISK = {"low", "medium", "high"}
ALLOWED_HERMES_PREFLIGHT_GIT_STATUSES = {"clean", "dirty", "not-git"}


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


def verify_hermes_preflight_json_payload(
    payload: object,
    *,
    expected_roots_config_path: Path | None = None,
) -> dict:
    payload = _assert_json_object("Hermes preflight payload", payload)
    _assert_exact_keys("Hermes preflight payload", payload, EXPECTED_HERMES_PREFLIGHT_JSON_KEYS)

    if _assert_string("Hermes preflight payload.schema_version", payload["schema_version"]) != EXPECTED_HERMES_PREFLIGHT_JSON_SCHEMA_VERSION:
        raise AssertionError("Hermes preflight payload.schema_version drifted.")
    if _assert_string("Hermes preflight payload.command", payload["command"]) != EXPECTED_HERMES_PREFLIGHT_JSON_COMMAND:
        raise AssertionError("Hermes preflight payload.command drifted.")
    if _assert_string("Hermes preflight payload.mode", payload["mode"]) != EXPECTED_HERMES_PREFLIGHT_JSON_MODE:
        raise AssertionError("Hermes preflight payload.mode drifted.")
    if _assert_bool("Hermes preflight payload.dry_run", payload["dry_run"]) is not True:
        raise AssertionError("Hermes preflight payload.dry_run must remain true.")

    roots_config_path = payload["roots_config_path"]
    if roots_config_path is not None and not isinstance(roots_config_path, str):
        raise AssertionError("Hermes preflight payload.roots_config_path must be a string or null.")
    if expected_roots_config_path is not None and roots_config_path != str(expected_roots_config_path.resolve()):
        raise AssertionError("Hermes preflight payload.roots_config_path drifted.")

    _assert_string("Hermes preflight payload.summary", payload["summary"])
    roots_info = _assert_json_object("Hermes preflight payload.roots_info", payload["roots_info"])
    _assert_exact_keys("Hermes preflight payload.roots_info", roots_info, EXPECTED_HERMES_PREFLIGHT_ROOTS_INFO_KEYS)
    for key in EXPECTED_HERMES_PREFLIGHT_ROOTS_INFO_KEYS:
        _assert_integer(f"Hermes preflight payload.roots_info.{key}", roots_info[key])

    readiness_counts = _assert_json_object(
        "Hermes preflight payload.readiness_counts",
        payload["readiness_counts"],
    )
    _assert_exact_keys(
        "Hermes preflight payload.readiness_counts",
        readiness_counts,
        EXPECTED_HERMES_PREFLIGHT_READINESS_KEYS,
    )
    for key in EXPECTED_HERMES_PREFLIGHT_READINESS_KEYS:
        _assert_integer(f"Hermes preflight payload.readiness_counts.{key}", readiness_counts[key])

    _assert_string_list("Hermes preflight payload.warnings", payload["warnings"])
    _assert_string_list("Hermes preflight payload.errors", payload["errors"])
    for key in (
        "target_repos_modified",
        "qwen_dashscope_enabled",
        "graphify_enabled",
        "migration_writes_enabled",
        "report_writing_enabled",
        "target_repo_file_bodies_read",
    ):
        if _assert_bool(f"Hermes preflight payload.{key}", payload[key]) is not False:
            raise AssertionError(f"Hermes preflight payload.{key} must remain false.")

    roots = payload["roots"]
    if not isinstance(roots, list):
        raise AssertionError("Hermes preflight payload.roots must be a list.")
    root_paths: list[str] = []
    for root in roots:
        root_payload = _assert_json_object("Hermes preflight root payload", root)
        _assert_exact_keys("Hermes preflight root payload", root_payload, EXPECTED_HERMES_PREFLIGHT_ROOT_KEYS)
        root_path = _assert_string("Hermes preflight root payload.path", root_payload["path"])
        root_paths.append(root_path)
        root_classification = _assert_string(
            "Hermes preflight root payload.classification",
            root_payload["classification"],
        )
        if root_classification not in ALLOWED_HERMES_PREFLIGHT_ROOT_CLASSIFICATIONS:
            raise AssertionError("Hermes preflight root classification vocabulary drifted.")
        _assert_bool("Hermes preflight root payload.exists", root_payload["exists"])
        _assert_bool("Hermes preflight root payload.is_directory", root_payload["is_directory"])
        _assert_integer("Hermes preflight root payload.project_count", root_payload["project_count"])
        _assert_string_list("Hermes preflight root payload.issues", root_payload["issues"])
        projects = root_payload["projects"]
        if not isinstance(projects, list):
            raise AssertionError("Hermes preflight root payload.projects must be a list.")
        if root_payload["project_count"] != len(projects):
            raise AssertionError("Hermes preflight root payload.project_count must match projects length.")
        project_order: list[tuple[str, str]] = []
        for project in projects:
            project_payload = _assert_json_object("Hermes preflight project payload", project)
            _assert_exact_keys(
                "Hermes preflight project payload",
                project_payload,
                EXPECTED_HERMES_PREFLIGHT_PROJECT_KEYS,
            )
            project_name = _assert_string("Hermes preflight project payload.name", project_payload["name"])
            project_path = _assert_string("Hermes preflight project payload.path", project_payload["path"])
            project_order.append((project_name, project_path))
            if _assert_string("Hermes preflight project payload.root", project_payload["root"]) != root_path:
                raise AssertionError("Hermes preflight project payload.root must match parent root.")
            if _assert_string(
                "Hermes preflight project payload.scaffold_classification",
                project_payload["scaffold_classification"],
            ) not in ALLOWED_HERMES_PREFLIGHT_SCAFFOLD_CLASSIFICATIONS:
                raise AssertionError("Hermes preflight project scaffold classification vocabulary drifted.")
            readiness = _assert_string(
                "Hermes preflight project payload.automation_readiness",
                project_payload["automation_readiness"],
            )
            if readiness not in ALLOWED_HERMES_PREFLIGHT_READINESS:
                raise AssertionError("Hermes preflight automation readiness vocabulary drifted.")
            _assert_string("Hermes preflight project payload.migration_track", project_payload["migration_track"])
            if _assert_string(
                "Hermes preflight project payload.migration_risk",
                project_payload["migration_risk"],
            ) not in ALLOWED_HERMES_PREFLIGHT_MIGRATION_RISK:
                raise AssertionError("Hermes preflight migration risk vocabulary drifted.")
            git = _assert_json_object("Hermes preflight project payload.git", project_payload["git"])
            _assert_exact_keys("Hermes preflight project payload.git", git, EXPECTED_HERMES_PREFLIGHT_GIT_KEYS)
            is_git = _assert_bool("Hermes preflight project payload.git.is_git_repo", git["is_git_repo"])
            is_dirty = _assert_bool("Hermes preflight project payload.git.is_dirty", git["is_dirty"])
            git_status = _assert_string("Hermes preflight project payload.git.status", git["status"])
            if git_status not in ALLOWED_HERMES_PREFLIGHT_GIT_STATUSES:
                raise AssertionError("Hermes preflight git status vocabulary drifted.")
            _assert_integer("Hermes preflight project payload.git.dirty_path_count", git["dirty_path_count"])
            blocks = _assert_bool(
                "Hermes preflight project payload.git.blocks_future_apply",
                git["blocks_future_apply"],
            )
            if git_status == "not-git" and (is_git or is_dirty or not blocks):
                raise AssertionError("not-git must block future apply without marking dirty.")
            if git_status == "dirty" and (not is_git or not is_dirty or not blocks):
                raise AssertionError("dirty git must block future apply.")
            _assert_string_list("Hermes preflight project payload.detected_flags", project_payload["detected_flags"])
            _assert_string_list("Hermes preflight project payload.blocking_reasons", project_payload["blocking_reasons"])
            _assert_string_list("Hermes preflight project payload.warnings", project_payload["warnings"])
            _assert_string("Hermes preflight project payload.next_safe_action", project_payload["next_safe_action"])
        if project_order != sorted(project_order):
            raise AssertionError("Hermes preflight projects must be ordered by name/path.")
    if root_paths != sorted(root_paths):
        raise AssertionError("Hermes preflight roots must be ordered by path.")
    return payload


def verify_hermes_preflight_json_stdout(
    stdout: str,
    *,
    expected_roots_config_path: Path | None = None,
) -> dict:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Hermes preflight stdout must be valid JSON: {exc}") from exc
    return verify_hermes_preflight_json_payload(
        payload,
        expected_roots_config_path=expected_roots_config_path,
    )
