#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable

from workflow_manager.dashscope_connectivity import (
    DASHSCOPE_CONNECTIVITY_MODE,
    DASHSCOPE_CONNECTIVITY_REQUEST_BODY_KIND,
    DASHSCOPE_CONNECTIVITY_REQUEST_METHOD,
    DashScopeConnectivityProbeResult,
    DashScopeConnectivityTransport,
    probe_dashscope_connectivity,
)
from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL, inspect_dashscope_local_readiness
from workflow_manager.docs_health import DocsHealth, evaluate_docs_health
from workflow_manager.role_contract import (
    CANONICAL_ROLES,
    RESERVED_ROLES,
    ROLE_ACTION_CATEGORIES,
    ROLE_CONTRACT_SOURCE,
    SUPPORTED_ROLE_CONTRACT_HARNESSES,
    validate_role_contract_payload,
)


WORKFLOW_SCHEMA_VERSION = "2.0.0"
MIRROR_LOCK_SCHEMA_VERSION = "1.0.0"
ROOTS_CONFIG_SCHEMA_VERSION = "1.0.0"
GENERATED_FORMAT_VERSION = "workflow-managed-v1"
MACHINE_OUTPUT_SCHEMA_VERSION = "1.2.0"
HERMES_INVENTORY_SCHEMA_VERSION = "1.0.0"
HERMES_PREFLIGHT_SCHEMA_VERSION = "1.0.0"
HERMES_ANALYSIS_SCHEMA_VERSION = "1.0.0"
HERMES_QWEN_PREVIEW_SCHEMA_VERSION = "1.0.0"
HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS = 700
HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS = 3500
HERMES_QWEN_PREVIEW_MAX_EVIDENCE_CATEGORIES = 16
DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION = "1.0.0"
DEFAULT_CANONICAL_CONTRACT = "AGENTS.md"
GENERATED_ROLE_SHIMS = ["ROLES.md"]
DEFAULT_MEMORY_ROOT = ".specify/memory"
DEFAULT_STATE_ROOT = ".specify/state"
DEFAULT_LEGACY_ROOT = ".ai"

MANAGED_START = "<!-- workflow-managed:start -->"
MANAGED_END = "<!-- workflow-managed:end -->"
UNMANAGED_START = "<!-- workflow-unmanaged:start -->"
UNMANAGED_END = "<!-- workflow-unmanaged:end -->"

REQUIRED_MEMORY_FILES = [
    "constitution.md",
    "project.md",
    "decisions.md",
    "architecture.md",
    "tech.md",
]

MEMORY_FILES = [
    "constitution.md",
    "project.md",
    "decisions.md",
    "architecture.md",
    "tech.md",
]

REQUIRED_STATE_FILES = [
    "active.md",
    "handoff.md",
    "progress.md",
    "session.log.md",
    "drift.md",
    "migration.md",
]

CONTINUITY_STATE_FILES = [
    "active.md",
    "handoff.md",
    "progress.md",
    "session.log.md",
    "migration.md",
]

SHIMS = {
    "CLAUDE.md": "Claude Code",
    "GEMINI.md": "Gemini CLI",
}

GEMINI_ADAPTERS_ROOT = ".gemini/agents"
CLAUDE_ADAPTERS_ROOT = ".claude/agents"
OPENCODE_ADAPTERS_ROOT = ".opencode/agents"
DROID_ADAPTERS_ROOT = ".factory/droids"


def _ai_skills_capabilities_root() -> Path:
    override = os.environ.get("WORKFLOW_AI_SKILLS_CAPABILITIES_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "capabilities"


AI_SKILLS_CAPABILITIES_ROOT = _ai_skills_capabilities_root()

MANAGED_CLAUDE_ADAPTERS = {
    f"{CLAUDE_ADAPTERS_ROOT}/architect.md": {
        "name": "architect",
        "description": "Use for read-only planning and orchestration. Produces bounded tickets without editing code.",
        "tools": "Read, Grep, Glob, LS",
        "role": "Architect",
    },
    f"{CLAUDE_ADAPTERS_ROOT}/coder.md": {
        "name": "coder",
        "description": "Use for implementing approved tickets, editing files, and running required checks.",
        "tools": "Read, Grep, Glob, LS, Edit, MultiEdit, Write, Bash",
        "role": "Coder",
    },
    f"{CLAUDE_ADAPTERS_ROOT}/verifier.md": {
        "name": "verifier",
        "description": "Use for read-only verification, diff review, and running tests without writing patches.",
        "tools": "Read, Grep, Glob, LS, Bash",
        "role": "Verifier",
    },
}

MANAGED_OPENCODE_ADAPTERS = {
    f"{OPENCODE_ADAPTERS_ROOT}/architect.md": {
        "description": "Use for read-only planning and orchestration. Produces bounded tickets without editing code.",
        "mode": "subagent",
        "role": "Architect",
        "permission": {
            "edit": "deny",
            "bash": "deny",
            "webfetch": "deny",
        },
    },
    f"{OPENCODE_ADAPTERS_ROOT}/coder.md": {
        "description": "Use for implementing approved tickets, editing files, and running required checks.",
        "mode": "subagent",
        "role": "Coder",
        "permission": {
            "edit": "ask",
            "bash": "ask",
            "webfetch": "deny",
        },
    },
    f"{OPENCODE_ADAPTERS_ROOT}/verifier.md": {
        "description": "Use for read-only verification, diff review, and running tests without writing patches.",
        "mode": "subagent",
        "role": "Verifier",
        "permission": {
            "edit": "deny",
            "bash": "ask",
            "webfetch": "deny",
        },
    },
}

MANAGED_DROID_ADAPTERS = {
    f"{DROID_ADAPTERS_ROOT}/architect.md": {
        "name": "architect",
        "description": "Product droid for read-only planning and orchestration. Produces bounded tickets without editing code.",
        "model": "inherit",
        "tools": "read-only",
        "role": "Architect",
        "droid_type": "Product",
    },
    f"{DROID_ADAPTERS_ROOT}/coder.md": {
        "name": "coder",
        "description": "Code droid for implementing approved tickets, editing files, and running required checks.",
        "model": "inherit",
        "tools": '["Read", "LS", "Grep", "Glob", "Create", "Edit", "ApplyPatch", "Execute"]',
        "role": "Coder",
        "droid_type": "Code",
    },
    f"{DROID_ADAPTERS_ROOT}/verifier.md": {
        "name": "verifier",
        "description": "Reliability droid for read-only verification, diff review, and running tests without writing patches.",
        "model": "inherit",
        "tools": '["Read", "LS", "Grep", "Glob", "Execute"]',
        "role": "Verifier",
        "droid_type": "Reliability",
    },
}

MANAGED_GEMINI_ADAPTERS = {}
if AI_SKILLS_CAPABILITIES_ROOT.exists() and AI_SKILLS_CAPABILITIES_ROOT.is_dir():
    for capability_dir in sorted(AI_SKILLS_CAPABILITIES_ROOT.iterdir()):
        if capability_dir.is_dir() and not capability_dir.name.startswith("."):
            cap_md = capability_dir / "CAPABILITY.md"
            if cap_md.exists():
                skill_name = capability_dir.name
                repo_root = Path(__file__).resolve().parent.parent
                try:
                    canonical_capability = cap_md.resolve().relative_to(repo_root.resolve()).as_posix()
                except ValueError:
                    canonical_capability = f"<capabilities-root>/{skill_name}/CAPABILITY.md"
                MANAGED_GEMINI_ADAPTERS[f"{GEMINI_ADAPTERS_ROOT}/{skill_name}.md"] = {
                    "name": skill_name,
                    "description": (
                        f"Thin Workflow Manager adapter for the canonical ai-skills "
                        f"{skill_name} capability."
                    ),
                    "canonical_capability": canonical_capability,
                }

EXPECTED_WORKFLOW_COMMANDS = [
    "init",
    "sync",
    "status",
    "doctor",
    "roots",
    "hermes",
    "open",
    "list",
    "close",
    "save",
]

EXPECTED_WRAPPER_COMMANDS = [
    "project-open",
    "project-close",
    "project-save",
    "project-list",
    "project-status",
    "project-init",
    "project-sync",
    "project-add-root",
]

GUIDANCE_EXEMPTION_TOKENS = (
    "archived",
    "legacy",
    "historical",
    "preserved",
    "coexistence",
    "coexistence-only",
    "reference only",
    "no longer",
    "out of scope",
    "does not",
    "do not",
    "must not",
    "is not",
    "not by",
    "not implemented",
    "not yet",
)


class WorkflowError(RuntimeError):
    """Raised when the workflow command should fail loudly."""


@dataclass
class PlannedWrite:
    path: Path
    content: str
    description: str
    overwrite_mode: str = "error"


@dataclass
class RepoInfo:
    path: Path
    name: str
    classification: str
    notes: list[str] = field(default_factory=list)
    manifest: dict | None = None
    has_workflow_manifest: bool = False
    has_specify: bool = False
    has_ai: bool = False
    has_agents: bool = False
    has_claude: bool = False
    has_gemini: bool = False
    handoff_path: Path | None = None
    active_path: Path | None = None
    progress_path: Path | None = None
    session_log_path: Path | None = None
    legacy_handoff_path: Path | None = None
    legacy_state_path: Path | None = None
    legacy_task_path: Path | None = None
    legacy_session_log_path: Path | None = None


@dataclass
class RootsEntry:
    path: Path
    status: str


@dataclass
class HealthIssue:
    level: str
    message: str


@dataclass
class RootsHealth:
    roots: list[Path]
    usable_roots: list[Path]
    entries: list[RootsEntry]
    config_path: Path | None
    source_label: str
    status: str
    summary: str
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def missing(self) -> list[Path]:
        return [entry.path for entry in self.entries if entry.status == "missing"]

    @property
    def non_directories(self) -> list[Path]:
        return [entry.path for entry in self.entries if entry.status == "not-dir"]

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class ManifestHealth:
    manifest_path: Path
    status: str
    summary: str
    issues: list[HealthIssue] = field(default_factory=list)
    manifest: dict | None = None

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class MirrorHealth:
    lock_path: Path
    status: str
    summary: str
    sync_needed: bool
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class ContinuityStateEntry:
    relative_path: str
    status: str
    summary: str


@dataclass
class ContinuityStateHealth:
    state_root: Path
    status: str
    summary: str
    entries: list[ContinuityStateEntry] = field(default_factory=list)
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class MemoryEntry:
    relative_path: str
    status: str
    summary: str


@dataclass
class MemoryHealth:
    memory_root: Path
    status: str
    summary: str
    entries: list[MemoryEntry] = field(default_factory=list)
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class CommandDocsEntry:
    surface: str
    status: str
    summary: str


@dataclass
class CommandDocsHealth:
    manager_home: Path
    status: str
    summary: str
    entries: list[CommandDocsEntry] = field(default_factory=list)
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class RoleContractHealth:
    contract_path: Path
    status: str
    summary: str
    canonical_roles: list[str] = field(default_factory=list)
    reserved_roles: list[str] = field(default_factory=list)
    supported_harnesses: list[str] = field(default_factory=list)
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def warnings(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[HealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


@dataclass
class CliSurfaceSnapshot:
    commands: list[str]
    help_texts: dict[str, str]


@dataclass
class HealthOverview:
    overall_status: str
    summary: str
    command_docs_status: str
    manifest_status: str
    mirror_status: str
    memory_status: str
    continuity_status: str
    roots_status: str
    role_contract_status: str
    docs_status: str
    sync_needed: bool
    default_root_operations_safe: bool
    pre_hermes_readiness: str


@dataclass
class StatusSnapshot:
    repo: Path
    info: RepoInfo
    context: dict[str, str]
    command_docs_health: CommandDocsHealth
    manifest_health: ManifestHealth
    mirror_health: MirrorHealth
    memory_health: MemoryHealth
    continuity_health: ContinuityStateHealth
    roots_health: RootsHealth
    role_contract_health: RoleContractHealth
    docs_health: DocsHealth
    overview: HealthOverview


@dataclass
class DoctorResult:
    repo: Path
    info: RepoInfo
    errors: list[str]
    notes: list[str]
    overview: HealthOverview
    command_docs_health: CommandDocsHealth
    manifest_health: ManifestHealth
    mirror_health: MirrorHealth
    memory_health: MemoryHealth
    continuity_health: ContinuityStateHealth
    roots_health: RootsHealth
    role_contract_health: RoleContractHealth
    docs_health: DocsHealth
    wrote_report: bool
    drift_report_path: Path | None

    @property
    def passed(self) -> bool:
        return not self.errors


@dataclass
class HermesInventoryRepo:
    path: Path
    name: str
    classification: str
    notes: list[str] = field(default_factory=list)


@dataclass
class HermesInventoryRoot:
    path: Path
    classification: str
    repos: list[HermesInventoryRepo] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class HermesInventoryReport:
    roots_health: RootsHealth
    roots: list[HermesInventoryRoot]

    @property
    def configured_root_count(self) -> int:
        return len(self.roots)

    @property
    def usable_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "configured-root")

    @property
    def missing_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "missing-root")

    @property
    def invalid_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "invalid-root")

    @property
    def repo_count(self) -> int:
        return sum(len(root.repos) for root in self.roots)

    @property
    def classification_counts(self) -> dict[str, int]:
        counts = {name: 0 for name in ("v2", "legacy", "mixed", "unmanaged", "error")}
        for root in self.roots:
            for repo in root.repos:
                counts[repo.classification] = counts.get(repo.classification, 0) + 1
        return counts

    @property
    def summary(self) -> str:
        parts = [
            f"{self.repo_count} repo candidate(s)",
            f"{self.usable_root_count}/{self.configured_root_count} configured root(s) usable",
        ]
        if self.missing_root_count:
            parts.append(f"{self.missing_root_count} missing-root classification(s)")
        if self.invalid_root_count:
            parts.append(f"{self.invalid_root_count} invalid-root classification(s)")
        return "; ".join(parts) + "."


@dataclass
class GitPreflightFacts:
    is_git_repo: bool
    is_dirty: bool
    status: str
    dirty_path_count: int
    blocks_future_apply: bool


@dataclass
class HermesPreflightRepo:
    path: Path
    name: str
    root: Path
    scaffold_classification: str
    automation_readiness: str
    migration_track: str
    migration_risk: str
    git: GitPreflightFacts
    detected_flags: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_safe_action: str = ""


@dataclass
class HermesPreflightRoot:
    path: Path
    classification: str
    repos: list[HermesPreflightRepo] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class HermesPreflightReport:
    roots_health: RootsHealth
    roots: list[HermesPreflightRoot]

    @property
    def configured_root_count(self) -> int:
        return len(self.roots)

    @property
    def usable_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "configured-root")

    @property
    def missing_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "missing-root")

    @property
    def invalid_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "invalid-root")

    @property
    def repo_count(self) -> int:
        return sum(len(root.repos) for root in self.roots)

    @property
    def readiness_counts(self) -> dict[str, int]:
        counts = {name: 0 for name in ("ready", "needs_review", "blocked")}
        for root in self.roots:
            for repo in root.repos:
                counts[repo.automation_readiness] = counts.get(repo.automation_readiness, 0) + 1
        return counts

    @property
    def summary(self) -> str:
        counts = self.readiness_counts
        return (
            f"{self.repo_count} repo candidate(s); "
            f"{self.usable_root_count}/{self.configured_root_count} configured root(s) usable; "
            f"ready={counts['ready']}, needs_review={counts['needs_review']}, blocked={counts['blocked']}."
        )


@dataclass
class HermesAnalysisProject:
    path: Path
    name: str
    root: Path
    scaffold_classification: str
    automation_readiness: str
    migration_track: str
    migration_risk: str
    git_status: str
    deterministic_evidence: list[str] = field(default_factory=list)
    inferred_recommendation: str = ""
    blocked_actions: list[str] = field(default_factory=list)
    required_human_review: bool = False


@dataclass
class HermesAnalysisRoot:
    path: Path
    classification: str
    analyses: list[HermesAnalysisProject] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class HermesAnalysisReport:
    preflight: HermesPreflightReport
    roots: list[HermesAnalysisRoot]

    @property
    def configured_root_count(self) -> int:
        return len(self.roots)

    @property
    def usable_root_count(self) -> int:
        return sum(1 for root in self.roots if root.classification == "configured-root")

    @property
    def repo_count(self) -> int:
        return sum(len(root.analyses) for root in self.roots)

    @property
    def analysis_counts(self) -> dict[str, int]:
        counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "requires_human_review": 0,
            "blocked": 0,
        }
        for root in self.roots:
            for analysis in root.analyses:
                counts[analysis.migration_risk] = counts.get(analysis.migration_risk, 0) + 1
                if analysis.required_human_review:
                    counts["requires_human_review"] += 1
                if analysis.automation_readiness == "blocked":
                    counts["blocked"] += 1
        return counts

    @property
    def summary(self) -> str:
        counts = self.analysis_counts
        return (
            f"{self.repo_count} repo candidate(s); "
            f"{self.usable_root_count}/{self.configured_root_count} configured root(s) usable; "
            f"low={counts['low']}, medium={counts['medium']}, high={counts['high']}; "
            f"human_review={counts['requires_human_review']}, blocked={counts['blocked']}."
        )


@dataclass
class HermesQwenPreviewReport:
    analysis: HermesAnalysisReport
    selected_model: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    local_config_ready: bool
    source_summary: dict[str, object]
    analysis_summary: dict[str, object]
    request_preview: dict[str, object]
    prompt_preview: dict[str, object]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def now_short() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_optional(path: Path) -> str:
    return read_text(path) if path.exists() else ""


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def backup_path(path: Path) -> Path:
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    candidate = path.with_name(f"{path.name}.bak.{stamp}")
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.bak.{stamp}.{counter}")
        counter += 1
    return candidate


def backup_file(path: Path) -> Path:
    destination = backup_path(path)
    shutil.copy2(path, destination)
    return destination


def normalize_heading(value: str) -> str:
    return " ".join(value.strip().lower().split())


def extract_h1(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def extract_section(text: str, headings: list[str]) -> str | None:
    wanted = {normalize_heading(heading) for heading in headings}
    lines = text.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        if line.startswith("## "):
            heading = normalize_heading(line[3:])
            if collecting and heading not in wanted:
                break
            if heading in wanted:
                collecting = True
                continue
        if collecting:
            collected.append(line)
    value = "\n".join(collected).strip()
    return value or None


def parse_keyed_bullets(text: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not text:
        return parsed
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:]
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        parsed[normalize_heading(key)] = value.strip()
    return parsed


def first_nonempty_paragraph(text: str | None, default: str) -> str:
    if not text:
        return default
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return blocks[0] if blocks else default


def clean_block(text: str | None, default: str) -> str:
    if text and text.strip():
        return text.strip()
    return default


def repo_name_from_agents(repo: Path, agents_text: str) -> str:
    return extract_h1(agents_text) or repo.name


def relative_display(path: Path | None, repo: Path) -> str:
    if path is None:
        return "Unavailable."
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def render_shell_assignments(payload: dict[str, str]) -> str:
    return "\n".join(
        f"{key}={shlex.quote(value)}"
        for key, value in payload.items()
    )


def render_shell_array_assignment(name: str, values: list[str]) -> str:
    rendered = " ".join(shlex.quote(value) for value in values)
    return f"{name}=({rendered})"


def render_json_output(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def path_or_none(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def serialize_issue(issue: HealthIssue) -> dict[str, str]:
    return {
        "level": issue.level,
        "message": issue.message,
    }


def serialize_roots_health(roots_health: RootsHealth) -> dict:
    return {
        "status": roots_health.status,
        "summary": roots_health.summary,
        "config_path": path_or_none(roots_health.config_path),
        "source_label": roots_health.source_label,
        "default_root_operations_safe": roots_health.status == "pass",
        "roots": [str(root) for root in roots_health.roots],
        "usable_roots": [str(root) for root in roots_health.usable_roots],
        "entries": [
            {
                "path": str(entry.path),
                "status": entry.status,
            }
            for entry in roots_health.entries
        ],
        "issues": [serialize_issue(issue) for issue in roots_health.issues],
    }


def serialize_manifest_health(manifest_health: ManifestHealth) -> dict:
    return {
        "status": manifest_health.status,
        "summary": manifest_health.summary,
        "path": str(manifest_health.manifest_path),
        "issues": [serialize_issue(issue) for issue in manifest_health.issues],
    }


def serialize_mirror_health(mirror_health: MirrorHealth) -> dict:
    return {
        "status": mirror_health.status,
        "summary": mirror_health.summary,
        "path": str(mirror_health.lock_path),
        "sync_needed": mirror_health.sync_needed,
        "issues": [serialize_issue(issue) for issue in mirror_health.issues],
    }


def serialize_memory_health(memory_health: MemoryHealth) -> dict:
    return {
        "status": memory_health.status,
        "summary": memory_health.summary,
        "path": str(memory_health.memory_root),
        "entries": [
            {
                "relative_path": entry.relative_path,
                "status": entry.status,
                "summary": entry.summary,
            }
            for entry in memory_health.entries
        ],
        "issues": [serialize_issue(issue) for issue in memory_health.issues],
    }


def serialize_continuity_state_health(continuity_health: ContinuityStateHealth) -> dict:
    return {
        "status": continuity_health.status,
        "summary": continuity_health.summary,
        "path": str(continuity_health.state_root),
        "entries": [
            {
                "relative_path": entry.relative_path,
                "status": entry.status,
                "summary": entry.summary,
            }
            for entry in continuity_health.entries
        ],
        "issues": [serialize_issue(issue) for issue in continuity_health.issues],
    }


def serialize_command_docs_health(command_docs_health: CommandDocsHealth) -> dict:
    return {
        "status": command_docs_health.status,
        "summary": command_docs_health.summary,
        "path": str(command_docs_health.manager_home),
        "entries": [
            {
                "surface": entry.surface,
                "status": entry.status,
                "summary": entry.summary,
            }
            for entry in command_docs_health.entries
        ],
        "issues": [serialize_issue(issue) for issue in command_docs_health.issues],
    }


def serialize_role_contract_health(role_contract_health: RoleContractHealth) -> dict:
    return {
        "status": role_contract_health.status,
        "summary": role_contract_health.summary,
        "path": str(role_contract_health.contract_path),
        "canonical_roles": list(role_contract_health.canonical_roles),
        "reserved_roles": list(role_contract_health.reserved_roles),
        "supported_harnesses": list(role_contract_health.supported_harnesses),
        "issues": [serialize_issue(issue) for issue in role_contract_health.issues],
    }


def serialize_docs_health(docs_health: DocsHealth) -> dict:
    return {
        "status": docs_health.status,
        "summary": docs_health.summary,
        "path": str(docs_health.repo),
        "entries": [
            {
                "relative_path": entry.relative_path,
                "status": entry.status,
                "line_count": entry.line_count,
                "budget": entry.budget,
                "summary": entry.summary,
            }
            for entry in docs_health.entries
        ],
        "issues": [serialize_issue(HealthIssue(issue.level, issue.message)) for issue in docs_health.issues],
    }


def serialize_health_overview(overview: HealthOverview) -> dict:
    return {
        "overall_status": overview.overall_status,
        "summary": overview.summary,
        "subsystems": {
            "command_help_docs": overview.command_docs_status,
            "manifest": overview.manifest_status,
            "mirror_lock_shim": overview.mirror_status,
            "memory": overview.memory_status,
            "continuity_state": overview.continuity_status,
            "roots": overview.roots_status,
            "role_contract": overview.role_contract_status,
            "docs_health": overview.docs_status,
        },
        "sync_needed": overview.sync_needed,
        "default_root_operations_safe": overview.default_root_operations_safe,
        "pre_hermes_readiness": overview.pre_hermes_readiness,
    }


def serialize_health_bundle(
    command_docs_health: CommandDocsHealth,
    manifest_health: ManifestHealth,
    mirror_health: MirrorHealth,
    memory_health: MemoryHealth,
    continuity_health: ContinuityStateHealth,
    roots_health: RootsHealth,
    role_contract_health: RoleContractHealth,
    docs_health: DocsHealth,
) -> dict:
    return {
        "command_help_docs": serialize_command_docs_health(command_docs_health),
        "manifest": serialize_manifest_health(manifest_health),
        "mirror_lock_shim": serialize_mirror_health(mirror_health),
        "memory": serialize_memory_health(memory_health),
        "continuity_state": serialize_continuity_state_health(continuity_health),
        "roots": serialize_roots_health(roots_health),
        "role_contract": serialize_role_contract_health(role_contract_health),
        "docs_health": serialize_docs_health(docs_health),
    }


def status_continuity_payload(info: RepoInfo) -> dict:
    sources: dict[str, str | bool] = {
        "legacy_preserved": info.has_ai,
    }
    if info.handoff_path is not None:
        sources["handoff"] = relative_display(info.handoff_path, info.path)
    if info.active_path is not None:
        sources["active_state"] = relative_display(info.active_path, info.path)
    if info.progress_path is not None:
        sources["progress"] = relative_display(info.progress_path, info.path)
    if info.session_log_path is not None:
        sources["session_log"] = relative_display(info.session_log_path, info.path)
    if info.legacy_handoff_path is not None:
        sources["legacy_handoff"] = relative_display(info.legacy_handoff_path, info.path)
    if info.legacy_state_path is not None:
        sources["legacy_state"] = relative_display(info.legacy_state_path, info.path)
    if info.legacy_task_path is not None:
        sources["legacy_task"] = relative_display(info.legacy_task_path, info.path)
    if info.legacy_session_log_path is not None:
        sources["legacy_session_log"] = relative_display(info.legacy_session_log_path, info.path)
    return sources


def status_migration_payload(info: RepoInfo, summary: str) -> dict:
    payload: dict[str, object] = {
        "summary": summary,
    }
    manifest = info.manifest if isinstance(info.manifest, dict) else {}
    migration = manifest.get("migration")
    if isinstance(migration, dict):
        payload["status"] = migration.get("status")
        payload["phase"] = migration.get("phase")
        payload["legacy_preserved"] = migration.get("legacy_preserved")
        payload["branch"] = migration.get("branch")
    return payload


DOCTOR_FINDING_PATTERN = re.compile(
    r"^(Command/help/docs|Role-contract|Docs-health|Manifest|Mirror-lock/shim|Memory|Continuity-state|Roots) (error|warning): (.+)$"
)


def parse_doctor_finding(text: str) -> dict[str, str]:
    match = DOCTOR_FINDING_PATTERN.match(text)
    if not match:
        return {
            "surface": "repo",
            "level": "error",
            "message": text,
            "text": text,
        }
    return {
        "surface": match.group(1).lower().replace("/", "_").replace("-", "_"),
        "level": match.group(2),
        "message": match.group(3),
        "text": text,
    }


def build_workflow_error_payload(command: str, message: str, *, repo_path: str | None = None) -> dict:
    return {
        "schema_version": MACHINE_OUTPUT_SCHEMA_VERSION,
        "command": command,
        "repo_path": repo_path,
        "result_status": "fail",
        "errors": [message],
    }


def extract_relative_path_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for raw_token in text.replace("`", " ").split():
        token = raw_token.strip("()[]{}<>,.;:'\"")
        if not token or token.startswith(("http://", "https://", "/")):
            continue
        if "/" not in token and not token.endswith((".md", ".json", ".txt")):
            continue
        if token in seen:
            continue
        seen.add(token)
        candidates.append(token)
    return candidates


def ensure_repo_target(path_value: str | None) -> Path:
    repo = Path(path_value).expanduser().resolve() if path_value else Path.cwd().resolve()
    if repo.exists() and not repo.is_dir():
        raise WorkflowError(f"`{repo}` exists but is not a directory.")
    return repo


def workflow_manager_home() -> Path:
    override = os.environ.get("WORKFLOW_MANAGER_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def roots_config_path() -> Path:
    explicit = os.environ.get("WORKFLOW_ROOTS_FILE")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return workflow_manager_home() / ".workflow/roots.json"


def build_roots_health(
    raw_roots: list[str | Path],
    *,
    source_label: str,
    config_path: Path | None = None,
) -> RootsHealth:
    roots: list[Path] = []
    usable_roots: list[Path] = []
    entries: list[RootsEntry] = []
    issues: list[HealthIssue] = []
    seen: set[str] = set()

    if not raw_roots:
        issues.append(HealthIssue("error", f"{source_label} does not declare any workspace roots."))

    for index, raw_root in enumerate(raw_roots, start=1):
        raw_value = str(raw_root).strip()
        if not raw_value:
            issues.append(
                HealthIssue("error", f"{source_label} contains an empty roots entry at position {index}.")
            )
            continue
        candidate = Path(raw_value).expanduser()
        if not candidate.is_absolute():
            issues.append(
                HealthIssue(
                    "error",
                    f"{source_label} entry {index} must be an absolute path or use `~`: `{raw_value}`.",
                )
            )
            continue
        resolved = candidate.resolve()
        key = str(resolved)
        if key in seen:
            issues.append(
                HealthIssue("error", f"{source_label} contains a duplicate workspace root: `{resolved}`.")
            )
            continue
        seen.add(key)
        roots.append(resolved)

        if not resolved.exists():
            entries.append(RootsEntry(resolved, "missing"))
            issues.append(HealthIssue("warning", f"Configured root is missing on disk: `{resolved}`."))
            continue
        if not resolved.is_dir():
            entries.append(RootsEntry(resolved, "not-dir"))
            issues.append(HealthIssue("warning", f"Configured root exists but is not a directory: `{resolved}`."))
            continue
        entries.append(RootsEntry(resolved, "ok"))
        usable_roots.append(resolved)

    failure_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if failure_count:
        status = "fail"
        if failure_count == 1 and not warning_count:
            summary = issues[0].message
        else:
            summary = f"{failure_count} roots-config error(s) detected."
    elif warning_count:
        status = "warning"
        if warning_count == 1:
            summary = issues[0].message
        else:
            summary = f"{warning_count} configured roots need review."
    else:
        status = "pass"
        count = len(roots)
        noun = "root is" if count == 1 else "roots are"
        summary = f"All {count} configured {noun} usable."

    return RootsHealth(
        roots=roots,
        usable_roots=usable_roots,
        entries=entries,
        config_path=config_path,
        source_label=source_label,
        status=status,
        summary=summary,
        issues=issues,
    )


def evaluate_configured_roots() -> RootsHealth:
    config_path = roots_config_path()
    if not config_path.exists():
        message = f"Missing roots config `{config_path}`."
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    try:
        payload = json.loads(read_text(config_path))
    except json.JSONDecodeError as exc:
        message = f"Invalid roots config `{config_path}`: {exc}"
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    if not isinstance(payload, dict):
        message = f"Invalid roots config `{config_path}`: top-level JSON must be an object."
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    schema_version = payload.get("schema_version")
    if schema_version != ROOTS_CONFIG_SCHEMA_VERSION:
        message = (
            f"Invalid roots config `{config_path}`: expected schema_version "
            f"`{ROOTS_CONFIG_SCHEMA_VERSION}`, found `{schema_version}`."
        )
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    if "roots" not in payload:
        message = f"Invalid roots config `{config_path}`: missing required `roots` key."
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    raw_roots = payload.get("roots")
    if not isinstance(raw_roots, list):
        message = f"Invalid roots config `{config_path}`: `roots` must be a JSON array."
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    if not raw_roots:
        message = f"Invalid roots config `{config_path}`: `roots` must not be empty."
        return RootsHealth(
            roots=[],
            usable_roots=[],
            entries=[],
            config_path=config_path,
            source_label=f"roots config `{config_path}`",
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )
    return build_roots_health(
        [str(root) for root in raw_roots],
        source_label=f"roots config `{config_path}`",
        config_path=config_path,
    )


def resolve_workspace_roots(explicit_roots: list[Path]) -> RootsHealth:
    if explicit_roots:
        return build_roots_health(
            explicit_roots,
            source_label="explicit `--roots` arguments",
        )
    return evaluate_configured_roots()


def require_usable_roots(explicit_roots: list[Path]) -> RootsHealth:
    roots_health = resolve_workspace_roots(explicit_roots)
    if roots_health.status == "fail":
        messages = "\n".join(issue.message for issue in roots_health.failures)
        raise WorkflowError(messages)
    return roots_health


def roots_issue_lines(roots_health: RootsHealth, *, level: str | None = None) -> list[str]:
    issues = roots_health.issues
    if level is not None:
        issues = [issue for issue in issues if issue.level == level]
    return [issue.message for issue in issues]


def legacy_shim_header(filename: str, project_name: str) -> str:
    tool = SHIMS[filename]
    return textwrap.dedent(
        f"""\
        # {tool} context — {project_name}
        # This file is auto-synced from AGENTS.md via project-sync.
        # To update: edit AGENTS.md, then run project-sync.
        """
    ).strip()


def render_shim(
    filename: str,
    project_name: str,
    agents_text: str,
    unmanaged: str = "",
) -> str:
    tool = SHIMS[filename]
    unmanaged = unmanaged.rstrip("\n")
    if not unmanaged:
        unmanaged = (
            "No unmanaged notes.\n"
            "Add tool-specific notes here only when they cannot live in `AGENTS.md`."
        )
    managed_block = textwrap.dedent(
        """\
        # {tool} context — {project_name}
        # Generated from AGENTS.md by `workflow sync`.
        # Do not edit the managed section below.

        {managed_start}
        {agents_text}
        {managed_end}

        {unmanaged_start}
        {unmanaged}
        {unmanaged_end}
        """
    ).format(
        tool=tool,
        project_name=project_name,
        managed_start=MANAGED_START,
        agents_text=agents_text.rstrip(),
        managed_end=MANAGED_END,
        unmanaged_start=UNMANAGED_START,
        unmanaged=unmanaged,
        unmanaged_end=UNMANAGED_END,
    )
    generated_header = (
        f"<!-- workflow-generated:version={GENERATED_FORMAT_VERSION};"
        f"tool={filename};source=AGENTS.md -->"
    )
    return f"{generated_header}\n{managed_block.rstrip()}\n"


def render_role_shim() -> str:
    return textwrap.dedent(
        f"""\
        <!-- workflow-generated:version={GENERATED_FORMAT_VERSION};tool=roles-pointer;source=~/ROLES.md -->

        # Roles

        This file is generated by `workflow sync`; do not edit it directly.

        Canonical role contract: `~/ROLES.md`

        This repo-local file is intentionally only a pointer. It must not copy,
        summarize, or redefine the Architect, Coder, Verifier, or reserved Tester
        role definitions.

        Per-repo specifics may live in `AGENTS.md` or `.specify/*`; the role
        definitions themselves live only in `~/ROLES.md`.
        """
    )


def parse_generated_role_shim(text: str) -> dict[str, str] | None:
    marker = f"workflow-generated:version={GENERATED_FORMAT_VERSION};tool=roles-pointer;source=~/ROLES.md"
    if not text.startswith("<!-- workflow-generated:"):
        return None
    if marker not in text:
        return None
    if "Canonical role contract: `~/ROLES.md`" not in text:
        return None
    for forbidden_heading in ("### Architect", "### Coder", "### Verifier"):
        if forbidden_heading in text:
            return None
    return {"format": GENERATED_FORMAT_VERSION, "source": "~/ROLES.md"}


def parse_generated_shim(text: str) -> dict[str, str] | None:
    if not text.startswith("<!-- workflow-generated:"):
        return None
    try:
        managed = text.split(MANAGED_START, 1)[1].split(MANAGED_END, 1)[0]
        unmanaged = text.split(UNMANAGED_START, 1)[1].split(UNMANAGED_END, 1)[0]
    except IndexError:
        return None
    return {
        "managed": managed.strip("\n"),
        "unmanaged": unmanaged.strip("\n"),
    }


def render_gemini_adapter(relative_path: str) -> str:
    adapter = MANAGED_GEMINI_ADAPTERS[relative_path]
    heading = f"{adapter['name']} Capability Adapter"
    return textwrap.dedent(
        f"""\
        ---
        name: {adapter["name"]}
        description: {adapter["description"]}
        ---

        <!-- workflow-generated:version={GENERATED_FORMAT_VERSION};tool=gemini-subagent;source={adapter["canonical_capability"]} -->

        # {heading}

        This file is generated by `workflow sync`; do not edit it directly.

        Canonical capability: `{adapter["canonical_capability"]}`

        Read and follow that canonical capability file before using this subagent.
        This adapter is intentionally thin and must not copy or replace the full capability body.
        """
    )


def render_claude_adapter(relative_path: str) -> str:
    adapter = MANAGED_CLAUDE_ADAPTERS[relative_path]
    return textwrap.dedent(
        f"""\
        ---
        name: {adapter["name"]}
        description: {adapter["description"]}
        tools: {adapter["tools"]}
        ---

        <!-- workflow-generated:version={GENERATED_FORMAT_VERSION};tool=claude-subagent;source=ROLES.md -->

        # {adapter["role"]} Adapter

        This file is generated by `workflow sync`; do not edit it directly.

        Canonical role contract: `~/ROLES.md`
        Workflow-manager local mapping: `ROLES.md`

        Read and follow the canonical role contract before using this subagent.
        This adapter is intentionally thin and must not copy or replace the role definitions.
        """
    )


def render_opencode_adapter(relative_path: str) -> str:
    adapter = MANAGED_OPENCODE_ADAPTERS[relative_path]
    permission_lines = "\n".join(
        f"  {key}: {value}" for key, value in adapter["permission"].items()
    )
    return (
        "---\n"
        f"description: {adapter['description']}\n"
        f"mode: {adapter['mode']}\n"
        "permission:\n"
        f"{permission_lines}\n"
        "---\n\n"
        f"<!-- workflow-generated:version={GENERATED_FORMAT_VERSION};tool=opencode-agent;source=ROLES.md -->\n\n"
        f"# {adapter['role']} Adapter\n\n"
        "This file is generated by `workflow sync`; do not edit it directly.\n\n"
        "Canonical role contract: `~/ROLES.md`\n"
        "Workflow-manager local mapping: `ROLES.md`\n\n"
        "Read and follow the canonical role contract before using this agent.\n"
        "This adapter is intentionally thin and must not copy or replace the role definitions.\n"
    )


def render_droid_adapter(relative_path: str) -> str:
    adapter = MANAGED_DROID_ADAPTERS[relative_path]
    return (
        "---\n"
        f"name: {adapter['name']}\n"
        f"description: {adapter['description']}\n"
        f"model: {adapter['model']}\n"
        f"tools: {adapter['tools']}\n"
        "---\n\n"
        f"<!-- workflow-generated:version={GENERATED_FORMAT_VERSION};tool=factory-droid;source=ROLES.md -->\n\n"
        f"# {adapter['role']} Adapter\n\n"
        "This file is generated by `workflow sync`; do not edit it directly.\n\n"
        f"Factory Droid type assignment: {adapter['droid_type']}\n"
        "Canonical role contract: `~/ROLES.md`\n"
        "Workflow-manager local mapping: `ROLES.md`\n\n"
        "Read and follow the canonical role contract before using this droid.\n"
        "This adapter is intentionally thin and must not copy or replace the role definitions.\n"
    )


def parse_generated_claude_adapter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    if f"workflow-generated:version={GENERATED_FORMAT_VERSION};tool=claude-subagent;" not in text:
        return None
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        return None
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    if not metadata.get("name") or not metadata.get("description") or not metadata.get("tools"):
        return None
    return metadata


def parse_generated_droid_adapter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    if f"workflow-generated:version={GENERATED_FORMAT_VERSION};tool=factory-droid;" not in text:
        return None
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        return None
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    if (
        not metadata.get("name")
        or not metadata.get("description")
        or metadata.get("model") != "inherit"
        or not metadata.get("tools")
    ):
        return None
    return metadata


def parse_generated_opencode_adapter(text: str) -> dict[str, object] | None:
    if not text.startswith("---\n"):
        return None
    if f"workflow-generated:version={GENERATED_FORMAT_VERSION};tool=opencode-agent;" not in text:
        return None
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        return None
    metadata: dict[str, object] = {}
    permission: dict[str, str] = {}
    in_permission = False
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and in_permission:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            permission[key.strip()] = value.strip()
            continue
        in_permission = False
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "permission":
            in_permission = True
            metadata["permission"] = permission
        else:
            metadata[key] = value
    if not metadata.get("description") or metadata.get("mode") != "subagent" or not permission:
        return None
    return metadata


def parse_generated_gemini_adapter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    if f"workflow-generated:version={GENERATED_FORMAT_VERSION};tool=gemini-subagent;" not in text:
        return None
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError:
        return None
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    if not metadata.get("name") or not metadata.get("description"):
        return None
    return metadata


def is_legacy_generated_shim(text: str, filename: str, project_name: str) -> bool:
    return text.startswith(legacy_shim_header(filename, project_name))


def ensure_agents(repo: Path) -> str:
    path = repo / "AGENTS.md"
    if path.exists():
        return read_text(path)
    repo_name = repo.name
    return textwrap.dedent(
        f"""\
        # {repo_name}

        ## What this project is
        Describe what this project is and why it exists.

        ## Current status
        Fill in the current state of the project.

        ## Active task
        Describe the current focus for the next session.

        ## How to continue
        1. Read `.specify/state/handoff.md`
        2. Read `.specify/state/active.md`
        3. Confirm the next safe step before changing code

        ## Key files
        - Add the most important files in this repo.

        ## Rules
        - Keep `AGENTS.md` as the canonical cross-tool contract.
        - Canonical role definitions live in `~/ROLES.md`; repo-local `ROLES.md` is only a thin pointer.
        - Run `workflow sync` after editing `AGENTS.md`.
        - Update `.specify/state/*` as work changes.
        """
    )


def build_manifest(repo: Path, legacy_exists: bool) -> str:
    manifest = {
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "scaffold": "workflow-manager-v2",
        "base": "workflow-manager-safe-slice",
        "canonical_contract": DEFAULT_CANONICAL_CONTRACT,
        "generated_role_shims": list(GENERATED_ROLE_SHIMS),
        "generated_shims": list(SHIMS.keys()),
        "generated_claude_adapters": list(MANAGED_CLAUDE_ADAPTERS.keys()),
        "generated_opencode_adapters": list(MANAGED_OPENCODE_ADAPTERS.keys()),
        "generated_droid_adapters": list(MANAGED_DROID_ADAPTERS.keys()),
        "generated_gemini_adapters": list(MANAGED_GEMINI_ADAPTERS.keys()),
        "state_root": DEFAULT_STATE_ROOT,
        "memory_root": DEFAULT_MEMORY_ROOT,
        "legacy_root": DEFAULT_LEGACY_ROOT,
        "migration": {
            "status": "coexist" if legacy_exists else "v2",
            "started_at": timestamp(),
            "phase": "milestone-1-foundation",
            "branch": None,
            "legacy_preserved": legacy_exists,
        },
        "features": {
            "graphify": False,
            "memory_bank_compat": False,
            "nested_workspaces": False,
            "llm_analysis": False,
        },
        "hermes": {
            "model": None,
            "provider": None,
            "mode": "migration-only",
            "last_run": None,
        },
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def collect_context(repo: Path, agents_text: str) -> dict[str, str]:
    project_state = read_optional(repo / ".ai/context/PROJECT_STATE.md")
    next_step = read_optional(repo / ".ai/handoffs/NEXT_STEP.md")
    current_task = read_optional(repo / ".ai/prompts/CURRENT_TASK.md")
    legacy_session_log = read_optional(repo / ".ai/logs/session.log")
    return {
        "project_name": repo_name_from_agents(repo, agents_text),
        "agents_text": agents_text,
        "what_project": first_nonempty_paragraph(
            extract_section(agents_text, ["What this project is"]),
            "Describe what this project is and why it exists.",
        ),
        "current_status": clean_block(
            extract_section(agents_text, ["Current status"]),
            "Current status has not been captured yet.",
        ),
        "active_task": first_nonempty_paragraph(
            extract_section(agents_text, ["Active task"]),
            "No current task has been recorded yet.",
        ),
        "how_to_continue": clean_block(
            extract_section(agents_text, ["How to continue"]),
            "1. Read `.specify/state/handoff.md`\n2. Read `.specify/state/active.md`",
        ),
        "key_files": clean_block(
            extract_section(agents_text, ["Key files"]),
            "- Add the most important files in this repo.",
        ),
        "rules": clean_block(
            extract_section(agents_text, ["Rules", "Rules for this project"]),
            "- Keep `AGENTS.md` as the canonical cross-tool contract.",
        ),
        "known_truths": clean_block(
            extract_section(project_state, ["Known Truths"]),
            "- Stable facts have not been imported yet.",
        ),
        "open_unknowns": clean_block(
            extract_section(project_state, ["Open Unknowns"]),
            "- No open questions were imported from the legacy state.",
        ),
        "next_validation": first_nonempty_paragraph(
            extract_section(project_state, ["Next Validation Step"]),
            "Run `workflow doctor` after changing workflow artifacts.",
        ),
        "completed": clean_block(
            extract_section(project_state, ["Completed"]),
            "- No legacy completion log was imported.",
        ),
        "next_step_done": clean_block(
            extract_section(next_step, ["What was just done"]),
            "Legacy handoff notes were not present.",
        ),
        "next_step_next": clean_block(
            extract_section(next_step, ["What to do next"]),
            "Capture the next safe step in `.specify/state/handoff.md`.",
        ),
        "next_step_blockers": clean_block(
            extract_section(next_step, ["Blockers"]),
            "None recorded.",
        ),
        "current_task_prompt": clean_block(
            current_task.strip(),
            "No legacy current-task prompt was imported.",
        ),
        "legacy_session_log": legacy_session_log.strip(),
    }


def build_seed_files(repo: Path, context: dict[str, str], legacy_exists: bool) -> list[PlannedWrite]:
    spec_file = repo / "research-results/workflow-manager-v2-product-spec.md"
    spec_note = (
        "- Open question: the product spec still calls for a future `spec-kit` fork/preset. "
        "This safe slice uses repo-local deterministic templates instead, and the repo should revisit that before Hermes work begins."
        if spec_file.exists()
        else "- No explicit open questions have been recorded yet."
    )
    session_entries: list[str] = []
    if context["legacy_session_log"]:
        for line in context["legacy_session_log"].splitlines()[-5:]:
            if line.strip():
                session_entries.append(f"- Imported legacy entry: {line.strip()}")
    session_entries.append(
        f"- {now_short()}: Seeded the v2 continuity layer from `AGENTS.md` and preserved legacy `.ai/` files for coexistence."
    )
    migration_status = "coexist" if legacy_exists else "v2"

    files = {
        ".workflow/workflow.json": build_manifest(repo, legacy_exists),
        "ROLES.md": render_role_shim(),
        ".specify/memory/constitution.md": textwrap.dedent(
            """\
            # Constitution

            Updated: {updated}
            Primary source: `AGENTS.md`

            ## Non-negotiables
            {rules}

            ## Continuity contract
            - `AGENTS.md` is the only hand-edited cross-tool contract.
            - Run `workflow sync` after any change to `AGENTS.md`.
            - Treat `.specify/memory/*` and `.specify/state/*` as the primary v2 continuity layer.
            - Preserve legacy `.ai/` files during coexistence, but do not treat them as the operational source of truth after v2 activation.
            - Prefer loud validation and explicit backups over silent repair.

            ## Source notes
            - This file was seeded from `AGENTS.md` and legacy continuity docs where available.
            """
        ).format(updated=now_short(), rules=context["rules"]),
        ".specify/memory/project.md": textwrap.dedent(
            """\
            # Project Memory

            Updated: {updated}
            Primary sources: `AGENTS.md`, `.ai/context/PROJECT_STATE.md`

            ## What this project is
            {what_project}

            ## Stable facts
            {known_truths}

            ## Current status snapshot
            {current_status}

            ## Open questions
            {open_unknowns}
            {spec_note}

            ## Next validation step
            {next_validation}
            """
        ).format(
            updated=now_short(),
            what_project=context["what_project"],
            known_truths=context["known_truths"],
            current_status=context["current_status"],
            open_unknowns=context["open_unknowns"],
            spec_note=spec_note,
            next_validation=context["next_validation"],
        ),
        ".specify/memory/decisions.md": textwrap.dedent(
            """\
            # Decisions

            Updated: {updated}

            ## Durable decisions
            - `AGENTS.md` remains the canonical contract for cross-tool instructions.
            - `CLAUDE.md` and `GEMINI.md` are generated compatibility shims and should be synced from `AGENTS.md`.
            - Session continuity must live in repo-local files instead of chat memory alone.
            - Legacy `.ai/` artifacts stay preserved during the coexistence phase.

            ## Imported legacy context
            {completed}

            ## Review notes
            {spec_note}
            """
        ).format(updated=now_short(), completed=context["completed"], spec_note=spec_note),
        ".specify/memory/architecture.md": textwrap.dedent(
            """\
            # Architecture

            Updated: {updated}

            ## Layers
            - Canonical contract: `AGENTS.md`
            - Generated shim layer: `CLAUDE.md`, `GEMINI.md`
            - Manifest and lock layer: `.workflow/workflow.json`, `.workflow/mirror-lock.json`
            - Continuity layer: `.specify/memory/*`, `.specify/state/*`
            - Legacy compatibility layer: `.ai/` preserved during migration

            ## Command model
            - `workflow` owns deterministic init, sync, status, doctor, close, save, and list behavior.
            - `project-*` commands are thin shell wrappers around the v2 model where possible.
            - The shell script remains a thin workspace bridge for navigation-oriented commands.

            ## Guardrails
            - Generated shims are checksum-locked from `AGENTS.md`.
            - Sync refuses managed drift unless `--force` is used.
            - Doctor fails loudly on missing, empty, inconsistent, or half-migrated artifacts.
            """
        ).format(updated=now_short()),
        ".specify/memory/tech.md": textwrap.dedent(
            """\
            # Tech Context

            Updated: {updated}

            ## Stack
            - Python 3 standard library for deterministic workflow commands
            - zsh shell bridge in `scripts/workflow.sh`
            - Markdown and JSON artifacts stored in-repo

            ## Core commands
            - `workflow init [--dry-run]`
            - `workflow sync`
            - `workflow status`
            - `workflow doctor`
            - `workflow open`
            - `workflow list`
            - `workflow close`
            - `workflow save`

            ## Continuity workflow
            {how_to_continue}

            ## Important files
            {key_files}
            """
        ).format(
            updated=now_short(),
            how_to_continue=context["how_to_continue"],
            key_files=context["key_files"],
        ),
        ".specify/state/active.md": textwrap.dedent(
            """\
            # Active State

            Updated: {updated}

            ## Current task
            {active_task}

            ## Active spec/task pointer
            No active spec/task is declared yet.

            ## Current focus
            {current_task_prompt}

            ## Notes
            - This repo is using `.specify/*` as the primary continuity layer.
            """
        ).format(
            updated=now_short(),
            active_task=context["active_task"],
            current_task_prompt=context["current_task_prompt"],
        ),
        ".specify/state/handoff.md": textwrap.dedent(
            """\
            # Handoff

            Updated: {updated}

            ## What was just done
            {next_step_done}

            ## What to do next
            {next_step_next}

            ## Blockers
            {next_step_blockers}
            """
        ).format(
            updated=now_short(),
            next_step_done=context["next_step_done"],
            next_step_next=context["next_step_next"],
            next_step_blockers=context["next_step_blockers"],
        ),
        ".specify/state/progress.md": textwrap.dedent(
            """\
            # Progress

            Updated: {updated}

            ## Recent progress
            - {updated}: Bootstrapped the v2 scaffold foundation in this repo and preserved legacy `.ai/` artifacts for coexistence.

            ## Imported legacy completions
            {completed}
            """
        ).format(updated=now_short(), completed=context["completed"]),
        ".specify/state/session.log.md": textwrap.dedent(
            """\
            # Session Log

            Updated: {updated}

            ## Entries
            {entries}
            """
        ).format(updated=now_short(), entries="\n".join(session_entries)),
        ".specify/state/drift.md": textwrap.dedent(
            """\
            # Drift Report

            Updated: {updated}

            ## Latest summary
            - No doctor report has been written yet.
            - Run `workflow doctor --write-report` to refresh this file.

            ## Notes
            - Graphify checks are disabled in this safe slice.
            """
        ).format(updated=now_short()),
        ".specify/state/migration.md": textwrap.dedent(
            """\
            # Migration State

            Updated: {updated}

            ## Current state
            - Status: {migration_status}
            - Phase: milestone-1-foundation
            - Legacy preserved: {legacy_preserved}
            - Canonical continuity: `.specify/*`
            - Legacy continuity: `.ai/*` preserved during coexistence

            ## Notes
            - Hermes migration logic is intentionally out of scope for this slice.
            - Graphify integration is intentionally out of scope for this slice.
            - This repo should remain self-describing without the external setup markdown.
            """
        ).format(
            updated=now_short(),
            migration_status=migration_status,
            legacy_preserved="yes" if legacy_exists else "no",
        ),
    }
    return [
        PlannedWrite(repo / relative_path, content.rstrip() + "\n", relative_path)
        for relative_path, content in files.items()
    ]


def load_manifest(repo: Path) -> dict:
    manifest_path = repo / ".workflow/workflow.json"
    if not manifest_path.exists():
        raise WorkflowError("Missing `.workflow/workflow.json`. Run `workflow init` first.")
    try:
        return json.loads(read_text(manifest_path))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid `.workflow/workflow.json`: {exc}") from exc


def load_lock(repo: Path) -> dict | None:
    lock_path = repo / ".workflow/mirror-lock.json"
    if not lock_path.exists():
        return None
    try:
        return json.loads(read_text(lock_path))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid `.workflow/mirror-lock.json`: {exc}") from exc


def mirror_lock_declares_path(lock_payload: object, relative_path: str) -> bool:
    if not isinstance(lock_payload, dict):
        return False
    if lock_payload.get("canonical_contract") == relative_path:
        return True
    for key in ("shims", "role_shims", "gemini_adapters", "claude_adapters", "opencode_adapters", "droid_adapters"):
        section = lock_payload.get(key)
        if isinstance(section, dict) and relative_path in section:
            return True
    return False


def manifest_managed_adapter_paths(manifest: object, key: str, registry: dict[str, dict]) -> list[str]:
    if not isinstance(manifest, dict):
        return list(registry.keys())
    configured = manifest.get(key)
    if configured is None:
        return list(registry.keys())
    if not isinstance(configured, list):
        return list(registry.keys())
    return [
        relative_path
        for relative_path in configured
        if isinstance(relative_path, str) and relative_path in registry
    ]


def evaluate_manifest_health(repo: Path) -> ManifestHealth:
    manifest_path = repo / ".workflow/workflow.json"
    issues: list[HealthIssue] = []
    manifest: dict | None = None

    if not manifest_path.exists():
        message = f"Missing manifest `{manifest_path}`."
        return ManifestHealth(
            manifest_path=manifest_path,
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )

    try:
        payload = json.loads(read_text(manifest_path))
    except json.JSONDecodeError as exc:
        message = f"Invalid manifest `{manifest_path}`: {exc}"
        return ManifestHealth(
            manifest_path=manifest_path,
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )

    if not isinstance(payload, dict):
        message = f"Invalid manifest `{manifest_path}`: top-level JSON must be an object."
        return ManifestHealth(
            manifest_path=manifest_path,
            status="fail",
            summary=message,
            issues=[HealthIssue("error", message)],
        )

    manifest = payload
    if payload.get("schema_version") != WORKFLOW_SCHEMA_VERSION:
        issues.append(
            HealthIssue(
                "error",
                f"Manifest `{manifest_path}` has unsupported schema_version "
                f"`{payload.get('schema_version')}`; expected `{WORKFLOW_SCHEMA_VERSION}`.",
            )
        )

    required_keys = [
        "canonical_contract",
        "memory_root",
        "state_root",
        "legacy_root",
        "migration",
    ]
    for key in required_keys:
        if key not in payload:
            issues.append(HealthIssue("error", f"Manifest `{manifest_path}` is missing required key `{key}`."))

    if payload.get("canonical_contract") != DEFAULT_CANONICAL_CONTRACT:
        issues.append(
            HealthIssue(
                "error",
                f"Manifest `{manifest_path}` must declare `canonical_contract` as `{DEFAULT_CANONICAL_CONTRACT}`.",
            )
        )
    if payload.get("memory_root") != DEFAULT_MEMORY_ROOT:
        issues.append(
            HealthIssue(
                "error",
                f"Manifest `{manifest_path}` must declare `memory_root` as `{DEFAULT_MEMORY_ROOT}`.",
            )
        )
    if payload.get("state_root") != DEFAULT_STATE_ROOT:
        issues.append(
            HealthIssue(
                "error",
                f"Manifest `{manifest_path}` must declare `state_root` as `{DEFAULT_STATE_ROOT}`.",
            )
        )
    if payload.get("legacy_root") != DEFAULT_LEGACY_ROOT:
        issues.append(
            HealthIssue(
                "error",
                f"Manifest `{manifest_path}` must declare `legacy_root` as `{DEFAULT_LEGACY_ROOT}`.",
            )
        )

    migration = payload.get("migration")
    if not isinstance(migration, dict):
        issues.append(HealthIssue("error", f"Manifest `{manifest_path}` must declare `migration` as an object."))
    else:
        has_legacy = (repo / DEFAULT_LEGACY_ROOT).exists()
        has_state = (repo / ".specify").exists()
        status = migration.get("status")
        legacy_preserved = migration.get("legacy_preserved")
        if has_legacy and has_state:
            if status not in {"coexist", "legacy"}:
                issues.append(
                    HealthIssue(
                        "error",
                        "Manifest migration status conflicts with the repo's coexistence model; "
                        "expected `coexist` or `legacy` while both `.ai/` and `.specify/` exist.",
                    )
                )
            if legacy_preserved is not True:
                issues.append(
                    HealthIssue(
                        "error",
                        "Manifest migration metadata conflicts with the repo's coexistence model; "
                        "expected `legacy_preserved` to be true while `.ai/` is still present.",
                    )
                )
        elif not has_legacy and status == "coexist":
            issues.append(
                HealthIssue(
                    "error",
                    "Manifest migration status claims coexistence, but `.ai/` is not present in the repo.",
                )
            )

    if issues:
        summary = issues[0].message if len(issues) == 1 else f"{len(issues)} manifest issue(s) detected."
        return ManifestHealth(
            manifest_path=manifest_path,
            status="fail",
            summary=summary,
            issues=issues,
            manifest=manifest,
        )

    return ManifestHealth(
        manifest_path=manifest_path,
        status="pass",
        summary="Manifest matches the current v2 repo model.",
        issues=[],
        manifest=manifest,
    )


def evaluate_mirror_health(repo: Path) -> MirrorHealth:
    lock_path = repo / ".workflow/mirror-lock.json"
    manifest_path = repo / ".workflow/workflow.json"
    agents_path = repo / DEFAULT_CANONICAL_CONTRACT
    issues: list[HealthIssue] = []
    sync_needed = False
    agents_text = ""
    agents_checksum = ""
    lock_payload: dict | None = None
    manifest_payload: dict | None = None
    project_name = repo.name

    if manifest_path.exists():
        try:
            payload = json.loads(read_text(manifest_path))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            manifest_payload = payload

    if not agents_path.exists():
        issues.append(HealthIssue("error", f"Missing canonical contract `{agents_path}`."))
    else:
        agents_text = read_text(agents_path)
        agents_checksum = sha256_text(agents_text)
        project_name = repo_name_from_agents(repo, agents_text)

    if not lock_path.exists():
        issues.append(
            HealthIssue(
                "error",
                f"Missing mirror lockfile `{lock_path}`. Run `workflow sync` to generate it.",
            )
        )
    else:
        try:
            payload = json.loads(read_text(lock_path))
        except json.JSONDecodeError as exc:
            issues.append(HealthIssue("error", f"Invalid mirror lockfile `{lock_path}`: {exc}"))
            payload = None
        if payload is not None:
            if not isinstance(payload, dict):
                issues.append(
                    HealthIssue("error", f"Invalid mirror lockfile `{lock_path}`: top-level JSON must be an object.")
                )
            else:
                lock_payload = payload
                if payload.get("schema_version") != MIRROR_LOCK_SCHEMA_VERSION:
                    issues.append(
                        HealthIssue(
                            "error",
                            f"Mirror lockfile `{lock_path}` has unsupported schema_version "
                            f"`{payload.get('schema_version')}`; expected `{MIRROR_LOCK_SCHEMA_VERSION}`.",
                        )
                    )

    if agents_text and lock_payload is not None:
        if lock_payload.get("canonical_contract") != DEFAULT_CANONICAL_CONTRACT:
            issues.append(
                HealthIssue(
                    "error",
                    f"Mirror lockfile `{lock_path}` must declare `canonical_contract` as `{DEFAULT_CANONICAL_CONTRACT}`.",
                )
            )
        if lock_payload.get("source_checksum") != agents_checksum:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"`{DEFAULT_CANONICAL_CONTRACT}` has changed since the last `workflow sync`; mirror lock is stale.",
                )
            )

    lock_shims = lock_payload.get("shims") if isinstance(lock_payload, dict) else None
    if lock_payload is not None and lock_shims is not None and not isinstance(lock_shims, dict):
        issues.append(HealthIssue("error", f"Mirror lockfile `{lock_path}` must declare `shims` as an object."))
        lock_shims = None
    lock_claude_adapters = lock_payload.get("claude_adapters") if isinstance(lock_payload, dict) else None
    if (
        lock_payload is not None
        and lock_claude_adapters is not None
        and not isinstance(lock_claude_adapters, dict)
    ):
        issues.append(
            HealthIssue("error", f"Mirror lockfile `{lock_path}` must declare `claude_adapters` as an object.")
        )
        lock_claude_adapters = None
    lock_opencode_adapters = lock_payload.get("opencode_adapters") if isinstance(lock_payload, dict) else None
    if (
        lock_payload is not None
        and lock_opencode_adapters is not None
        and not isinstance(lock_opencode_adapters, dict)
    ):
        issues.append(
            HealthIssue("error", f"Mirror lockfile `{lock_path}` must declare `opencode_adapters` as an object.")
        )
        lock_opencode_adapters = None
    lock_droid_adapters = lock_payload.get("droid_adapters") if isinstance(lock_payload, dict) else None
    if (
        lock_payload is not None
        and lock_droid_adapters is not None
        and not isinstance(lock_droid_adapters, dict)
    ):
        issues.append(
            HealthIssue("error", f"Mirror lockfile `{lock_path}` must declare `droid_adapters` as an object.")
        )
        lock_droid_adapters = None
    lock_gemini_adapters = lock_payload.get("gemini_adapters") if isinstance(lock_payload, dict) else None
    if (
        lock_payload is not None
        and lock_gemini_adapters is not None
        and not isinstance(lock_gemini_adapters, dict)
    ):
        issues.append(
            HealthIssue("error", f"Mirror lockfile `{lock_path}` must declare `gemini_adapters` as an object.")
        )
        lock_gemini_adapters = None
    lock_role_shims = lock_payload.get("role_shims") if isinstance(lock_payload, dict) else None
    if lock_payload is not None and lock_role_shims is not None and not isinstance(lock_role_shims, dict):
        issues.append(HealthIssue("error", f"Mirror lockfile `{lock_path}` must declare `role_shims` as an object."))
        lock_role_shims = None

    for filename in SHIMS:
        shim_path = repo / filename
        if not shim_path.exists():
            issues.append(HealthIssue("error", f"Missing generated shim `{filename}`."))
            continue

        shim_text = read_text(shim_path)
        parsed = parse_generated_shim(shim_text)
        if parsed is None:
            issues.append(HealthIssue("error", f"`{filename}` is not in the managed shim format."))
            continue

        if agents_text:
            expected = render_shim(filename, project_name, agents_text, parsed["unmanaged"])
        else:
            expected = ""

        if lock_shims is None:
            if agents_text and shim_text != expected:
                issues.append(HealthIssue("error", f"`{filename}` is drifting from the current `{DEFAULT_CANONICAL_CONTRACT}` render."))
            continue
        locked = lock_shims.get(filename)
        if locked is None:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"Mirror lockfile `{lock_path}` is missing an entry for `{filename}`; run `workflow sync`.",
                )
            )
            continue
        if not isinstance(locked, dict):
            issues.append(
                HealthIssue("error", f"Mirror lockfile entry for `{filename}` must be an object.")
            )
            continue

        managed_checksum = sha256_text(parsed["managed"])
        if agents_text and shim_text != expected:
            if managed_checksum == locked.get("managed_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{filename}` is stale relative to `{DEFAULT_CANONICAL_CONTRACT}`; run `workflow sync`.",
                    )
                )
            else:
                issues.append(HealthIssue("error", f"`{filename}` is drifting from the current `{DEFAULT_CANONICAL_CONTRACT}` render."))
        elif agents_text and shim_text == expected:
            if managed_checksum != locked.get("managed_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{filename}` managed checksum does not match the mirror lockfile; run `workflow sync`.",
                )
            )

    role_shim_paths = []
    if isinstance(lock_payload, dict):
        role_shim_paths = [
            relative_path
            for relative_path in lock_payload.get("generated_role_shims", [])
            if isinstance(relative_path, str)
        ]
    if not role_shim_paths:
        try:
            manifest = load_manifest(repo)
        except WorkflowError:
            manifest = {}
        role_shim_paths = [
            relative_path
            for relative_path in manifest.get("generated_role_shims", [])
            if relative_path in GENERATED_ROLE_SHIMS
        ]

    for relative_path in role_shim_paths:
        if relative_path not in GENERATED_ROLE_SHIMS:
            continue
        role_path = repo / relative_path
        if not role_path.exists():
            issues.append(HealthIssue("error", f"Missing generated role pointer `{relative_path}`."))
            continue

        role_text = read_text(role_path)
        parsed_role = parse_generated_role_shim(role_text)
        if parsed_role is None:
            issues.append(HealthIssue("error", f"`{relative_path}` is not in the managed role-pointer format."))
            continue

        expected_role = render_role_shim()
        if lock_role_shims is None:
            if lock_payload is not None:
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"Mirror lockfile `{lock_path}` is missing role-pointer entries; run `workflow sync`.",
                    )
                )
            if role_text != expected_role:
                issues.append(HealthIssue("error", f"`{relative_path}` is drifting from the generated role-pointer render."))
            continue

        locked_role = lock_role_shims.get(relative_path)
        if locked_role is None:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"Mirror lockfile `{lock_path}` is missing an entry for `{relative_path}`; run `workflow sync`.",
                )
            )
            continue
        if not isinstance(locked_role, dict):
            issues.append(HealthIssue("error", f"Mirror lockfile entry for `{relative_path}` must be an object."))
            continue

        current_checksum = sha256_text(role_text)
        if role_text != expected_role:
            if current_checksum == locked_role.get("full_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{relative_path}` is stale relative to the generated role-pointer render; run `workflow sync`.",
                    )
                )
            else:
                issues.append(HealthIssue("error", f"`{relative_path}` is drifting from the generated role-pointer render."))
        elif current_checksum != locked_role.get("full_checksum"):
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"`{relative_path}` checksum does not match the mirror lockfile; run `workflow sync`.",
                )
            )

    for relative_path in manifest_managed_adapter_paths(
        manifest_payload,
        "generated_claude_adapters",
        MANAGED_CLAUDE_ADAPTERS,
    ):
        adapter_path = repo / relative_path
        if not adapter_path.exists():
            issues.append(HealthIssue("error", f"Missing generated Claude adapter `{relative_path}`."))
            continue

        adapter_text = read_text(adapter_path)
        parsed_adapter = parse_generated_claude_adapter(adapter_text)
        if parsed_adapter is None:
            issues.append(HealthIssue("error", f"`{relative_path}` is not in the managed Claude adapter format."))
            continue

        expected_adapter = render_claude_adapter(relative_path)
        if lock_claude_adapters is None:
            if lock_payload is not None:
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"Mirror lockfile `{lock_path}` is missing Claude adapter entries; run `workflow sync`.",
                    )
                )
            if adapter_text != expected_adapter:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated Claude adapter render.")
                )
            continue

        locked_adapter = lock_claude_adapters.get(relative_path)
        if locked_adapter is None:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"Mirror lockfile `{lock_path}` is missing an entry for `{relative_path}`; run `workflow sync`.",
                )
            )
            continue
        if not isinstance(locked_adapter, dict):
            issues.append(HealthIssue("error", f"Mirror lockfile entry for `{relative_path}` must be an object."))
            continue

        current_checksum = sha256_text(adapter_text)
        if adapter_text != expected_adapter:
            if current_checksum == locked_adapter.get("full_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{relative_path}` is stale relative to the generated Claude adapter render; run `workflow sync`.",
                    )
                )
            else:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated Claude adapter render.")
                )
        elif current_checksum != locked_adapter.get("full_checksum"):
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"`{relative_path}` checksum does not match the mirror lockfile; run `workflow sync`.",
                )
            )

    for relative_path in manifest_managed_adapter_paths(
        manifest_payload,
        "generated_opencode_adapters",
        MANAGED_OPENCODE_ADAPTERS,
    ):
        adapter_path = repo / relative_path
        if not adapter_path.exists():
            issues.append(HealthIssue("error", f"Missing generated OpenCode adapter `{relative_path}`."))
            continue

        adapter_text = read_text(adapter_path)
        parsed_adapter = parse_generated_opencode_adapter(adapter_text)
        if parsed_adapter is None:
            issues.append(HealthIssue("error", f"`{relative_path}` is not in the managed OpenCode adapter format."))
            continue

        expected_adapter = render_opencode_adapter(relative_path)
        if lock_opencode_adapters is None:
            if lock_payload is not None:
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"Mirror lockfile `{lock_path}` is missing OpenCode adapter entries; run `workflow sync`.",
                    )
                )
            if adapter_text != expected_adapter:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated OpenCode adapter render.")
                )
            continue

        locked_adapter = lock_opencode_adapters.get(relative_path)
        if locked_adapter is None:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"Mirror lockfile `{lock_path}` is missing an entry for `{relative_path}`; run `workflow sync`.",
                )
            )
            continue
        if not isinstance(locked_adapter, dict):
            issues.append(HealthIssue("error", f"Mirror lockfile entry for `{relative_path}` must be an object."))
            continue

        current_checksum = sha256_text(adapter_text)
        if adapter_text != expected_adapter:
            if current_checksum == locked_adapter.get("full_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{relative_path}` is stale relative to the generated OpenCode adapter render; run `workflow sync`.",
                    )
                )
            else:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated OpenCode adapter render.")
                )
        elif current_checksum != locked_adapter.get("full_checksum"):
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"`{relative_path}` checksum does not match the mirror lockfile; run `workflow sync`.",
                )
            )

    for relative_path in manifest_managed_adapter_paths(
        manifest_payload,
        "generated_droid_adapters",
        MANAGED_DROID_ADAPTERS,
    ):
        adapter_path = repo / relative_path
        if not adapter_path.exists():
            issues.append(HealthIssue("error", f"Missing generated Factory Droid adapter `{relative_path}`."))
            continue

        adapter_text = read_text(adapter_path)
        parsed_adapter = parse_generated_droid_adapter(adapter_text)
        if parsed_adapter is None:
            issues.append(HealthIssue("error", f"`{relative_path}` is not in the managed Factory Droid adapter format."))
            continue

        expected_adapter = render_droid_adapter(relative_path)
        if lock_droid_adapters is None:
            if lock_payload is not None:
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"Mirror lockfile `{lock_path}` is missing Factory Droid adapter entries; run `workflow sync`.",
                    )
                )
            if adapter_text != expected_adapter:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated Factory Droid adapter render.")
                )
            continue

        locked_adapter = lock_droid_adapters.get(relative_path)
        if locked_adapter is None:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"Mirror lockfile `{lock_path}` is missing an entry for `{relative_path}`; run `workflow sync`.",
                )
            )
            continue
        if not isinstance(locked_adapter, dict):
            issues.append(HealthIssue("error", f"Mirror lockfile entry for `{relative_path}` must be an object."))
            continue

        current_checksum = sha256_text(adapter_text)
        if adapter_text != expected_adapter:
            if current_checksum == locked_adapter.get("full_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{relative_path}` is stale relative to the generated Factory Droid adapter render; run `workflow sync`.",
                    )
                )
            else:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated Factory Droid adapter render.")
                )
        elif current_checksum != locked_adapter.get("full_checksum"):
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"`{relative_path}` checksum does not match the mirror lockfile; run `workflow sync`.",
                )
            )

    for relative_path in manifest_managed_adapter_paths(
        manifest_payload,
        "generated_gemini_adapters",
        MANAGED_GEMINI_ADAPTERS,
    ):
        adapter_path = repo / relative_path
        if not adapter_path.exists():
            issues.append(HealthIssue("error", f"Missing generated Gemini adapter `{relative_path}`."))
            continue

        adapter_text = read_text(adapter_path)
        parsed_adapter = parse_generated_gemini_adapter(adapter_text)
        if parsed_adapter is None:
            issues.append(HealthIssue("error", f"`{relative_path}` is not in the managed Gemini adapter format."))
            continue

        expected_adapter = render_gemini_adapter(relative_path)
        if lock_gemini_adapters is None:
            if lock_payload is not None:
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"Mirror lockfile `{lock_path}` is missing Gemini adapter entries; run `workflow sync`.",
                    )
                )
            if adapter_text != expected_adapter:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated Gemini adapter render.")
                )
            continue

        locked_adapter = lock_gemini_adapters.get(relative_path)
        if locked_adapter is None:
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"Mirror lockfile `{lock_path}` is missing an entry for `{relative_path}`; run `workflow sync`.",
                )
            )
            continue
        if not isinstance(locked_adapter, dict):
            issues.append(HealthIssue("error", f"Mirror lockfile entry for `{relative_path}` must be an object."))
            continue

        current_checksum = sha256_text(adapter_text)
        if adapter_text != expected_adapter:
            if current_checksum == locked_adapter.get("full_checksum"):
                sync_needed = True
                issues.append(
                    HealthIssue(
                        "warning",
                        f"`{relative_path}` is stale relative to the generated Gemini adapter render; run `workflow sync`.",
                    )
                )
            else:
                issues.append(
                    HealthIssue("error", f"`{relative_path}` is drifting from the generated Gemini adapter render.")
                )
        elif current_checksum != locked_adapter.get("full_checksum"):
            sync_needed = True
            issues.append(
                HealthIssue(
                    "warning",
                    f"`{relative_path}` checksum does not match the mirror lockfile; run `workflow sync`.",
                )
            )

    failure_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if failure_count:
        summary = issues[0].message if failure_count == 1 and warning_count == 0 else f"{failure_count} mirror-lock/shim issue(s) detected."
        status = "fail"
    elif warning_count:
        summary = "Mirror lock/shim state is structurally valid, but `workflow sync` is needed."
        status = "warning"
    else:
        summary = "Mirror lock, AGENTS.md, generated shims, and managed adapters are aligned."
        status = "pass"

    return MirrorHealth(
        lock_path=lock_path,
        status=status,
        summary=summary,
        sync_needed=sync_needed,
        issues=issues,
    )


def evaluate_continuity_state_health(
    repo: Path,
    manifest_health: ManifestHealth | None = None,
) -> ContinuityStateHealth:
    state_root = repo / DEFAULT_STATE_ROOT
    issues: list[HealthIssue] = []
    file_issues: dict[str, list[HealthIssue]] = {filename: [] for filename in CONTINUITY_STATE_FILES}

    def add_issue(filename: str, message: str, *, level: str = "error") -> None:
        issue = HealthIssue(level, message)
        file_issues[filename].append(issue)
        issues.append(issue)

    def load_file(filename: str) -> str | None:
        relative_path = f"{DEFAULT_STATE_ROOT}/{filename}"
        path = state_root / filename
        if not path.exists():
            add_issue(filename, f"Missing continuity-state file `{relative_path}`.")
            return None
        text = read_text(path)
        if not text.strip():
            add_issue(filename, f"Continuity-state file `{relative_path}` is empty.")
            return None
        return text

    active_text = load_file("active.md")
    if active_text is not None:
        current_task = extract_section(active_text, ["Current task"])
        if not current_task or not current_task.strip():
            add_issue("active.md", "`.specify/state/active.md` is missing a current-task signal.")
        pointer = extract_section(active_text, ["Active spec/task pointer"])
        if not pointer or not pointer.strip():
            add_issue(
                "active.md",
                "`.specify/state/active.md` is missing an active spec/task pointer or explicit no-active-spec note.",
            )
        else:
            pointer_normalized = pointer.lower()
            if "no active spec" not in pointer_normalized:
                candidates = extract_relative_path_candidates(pointer)
                if not candidates:
                    add_issue(
                        "active.md",
                        "`.specify/state/active.md` does not declare a valid spec/task pointer or an explicit no-active-spec note.",
                    )
                else:
                    has_existing_reference = False
                    for relative in candidates:
                        if (repo / relative).exists():
                            has_existing_reference = True
                        else:
                            add_issue("active.md", f"`.specify/state/active.md` references missing path `{relative}`.")
                    if not has_existing_reference and not any(
                        "references missing path" in issue.message for issue in file_issues["active.md"]
                    ):
                        add_issue(
                            "active.md",
                            "`.specify/state/active.md` does not declare a valid spec/task pointer or an explicit no-active-spec note.",
                        )

    handoff_text = load_file("handoff.md")
    if handoff_text is not None:
        next_step = extract_section(handoff_text, ["What to do next"])
        if not next_step or not next_step.strip():
            add_issue("handoff.md", "`.specify/state/handoff.md` is missing a next-step handoff signal.")

    progress_text = load_file("progress.md")
    if progress_text is not None:
        recent_progress = extract_section(progress_text, ["Recent progress"])
        if not recent_progress or not recent_progress.strip():
            add_issue("progress.md", "`.specify/state/progress.md` is missing a recent-progress signal.")

    session_text = load_file("session.log.md")
    if session_text is not None:
        entries_section = extract_section(session_text, ["Entries"])
        if not entries_section or not entries_section.strip():
            add_issue("session.log.md", "`.specify/state/session.log.md` is missing session entries.")
        else:
            entries = [line for line in entries_section.splitlines() if line.strip().startswith("- ")]
            if not entries:
                add_issue(
                    "session.log.md",
                    "`.specify/state/session.log.md` must contain session entries as bullet lines starting with `- `.",
                )

    migration_text = load_file("migration.md")
    if migration_text is not None:
        current_state = extract_section(migration_text, ["Current state"])
        if not current_state or not current_state.strip():
            add_issue("migration.md", "`.specify/state/migration.md` is missing a migration-state signal.")
        else:
            fields = parse_keyed_bullets(current_state)
            if not fields.get("status"):
                add_issue("migration.md", "`.specify/state/migration.md` is missing a migration status signal.")
            if not fields.get("phase"):
                add_issue("migration.md", "`.specify/state/migration.md` is missing a migration phase signal.")
            if not fields.get("legacy preserved"):
                add_issue("migration.md", "`.specify/state/migration.md` is missing a legacy-preserved signal.")

            if manifest_health is not None and manifest_health.status == "pass" and manifest_health.manifest is not None:
                manifest_migration = manifest_health.manifest.get("migration", {})
                expected_status = str(manifest_migration.get("status", "")).strip()
                expected_phase = str(manifest_migration.get("phase", "")).strip()
                expected_legacy = "yes" if manifest_migration.get("legacy_preserved") else "no"

                actual_status = fields.get("status", "")
                actual_phase = fields.get("phase", "")
                actual_legacy = fields.get("legacy preserved", "")

                if expected_status and actual_status and normalize_heading(actual_status) != normalize_heading(expected_status):
                    add_issue(
                        "migration.md",
                        "`.specify/state/migration.md` status "
                        f"`{actual_status}` does not match manifest migration status `{expected_status}`.",
                    )
                if expected_phase and actual_phase and normalize_heading(actual_phase) != normalize_heading(expected_phase):
                    add_issue(
                        "migration.md",
                        "`.specify/state/migration.md` phase "
                        f"`{actual_phase}` does not match manifest migration phase `{expected_phase}`.",
                    )
                if actual_legacy and normalize_heading(actual_legacy) != normalize_heading(expected_legacy):
                    add_issue(
                        "migration.md",
                        "`.specify/state/migration.md` legacy-preserved value "
                        f"`{actual_legacy}` does not match manifest value `{expected_legacy}`.",
                    )

        migration_lower = migration_text.lower()
        misleading_claims = [
            (
                "hermes is implemented",
                "`.specify/state/migration.md` claims Hermes is implemented, but Hermes remains intentionally out of scope.",
            ),
            (
                "spec-kit fork/preset is implemented",
                "`.specify/state/migration.md` claims a spec-kit fork/preset is implemented, but the repo still uses a repo-local safe slice.",
            ),
        ]
        for needle, message in misleading_claims:
            if needle in migration_lower:
                add_issue("migration.md", message)

    entries: list[ContinuityStateEntry] = []
    for filename in CONTINUITY_STATE_FILES:
        relative_path = f"{DEFAULT_STATE_ROOT}/{filename}"
        per_file_issues = file_issues[filename]
        if per_file_issues:
            status = "fail" if any(issue.level == "error" for issue in per_file_issues) else "warning"
            summary = per_file_issues[0].message
        else:
            status = "pass"
            summary = f"`{relative_path}` looks healthy."
        entries.append(
            ContinuityStateEntry(
                relative_path=relative_path,
                status=status,
                summary=summary,
            )
        )

    failure_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if failure_count:
        affected_files = sum(1 for entry in entries if entry.status == "fail")
        if failure_count == 1:
            summary = issues[0].message
        else:
            summary = f"{failure_count} continuity-state issue(s) detected across {affected_files} file(s)."
        status = "fail"
    elif warning_count:
        summary = issues[0].message if warning_count == 1 else f"{warning_count} continuity-state warning(s) detected."
        status = "warning"
    else:
        status = "pass"
        summary = f"All {len(CONTINUITY_STATE_FILES)} continuity-state files are structurally healthy."

    return ContinuityStateHealth(
        state_root=state_root,
        status=status,
        summary=summary,
        entries=entries,
        issues=issues,
    )


def evaluate_memory_health(
    repo: Path,
    manifest_health: ManifestHealth | None = None,
) -> MemoryHealth:
    memory_root = repo / DEFAULT_MEMORY_ROOT
    issues: list[HealthIssue] = []
    file_issues: dict[str, list[HealthIssue]] = {filename: [] for filename in MEMORY_FILES}

    def add_issue(filename: str, message: str, *, level: str = "error") -> None:
        issue = HealthIssue(level, message)
        file_issues[filename].append(issue)
        issues.append(issue)

    def load_file(filename: str) -> str | None:
        relative_path = f"{DEFAULT_MEMORY_ROOT}/{filename}"
        path = memory_root / filename
        if not path.exists():
            add_issue(filename, f"Missing memory file `{relative_path}`.")
            return None
        text = read_text(path)
        if not text.strip():
            add_issue(filename, f"Memory file `{relative_path}` is empty.")
            return None
        return text

    def check_misleading_claims(filename: str, text: str) -> None:
        lower = text.lower()
        misleading_claims = [
            (
                "hermes is implemented",
                f"`{DEFAULT_MEMORY_ROOT}/{filename}` claims Hermes is implemented, but Hermes remains intentionally out of scope.",
            ),
            (
                "graphify is implemented",
                f"`{DEFAULT_MEMORY_ROOT}/{filename}` claims Graphify is implemented, but Graphify remains intentionally out of scope.",
            ),
            (
                "dashscope is integrated",
                f"`{DEFAULT_MEMORY_ROOT}/{filename}` claims DashScope integration is implemented, but DashScope remains intentionally out of scope.",
            ),
            (
                "qwen integration is complete",
                f"`{DEFAULT_MEMORY_ROOT}/{filename}` claims Qwen integration is complete, but Qwen remains intentionally out of scope.",
            ),
            (
                "spec-kit fork/preset is implemented",
                f"`{DEFAULT_MEMORY_ROOT}/{filename}` claims a spec-kit fork/preset is implemented, but the repo still uses a repo-local safe slice.",
            ),
            (
                "full spec-kit fork/preset is implemented",
                f"`{DEFAULT_MEMORY_ROOT}/{filename}` claims a full spec-kit fork/preset is implemented, but the repo still uses a repo-local safe slice.",
            ),
        ]
        for needle, message in misleading_claims:
            if needle in lower:
                add_issue(filename, message)

    constitution_text = load_file("constitution.md")
    if constitution_text is not None:
        non_negotiables = extract_section(constitution_text, ["Non-negotiables", "Operating principles"])
        continuity_contract = extract_section(constitution_text, ["Continuity contract"])
        if not non_negotiables and not continuity_contract:
            add_issue(
                "constitution.md",
                "`.specify/memory/constitution.md` is missing governance or operating-principles signals.",
            )
        if "`agents.md`" not in constitution_text.lower() and "agents.md" not in constitution_text.lower():
            add_issue(
                "constitution.md",
                "`.specify/memory/constitution.md` is missing the AGENTS-as-canonical signal.",
            )
        check_misleading_claims("constitution.md", constitution_text)

    project_text = load_file("project.md")
    if project_text is not None:
        what_project = extract_section(project_text, ["What this project is"])
        stable_facts = extract_section(project_text, ["Stable facts"])
        if not what_project or not what_project.strip():
            add_issue(
                "project.md",
                "`.specify/memory/project.md` is missing a project identity or purpose signal.",
            )
        elif "unavailable." in what_project.lower():
            add_issue(
                "project.md",
                "`.specify/memory/project.md` is missing a project identity or purpose signal.",
            )
        if not stable_facts or not stable_facts.strip():
            add_issue(
                "project.md",
                "`.specify/memory/project.md` is missing stable project signals.",
            )
        check_misleading_claims("project.md", project_text)

    decisions_text = load_file("decisions.md")
    if decisions_text is not None:
        durable_decisions = extract_section(decisions_text, ["Durable decisions", "Decisions"])
        if not durable_decisions or not durable_decisions.strip():
            add_issue(
                "decisions.md",
                "`.specify/memory/decisions.md` is missing a durable-decisions signal.",
            )
        else:
            decision_lines = [line for line in durable_decisions.splitlines() if line.strip().startswith("- ")]
            if not decision_lines:
                add_issue(
                    "decisions.md",
                    "`.specify/memory/decisions.md` does not record any durable decisions.",
                )
        has_legacy = (repo / DEFAULT_LEGACY_ROOT).exists()
        manifest = manifest_health.manifest if manifest_health is not None and manifest_health.status == "pass" else None
        migration_status = manifest.get("migration", {}).get("status") if isinstance(manifest, dict) else None
        if has_legacy and migration_status in {"coexist", "legacy"}:
            if ".ai/" not in decisions_text and "legacy `.ai/`" not in decisions_text:
                add_issue(
                    "decisions.md",
                    "`.specify/memory/decisions.md` is missing the intentional legacy `.ai/` coexistence signal.",
                )
        check_misleading_claims("decisions.md", decisions_text)

    architecture_text = load_file("architecture.md")
    if architecture_text is not None:
        layers = extract_section(architecture_text, ["Layers", "Architecture"])
        command_model = extract_section(architecture_text, ["Command model"])
        if not layers or not layers.strip():
            add_issue(
                "architecture.md",
                "`.specify/memory/architecture.md` is missing an architecture or layering signal.",
            )
        if not command_model or not command_model.strip():
            add_issue(
                "architecture.md",
                "`.specify/memory/architecture.md` is missing a command-model signal.",
            )
        else:
            lower = command_model.lower()
            if "`workflow`" not in command_model and "workflow" not in lower:
                add_issue(
                    "architecture.md",
                    "`.specify/memory/architecture.md` is missing the CLI-authority signal.",
                )
            if "project-*" not in command_model and "wrapper" not in lower:
                add_issue(
                    "architecture.md",
                    "`.specify/memory/architecture.md` is missing the wrapper-compatibility signal.",
                )
        check_misleading_claims("architecture.md", architecture_text)

    tech_text = load_file("tech.md")
    if tech_text is not None:
        stack = extract_section(tech_text, ["Stack"])
        core_commands = extract_section(tech_text, ["Core commands"])
        if not stack or not stack.strip():
            add_issue(
                "tech.md",
                "`.specify/memory/tech.md` is missing a runtime or tooling signal.",
            )
        else:
            lower = stack.lower()
            if "python" not in lower:
                add_issue(
                    "tech.md",
                    "`.specify/memory/tech.md` is missing the Python CLI runtime signal.",
                )
            if "zsh" not in lower and "scripts/workflow.sh" not in stack:
                add_issue(
                    "tech.md",
                    "`.specify/memory/tech.md` is missing the shell-wrapper signal.",
                )
        if not core_commands or not core_commands.strip():
            add_issue(
                "tech.md",
                "`.specify/memory/tech.md` is missing a core-commands signal.",
            )
        check_misleading_claims("tech.md", tech_text)

    entries: list[MemoryEntry] = []
    for filename in MEMORY_FILES:
        relative_path = f"{DEFAULT_MEMORY_ROOT}/{filename}"
        per_file_issues = file_issues[filename]
        if per_file_issues:
            status = "fail" if any(issue.level == "error" for issue in per_file_issues) else "warning"
            summary = per_file_issues[0].message
        else:
            status = "pass"
            summary = f"`{relative_path}` looks healthy."
        entries.append(MemoryEntry(relative_path=relative_path, status=status, summary=summary))

    failure_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if failure_count:
        affected_files = sum(1 for entry in entries if entry.status == "fail")
        summary = issues[0].message if failure_count == 1 else f"{failure_count} memory-health issue(s) detected across {affected_files} file(s)."
        status = "fail"
    elif warning_count:
        summary = issues[0].message if warning_count == 1 else f"{warning_count} memory-health warning(s) detected."
        status = "warning"
    else:
        status = "pass"
        summary = f"All {len(MEMORY_FILES)} memory files are structurally healthy."

    return MemoryHealth(
        memory_root=memory_root,
        status=status,
        summary=summary,
        entries=entries,
        issues=issues,
    )


def subparser_choices(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if getattr(action, "dest", None) == "command" and isinstance(choices, dict):
            return choices
    return {}


def build_cli_surface_snapshot(parser: argparse.ArgumentParser | None = None) -> CliSurfaceSnapshot:
    parser = parser or build_parser()
    choices = subparser_choices(parser)
    help_texts = {"workflow": parser.format_help()}
    for name, subparser in choices.items():
        help_texts[f"workflow {name}"] = subparser.format_help()
    return CliSurfaceSnapshot(
        commands=sorted(choices.keys()),
        help_texts=help_texts,
    )


def line_has_guidance_exemption(line: str) -> bool:
    lower = line.lower()
    return any(token in lower for token in GUIDANCE_EXEMPTION_TOKENS)


def scan_stale_live_guidance(source_label: str, text: str) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if line_has_guidance_exemption(lower):
            continue

        if "scripts/workflow.sh" in lower and "edit" in lower and "root" in lower:
            issues.append(
                HealthIssue(
                    "error",
                    f"`{source_label}` line {line_number} tells users to edit `scripts/workflow.sh` for live root management; roots belong in `.workflow/roots.json`.",
                )
            )
        if ".ai/context/scaffold-template" in lower and any(
            token in lower
            for token in ("primary", "new-project scaffold", "new project scaffold", "create", "copy")
        ):
            issues.append(
                HealthIssue(
                    "error",
                    f"`{source_label}` line {line_number} treats `.ai/context/scaffold-template` as live v2 scaffold guidance.",
                )
            )
        if ".ai/handoffs/next_step.md" in lower and any(
            token in lower for token in ("canonical", "primary", "for v2", "v2 repo", "v2 repos")
        ):
            issues.append(
                HealthIssue(
                    "error",
                    f"`{source_label}` line {line_number} treats `.ai/handoffs/NEXT_STEP.md` as canonical v2 guidance.",
                )
            )
        if ".ai/logs/session.log" in lower and any(
            token in lower for token in ("canonical", "primary", "for v2", "v2 repo", "v2 repos")
        ):
            issues.append(
                HealthIssue(
                    "error",
                    f"`{source_label}` line {line_number} treats `.ai/logs/session.log` as the primary v2 session log.",
                )
            )

        implementation_claims = [
            (
                "hermes is implemented",
                f"`{source_label}` line {line_number} claims Hermes is implemented, but Hermes remains intentionally out of scope.",
            ),
            (
                "dashscope is integrated",
                f"`{source_label}` line {line_number} claims DashScope integration is implemented, but DashScope remains intentionally out of scope.",
            ),
            (
                "qwen integration is complete",
                f"`{source_label}` line {line_number} claims Qwen integration is implemented, but Qwen remains intentionally out of scope.",
            ),
            (
                "graphify is implemented",
                f"`{source_label}` line {line_number} claims Graphify is implemented, but Graphify remains intentionally out of scope.",
            ),
            (
                "full spec-kit fork/preset is implemented",
                f"`{source_label}` line {line_number} claims a full spec-kit fork/preset is implemented, but the repo still uses a repo-local safe slice.",
            ),
            (
                "spec-kit fork/preset is implemented",
                f"`{source_label}` line {line_number} claims a spec-kit fork/preset is implemented, but the repo still uses a repo-local safe slice.",
            ),
        ]
        for needle, message in implementation_claims:
            if needle in lower:
                issues.append(HealthIssue("error", message))

    return issues


def script_defines_function(script_text: str, name: str) -> bool:
    return any(line.strip().startswith(f"{name}()") for line in script_text.splitlines())


def evaluate_command_docs_health(
    *,
    manager_home: Path | None = None,
    cli_snapshot: CliSurfaceSnapshot | None = None,
    readme_text: str | None = None,
    agents_text: str | None = None,
    script_text: str | None = None,
) -> CommandDocsHealth:
    manager_home = manager_home or workflow_manager_home()
    issues: list[HealthIssue] = []
    surface_issues: dict[str, list[HealthIssue]] = {
        "CLI command surface": [],
        "CLI help": [],
        "Wrapper command surface": [],
        "README.md": [],
        "AGENTS.md": [],
        "scripts/workflow.sh": [],
    }

    def add_issue(surface: str, message: str, *, level: str = "error") -> None:
        issue = HealthIssue(level, message)
        surface_issues[surface].append(issue)
        issues.append(issue)

    snapshot = cli_snapshot or build_cli_surface_snapshot()
    command_set = set(snapshot.commands)
    main_help = snapshot.help_texts.get("workflow", "")

    for command in EXPECTED_WORKFLOW_COMMANDS:
        if command not in command_set:
            add_issue("CLI command surface", f"CLI command `{command}` is missing from the workflow command surface.")
        if command not in main_help:
            add_issue("CLI help", f"`workflow --help` does not list expected command `{command}`.")

    help_requirements = [
        (
            "workflow sync",
            "AGENTS.md",
            "`workflow sync --help` must keep `AGENTS.md` as the canonical shim source.",
        ),
        (
            "workflow roots",
            "repo-owned config",
            "`workflow roots --help` must describe `.workflow/roots.json` as repo-owned config.",
        ),
        (
            "workflow open",
            "repo-owned workspace roots",
            "`workflow open --help` must describe `--roots` as an override for repo-owned workspace roots.",
        ),
        (
            "workflow list",
            "repo-owned workspace roots",
            "`workflow list --help` must describe `--roots` as an override for repo-owned workspace roots.",
        ),
    ]
    for label, needle, message in help_requirements:
        if needle not in snapshot.help_texts.get(label, ""):
            add_issue("CLI help", message)

    for label, help_text in snapshot.help_texts.items():
        for issue in scan_stale_live_guidance(f"{label} help", help_text):
            add_issue("CLI help", issue.message, level=issue.level)

    readme_path = manager_home / "README.md"
    if readme_text is None:
        if readme_path.exists():
            readme_text = read_text(readme_path)
        else:
            add_issue("README.md", f"Missing `{readme_path}`.")
            readme_text = ""
    for issue in scan_stale_live_guidance("README.md", readme_text):
        add_issue("README.md", issue.message, level=issue.level)

    agents_path = manager_home / "AGENTS.md"
    if agents_text is None:
        if agents_path.exists():
            agents_text = read_text(agents_path)
        else:
            add_issue("AGENTS.md", f"Missing `{agents_path}`.")
            agents_text = ""
    for issue in scan_stale_live_guidance("AGENTS.md", agents_text):
        add_issue("AGENTS.md", issue.message, level=issue.level)

    script_path = manager_home / "scripts/workflow.sh"
    if script_text is None:
        if script_path.exists():
            script_text = read_text(script_path)
        else:
            add_issue("scripts/workflow.sh", f"Missing `{script_path}`.")
            script_text = ""
    for name in EXPECTED_WRAPPER_COMMANDS:
        if script_text and not script_defines_function(script_text, name):
            add_issue("Wrapper command surface", f"Wrapper command `{name}` is missing from `scripts/workflow.sh`.")
    for issue in scan_stale_live_guidance("scripts/workflow.sh", script_text):
        add_issue("scripts/workflow.sh", issue.message, level=issue.level)

    entries: list[CommandDocsEntry] = []
    for surface, per_surface in surface_issues.items():
        if per_surface:
            status = "fail" if any(issue.level == "error" for issue in per_surface) else "warning"
            summary = per_surface[0].message
        else:
            status = "pass"
            summary = f"{surface} aligns with the current v2 workflow model."
        entries.append(CommandDocsEntry(surface=surface, status=status, summary=summary))

    failure_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if failure_count:
        affected = sum(1 for entry in entries if entry.status == "fail")
        summary = issues[0].message if failure_count == 1 else (
            f"{failure_count} command/help/docs consistency issue(s) detected across {affected} surface(s)."
        )
        status = "fail"
    elif warning_count:
        summary = issues[0].message if warning_count == 1 else f"{warning_count} command/help/docs surface(s) need review."
        status = "warning"
    else:
        status = "pass"
        summary = "CLI commands, wrapper guidance, help text, and repo docs align with the current v2 model."

    return CommandDocsHealth(
        manager_home=manager_home,
        status=status,
        summary=summary,
        entries=entries,
        issues=issues,
    )


def evaluate_role_contract_health(repo: Path) -> RoleContractHealth:
    issues: list[HealthIssue] = []
    contract_path = repo / "ROLES.md"
    global_contract_path = Path.home() / "ROLES.md"

    try:
        payload = validate_role_contract_payload()
    except ValueError as error:
        payload = {
            "canonical_roles": list(CANONICAL_ROLES),
            "reserved_roles": list(RESERVED_ROLES),
            "supported_harnesses": list(SUPPORTED_ROLE_CONTRACT_HARNESSES),
        }
        issues.append(HealthIssue("error", f"Runtime role contract helper drifted: {error}"))

    if not global_contract_path.exists():
        issues.append(HealthIssue("error", f"Missing global canonical role contract `{ROLE_CONTRACT_SOURCE}`."))
        global_text = ""
    else:
        global_text = read_text(global_contract_path)

    local_pointer_required = repo.resolve() == workflow_manager_home()
    if not contract_path.exists() and local_pointer_required:
        issues.append(HealthIssue("error", f"Missing workflow-manager local role pointer `{contract_path}`."))
        local_text = ""
    elif not contract_path.exists():
        local_text = ""
    else:
        local_text = read_text(contract_path)

    for role in CANONICAL_ROLES:
        heading = role.title()
        if global_text and f"### {heading}" not in global_text:
            issues.append(HealthIssue("error", f"Global role contract is missing `{heading}`."))
        policy = ROLE_ACTION_CATEGORIES.get(role)
        if not policy or not policy.get("allowed") or not policy.get("forbidden"):
            issues.append(HealthIssue("error", f"Runtime role contract is missing action categories for `{role}`."))

    for role in RESERVED_ROLES:
        if global_text and role.title() not in global_text:
            issues.append(HealthIssue("error", f"Global role contract is missing reserved `{role}` slot."))

    if local_text:
        if ROLE_CONTRACT_SOURCE not in local_text:
            issues.append(HealthIssue("error", f"Local `ROLES.md` must point at `{ROLE_CONTRACT_SOURCE}`."))
        for forbidden_heading in ("### Architect", "### Coder", "### Verifier"):
            if forbidden_heading in local_text:
                issues.append(HealthIssue("error", "Local `ROLES.md` must not redefine canonical role prose."))
                break
        if local_pointer_required:
            for harness in ("Claude Code CLI", "OpenCode", "Factory Droid", "Codex CLI", "Gemini CLI", "Antigravity IDE", "Cursor"):
                if harness not in local_text:
                    issues.append(HealthIssue("warning", f"Local `ROLES.md` mapping table does not mention {harness}."))

    lock_path = repo / ".workflow/mirror-lock.json"
    if lock_path.exists():
        try:
            lock_payload = json.loads(read_text(lock_path))
        except json.JSONDecodeError as error:
            issues.append(HealthIssue("warning", f"Could not inspect mirror lock for role-contract ownership: {error}."))
        else:
            if local_pointer_required and mirror_lock_declares_path(lock_payload, "ROLES.md"):
                issues.append(HealthIssue("error", "`ROLES.md` must remain hand-edited and outside mirror-lock governance."))

    failures = [issue for issue in issues if issue.level == "error"]
    warnings = [issue for issue in issues if issue.level == "warning"]
    if failures:
        status = "fail"
        summary = failures[0].message if len(failures) == 1 else f"{len(failures)} role-contract issue(s) detected."
    elif warnings:
        status = "warning"
        summary = warnings[0].message if len(warnings) == 1 else f"{len(warnings)} role-contract warning(s) need review."
    else:
        status = "pass"
        summary = "Canonical role contract, reserved Tester slot, and local pointer are aligned."

    return RoleContractHealth(
        contract_path=contract_path,
        status=status,
        summary=summary,
        canonical_roles=list(payload["canonical_roles"]),
        reserved_roles=list(payload["reserved_roles"]),
        supported_harnesses=list(payload["supported_harnesses"]),
        issues=issues,
    )


def evaluate_health_overview(
    command_docs_health: CommandDocsHealth,
    manifest_health: ManifestHealth,
    mirror_health: MirrorHealth,
    memory_health: MemoryHealth,
    continuity_health: ContinuityStateHealth,
    roots_health: RootsHealth,
    role_contract_health: RoleContractHealth,
    docs_health: DocsHealth,
) -> HealthOverview:
    subsystem_statuses = {
        "command/help/docs": command_docs_health.status,
        "manifest": manifest_health.status,
        "mirror-lock/shim": mirror_health.status,
        "memory": memory_health.status,
        "continuity-state": continuity_health.status,
        "roots": roots_health.status,
        "role-contract": role_contract_health.status,
        "docs-health": docs_health.status,
    }
    failure_count = sum(1 for status in subsystem_statuses.values() if status == "fail")
    warning_count = sum(1 for status in subsystem_statuses.values() if status == "warning")

    if failure_count:
        overall_status = "fail"
        summary = f"{failure_count} repo-owned health surface(s) are failing."
        if warning_count:
            summary += f" {warning_count} additional surface(s) need review."
    elif warning_count:
        overall_status = "warning"
        summary = f"{warning_count} repo-owned health surface(s) need review."
    else:
        overall_status = "pass"
        summary = f"All {len(subsystem_statuses)} repo-owned health surfaces pass."

    pre_hermes_readiness = {
        "fail": "blocked",
        "warning": "needs-review",
        "pass": "pre-hermes-foundation-ready",
    }[overall_status]

    return HealthOverview(
        overall_status=overall_status,
        summary=summary,
        command_docs_status=command_docs_health.status,
        manifest_status=manifest_health.status,
        mirror_status=mirror_health.status,
        memory_status=memory_health.status,
        continuity_status=continuity_health.status,
        roots_status=roots_health.status,
        role_contract_status=role_contract_health.status,
        docs_status=docs_health.status,
        sync_needed=mirror_health.sync_needed,
        default_root_operations_safe=(roots_health.status == "pass"),
        pre_hermes_readiness=pre_hermes_readiness,
    )


def apply_planned_writes(
    writes: list[PlannedWrite],
    *,
    dry_run: bool,
    force: bool,
    adopt_manual: bool = False,
) -> tuple[list[str], list[str]]:
    actions: list[str] = []
    backups: list[str] = []
    conflicts: list[str] = []
    adopt_managed_descriptions = {".workflow/workflow.json", "ROLES.md"}
    for planned in writes:
        existing = planned.path.exists()
        if existing:
            current = read_text(planned.path)
            if current == planned.content:
                actions.append(f"unchanged {planned.description}")
                continue
            if adopt_manual and planned.description not in adopt_managed_descriptions:
                actions.append(f"preserve existing {planned.description}")
                continue
            if not force:
                conflicts.append(
                    f"refusing to overwrite existing {planned.description}; rerun with `--force` to back it up first"
                )
                continue
            if not dry_run:
                backup = backup_file(planned.path)
                backups.append(str(backup))
                write_text_atomic(planned.path, planned.content)
            actions.append(f"replace {planned.description}")
            continue
        if not dry_run:
            write_text_atomic(planned.path, planned.content)
        actions.append(f"create {planned.description}")

    if conflicts:
        raise WorkflowError("\n".join(conflicts))
    return actions, backups


def ensure_init(repo: Path, *, dry_run: bool, force: bool, skip_sync: bool, adopt_manual: bool = False) -> int:
    if repo.exists() and not repo.is_dir():
        raise WorkflowError(f"`{repo}` exists but is not a directory.")

    agents_text = ensure_agents(repo)
    if adopt_manual and (repo / "AGENTS.md").exists() and ROLE_CONTRACT_SOURCE not in agents_text:
        raise WorkflowError(
            "Manual scaffold adoption requires `AGENTS.md` to point at `~/ROLES.md` before mirror-lock parity can be claimed."
        )
    writes: list[PlannedWrite] = []
    if not (repo / "AGENTS.md").exists():
        writes.append(PlannedWrite(repo / "AGENTS.md", agents_text.rstrip() + "\n", "AGENTS.md"))
    legacy_exists = (repo / ".ai").exists()
    writes.extend(build_seed_files(repo, collect_context(repo, agents_text), legacy_exists))

    print(f"workflow init :: repo={repo}")
    print(f"legacy scaffold :: {'detected (.ai present)' if legacy_exists else 'not detected'}")
    actions, backups = apply_planned_writes(
        writes,
        dry_run=dry_run,
        force=force,
        adopt_manual=adopt_manual,
    )
    for action in actions:
        prefix = "would " if dry_run else ""
        print(f"- {prefix}{action}")
    for backup in backups:
        print(f"- backup created: {backup}")

    if skip_sync:
        if dry_run:
            print("- would run workflow sync")
        else:
            print("- skipped workflow sync (`--skip-sync`)")
        return 0

    if dry_run:
        print("- would run workflow sync")
        return 0

    sync_exit = sync(repo, dry_run=False, force=force)
    if sync_exit != 0:
        return sync_exit
    doctor_result = doctor(repo, write_report=False)
    if doctor_result.errors:
        raise WorkflowError(
            "init completed but validation failed:\n"
            + "\n".join(f"- {error}" for error in doctor_result.errors)
        )
    return 0


def sync(repo: Path, *, dry_run: bool, force: bool) -> int:
    agents_path = repo / "AGENTS.md"
    if not agents_path.exists():
        raise WorkflowError("Missing `AGENTS.md`. Run `workflow init` or create it first.")

    manifest = load_manifest(repo)
    agents_text = read_text(agents_path)
    project_name = repo_name_from_agents(repo, agents_text)
    lock = load_lock(repo)
    source_checksum = sha256_text(agents_text)
    shims_payload: dict[str, dict[str, str]] = {}
    role_shims_payload: dict[str, dict[str, str]] = {}
    claude_adapters_payload: dict[str, dict[str, str]] = {}
    opencode_adapters_payload: dict[str, dict[str, object]] = {}
    droid_adapters_payload: dict[str, dict[str, str]] = {}
    gemini_adapters_payload: dict[str, dict[str, str]] = {}
    changed_files: list[str] = []
    backups: list[str] = []

    for filename in manifest.get("generated_shims", list(SHIMS.keys())):
        if filename not in SHIMS:
            continue
        path = repo / filename
        unmanaged = ""
        if path.exists():
            current = read_text(path)
            parsed = parse_generated_shim(current)
            if parsed:
                if lock:
                    locked = lock.get("shims", {}).get(filename)
                    if locked and sha256_text(parsed["managed"]) != locked.get("managed_checksum") and not force:
                        raise WorkflowError(
                            f"Refusing to overwrite managed drift in `{filename}`. "
                            "Back up or inspect the file, then rerun with `--force` if regeneration is intended."
                        )
                unmanaged = parsed["unmanaged"]
            elif lock and not force:
                raise WorkflowError(
                    f"`{filename}` no longer matches the generated shim format tracked in `.workflow/mirror-lock.json`."
                )
            elif is_legacy_generated_shim(current, filename, project_name):
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))
                print(f"- migrating legacy generated shim: {filename}")
            elif not force:
                raise WorkflowError(
                    f"Refusing to overwrite `{filename}` because it is not a recognized generated shim. "
                    "Rerun with `--force` to back it up and replace it."
                )
            else:
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))

        rendered = render_shim(filename, project_name, agents_text, unmanaged)
        if not path.exists() or read_text(path) != rendered:
            changed_files.append(filename)
            if not dry_run:
                write_text_atomic(path, rendered)

        parsed_rendered = parse_generated_shim(rendered)
        assert parsed_rendered is not None
        shims_payload[filename] = {
            "tool": filename,
            "format": GENERATED_FORMAT_VERSION,
            "managed_checksum": sha256_text(parsed_rendered["managed"]),
            "unmanaged_checksum": sha256_text(parsed_rendered["unmanaged"]),
            "full_checksum": sha256_text(rendered),
        }

    for relative_path in manifest.get("generated_role_shims", []):
        if relative_path not in GENERATED_ROLE_SHIMS:
            continue
        path = repo / relative_path
        if path.exists():
            current = read_text(path)
            parsed_role = parse_generated_role_shim(current)
            if parsed_role:
                if lock:
                    locked = lock.get("role_shims", {}).get(relative_path)
                    if locked and sha256_text(current) != locked.get("full_checksum") and not force:
                        raise WorkflowError(
                            f"Refusing to overwrite managed drift in `{relative_path}`. "
                            "Back up or inspect the file, then rerun with `--force` if regeneration is intended."
                        )
            elif lock and not force:
                raise WorkflowError(
                    f"`{relative_path}` no longer matches the generated role-pointer format tracked in `.workflow/mirror-lock.json`."
                )
            elif not force:
                raise WorkflowError(
                    f"Refusing to overwrite `{relative_path}` because it is not a recognized generated role pointer. "
                    "Rerun with `--force` to back it up and replace it."
                )
            else:
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))

        rendered_role = render_role_shim()
        if not path.exists() or read_text(path) != rendered_role:
            changed_files.append(relative_path)
            if not dry_run:
                write_text_atomic(path, rendered_role)

        role_shims_payload[relative_path] = {
            "format": GENERATED_FORMAT_VERSION,
            "source": "~/ROLES.md",
            "full_checksum": sha256_text(rendered_role),
        }

    for relative_path in manifest_managed_adapter_paths(
        manifest,
        "generated_claude_adapters",
        MANAGED_CLAUDE_ADAPTERS,
    ):
        if relative_path not in MANAGED_CLAUDE_ADAPTERS:
            continue
        path = repo / relative_path
        if path.exists():
            current = read_text(path)
            parsed_adapter = parse_generated_claude_adapter(current)
            if parsed_adapter:
                if lock:
                    locked = lock.get("claude_adapters", {}).get(relative_path)
                    if locked and sha256_text(current) != locked.get("full_checksum") and not force:
                        raise WorkflowError(
                            f"Refusing to overwrite managed drift in `{relative_path}`. "
                            "Back up or inspect the file, then rerun with `--force` if regeneration is intended."
                        )
            elif lock and not force:
                raise WorkflowError(
                    f"`{relative_path}` no longer matches the generated Claude adapter format tracked in `.workflow/mirror-lock.json`."
                )
            elif not force:
                raise WorkflowError(
                    f"Refusing to overwrite `{relative_path}` because it is not a recognized generated Claude adapter. "
                    "Rerun with `--force` to back it up and replace it."
                )
            else:
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))

        rendered_adapter = render_claude_adapter(relative_path)
        if not path.exists() or read_text(path) != rendered_adapter:
            changed_files.append(relative_path)
            if not dry_run:
                write_text_atomic(path, rendered_adapter)

        adapter = MANAGED_CLAUDE_ADAPTERS[relative_path]
        claude_adapters_payload[relative_path] = {
            "name": adapter["name"],
            "format": GENERATED_FORMAT_VERSION,
            "role": adapter["role"],
            "tools": adapter["tools"],
            "full_checksum": sha256_text(rendered_adapter),
        }

    for relative_path in manifest_managed_adapter_paths(
        manifest,
        "generated_opencode_adapters",
        MANAGED_OPENCODE_ADAPTERS,
    ):
        if relative_path not in MANAGED_OPENCODE_ADAPTERS:
            continue
        path = repo / relative_path
        if path.exists():
            current = read_text(path)
            parsed_adapter = parse_generated_opencode_adapter(current)
            if parsed_adapter:
                if lock:
                    locked = lock.get("opencode_adapters", {}).get(relative_path)
                    if locked and sha256_text(current) != locked.get("full_checksum") and not force:
                        raise WorkflowError(
                            f"Refusing to overwrite managed drift in `{relative_path}`. "
                            "Back up or inspect the file, then rerun with `--force` if regeneration is intended."
                        )
            elif lock and not force:
                raise WorkflowError(
                    f"`{relative_path}` no longer matches the generated OpenCode adapter format tracked in `.workflow/mirror-lock.json`."
                )
            elif not force:
                raise WorkflowError(
                    f"Refusing to overwrite `{relative_path}` because it is not a recognized generated OpenCode adapter. "
                    "Rerun with `--force` to back it up and replace it."
                )
            else:
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))

        rendered_adapter = render_opencode_adapter(relative_path)
        if not path.exists() or read_text(path) != rendered_adapter:
            changed_files.append(relative_path)
            if not dry_run:
                write_text_atomic(path, rendered_adapter)

        adapter = MANAGED_OPENCODE_ADAPTERS[relative_path]
        opencode_adapters_payload[relative_path] = {
            "format": GENERATED_FORMAT_VERSION,
            "role": adapter["role"],
            "mode": adapter["mode"],
            "permission": adapter["permission"],
            "full_checksum": sha256_text(rendered_adapter),
        }

    for relative_path in manifest_managed_adapter_paths(
        manifest,
        "generated_droid_adapters",
        MANAGED_DROID_ADAPTERS,
    ):
        if relative_path not in MANAGED_DROID_ADAPTERS:
            continue
        path = repo / relative_path
        if path.exists():
            current = read_text(path)
            parsed_adapter = parse_generated_droid_adapter(current)
            if parsed_adapter:
                if lock:
                    locked = lock.get("droid_adapters", {}).get(relative_path)
                    if locked and sha256_text(current) != locked.get("full_checksum") and not force:
                        raise WorkflowError(
                            f"Refusing to overwrite managed drift in `{relative_path}`. "
                            "Back up or inspect the file, then rerun with `--force` if regeneration is intended."
                        )
            elif lock and not force:
                raise WorkflowError(
                    f"`{relative_path}` no longer matches the generated Factory Droid adapter format tracked in `.workflow/mirror-lock.json`."
                )
            elif not force:
                raise WorkflowError(
                    f"Refusing to overwrite `{relative_path}` because it is not a recognized generated Factory Droid adapter. "
                    "Rerun with `--force` to back it up and replace it."
                )
            else:
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))

        rendered_adapter = render_droid_adapter(relative_path)
        if not path.exists() or read_text(path) != rendered_adapter:
            changed_files.append(relative_path)
            if not dry_run:
                write_text_atomic(path, rendered_adapter)

        adapter = MANAGED_DROID_ADAPTERS[relative_path]
        droid_adapters_payload[relative_path] = {
            "name": adapter["name"],
            "format": GENERATED_FORMAT_VERSION,
            "role": adapter["role"],
            "droid_type": adapter["droid_type"],
            "model": adapter["model"],
            "tools": adapter["tools"],
            "full_checksum": sha256_text(rendered_adapter),
        }

    for relative_path in manifest_managed_adapter_paths(
        manifest,
        "generated_gemini_adapters",
        MANAGED_GEMINI_ADAPTERS,
    ):
        if relative_path not in MANAGED_GEMINI_ADAPTERS:
            continue
        path = repo / relative_path
        if path.exists():
            current = read_text(path)
            parsed_adapter = parse_generated_gemini_adapter(current)
            if parsed_adapter:
                if lock:
                    locked = lock.get("gemini_adapters", {}).get(relative_path)
                    if locked and sha256_text(current) != locked.get("full_checksum") and not force:
                        raise WorkflowError(
                            f"Refusing to overwrite managed drift in `{relative_path}`. "
                            "Back up or inspect the file, then rerun with `--force` if regeneration is intended."
                        )
            elif lock and not force:
                raise WorkflowError(
                    f"`{relative_path}` no longer matches the generated Gemini adapter format tracked in `.workflow/mirror-lock.json`."
                )
            elif not force:
                raise WorkflowError(
                    f"Refusing to overwrite `{relative_path}` because it is not a recognized generated Gemini adapter. "
                    "Rerun with `--force` to back it up and replace it."
                )
            else:
                if not dry_run:
                    backup = backup_file(path)
                    backups.append(str(backup))

        rendered_adapter = render_gemini_adapter(relative_path)
        if not path.exists() or read_text(path) != rendered_adapter:
            changed_files.append(relative_path)
            if not dry_run:
                write_text_atomic(path, rendered_adapter)

        adapter = MANAGED_GEMINI_ADAPTERS[relative_path]
        gemini_adapters_payload[relative_path] = {
            "name": adapter["name"],
            "format": GENERATED_FORMAT_VERSION,
            "canonical_capability": adapter["canonical_capability"],
            "full_checksum": sha256_text(rendered_adapter),
        }

    lock_payload = {
        "schema_version": MIRROR_LOCK_SCHEMA_VERSION,
        "canonical_contract": "AGENTS.md",
        "source_checksum": source_checksum,
        "generated_at": timestamp(),
        "claude_adapters": claude_adapters_payload,
        "droid_adapters": droid_adapters_payload,
        "generated_role_shims": list(role_shims_payload.keys()),
        "gemini_adapters": gemini_adapters_payload,
        "opencode_adapters": opencode_adapters_payload,
        "role_shims": role_shims_payload,
        "shims": shims_payload,
    }
    if lock:
        existing_without_timestamp = {
            key: value for key, value in lock.items() if key != "generated_at"
        }
        new_without_timestamp = {
            key: value for key, value in lock_payload.items() if key != "generated_at"
        }
        if existing_without_timestamp == new_without_timestamp:
            lock_payload["generated_at"] = lock.get("generated_at")
    lock_path = repo / ".workflow/mirror-lock.json"
    lock_content = json.dumps(lock_payload, indent=2, sort_keys=True) + "\n"
    if not lock_path.exists() or read_text(lock_path) != lock_content:
        changed_files.append(".workflow/mirror-lock.json")
        if not dry_run:
            write_text_atomic(lock_path, lock_content)

    print(f"workflow sync :: repo={repo}")
    if changed_files:
        for changed in changed_files:
            prefix = "would update" if dry_run else "updated"
            print(f"- {prefix} {changed}")
    else:
        print("- no changes")
    for backup in backups:
        print(f"- backup created: {backup}")
    return 0


def git_summary(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        return "not a git repository"
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in status.stdout.splitlines() if line.strip()]
    return "clean" if not lines else f"dirty ({len(lines)} paths changed)"


def git_preflight_facts(repo: Path) -> GitPreflightFacts:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "true":
        return GitPreflightFacts(
            is_git_repo=False,
            is_dirty=False,
            status="not-git",
            dirty_path_count=0,
            blocks_future_apply=True,
        )
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in status.stdout.splitlines() if line.strip()]
    if lines:
        return GitPreflightFacts(
            is_git_repo=True,
            is_dirty=True,
            status="dirty",
            dirty_path_count=len(lines),
            blocks_future_apply=True,
        )
    return GitPreflightFacts(
        is_git_repo=True,
        is_dirty=False,
        status="clean",
        dirty_path_count=0,
        blocks_future_apply=False,
    )


def detect_nested_workspaces(repo: Path) -> list[Path]:
    nested = []
    for child in repo.iterdir():
        if child.name.startswith(".") or not child.is_dir():
            continue
        if (child / ".workflow/workflow.json").exists():
            nested.append(child)
    return nested


def classify_repo(repo: Path) -> RepoInfo:
    repo = repo.resolve()
    if not repo.exists():
        return RepoInfo(path=repo, name=repo.name, classification="error", notes=["Repository path does not exist."])
    if not repo.is_dir():
        return RepoInfo(path=repo, name=repo.name, classification="error", notes=["Repository path is not a directory."])

    manifest_path = repo / ".workflow/workflow.json"
    info = RepoInfo(
        path=repo,
        name=repo.name,
        classification="unmanaged",
        has_workflow_manifest=manifest_path.exists(),
        has_specify=(repo / ".specify").exists(),
        has_ai=(repo / ".ai").exists(),
        has_agents=(repo / "AGENTS.md").exists(),
        has_claude=(repo / "CLAUDE.md").exists(),
        has_gemini=(repo / "GEMINI.md").exists(),
        handoff_path=(repo / ".specify/state/handoff.md") if (repo / ".specify/state/handoff.md").exists() else None,
        active_path=(repo / ".specify/state/active.md") if (repo / ".specify/state/active.md").exists() else None,
        progress_path=(repo / ".specify/state/progress.md") if (repo / ".specify/state/progress.md").exists() else None,
        session_log_path=(repo / ".specify/state/session.log.md") if (repo / ".specify/state/session.log.md").exists() else None,
        legacy_handoff_path=(repo / ".ai/handoffs/NEXT_STEP.md") if (repo / ".ai/handoffs/NEXT_STEP.md").exists() else None,
        legacy_state_path=(repo / ".ai/context/PROJECT_STATE.md") if (repo / ".ai/context/PROJECT_STATE.md").exists() else None,
        legacy_task_path=(repo / ".ai/prompts/CURRENT_TASK.md") if (repo / ".ai/prompts/CURRENT_TASK.md").exists() else None,
        legacy_session_log_path=(repo / ".ai/logs/session.log") if (repo / ".ai/logs/session.log").exists() else None,
    )

    if manifest_path.exists():
        try:
            info.manifest = json.loads(read_text(manifest_path))
        except json.JSONDecodeError as exc:
            info.classification = "error"
            info.notes.append(f"Invalid `.workflow/workflow.json`: {exc}")
            return info

    if info.has_workflow_manifest and info.has_specify:
        if not info.has_agents:
            info.classification = "error"
            info.notes.append("v2 scaffold detected, but `AGENTS.md` is missing.")
            return info
        if info.has_ai and info.manifest:
            migration_status = info.manifest.get("migration", {}).get("status")
            if migration_status not in {"coexist", "legacy", "v2"}:
                info.classification = "error"
                info.notes.append(
                    "Legacy `.ai/` exists, but the manifest migration status does not allow coexistence."
                )
                return info
        info.classification = "v2"
        return info

    if info.has_workflow_manifest or info.has_specify:
        info.classification = "mixed"
        info.notes.append("Partial v2 signals detected without a complete manifest + continuity scaffold.")
        return info

    if info.has_ai:
        info.classification = "legacy"
        return info

    if info.has_agents or info.has_claude or info.has_gemini:
        info.classification = "unmanaged"
        info.notes.append("Instruction files exist, but no recognized legacy or v2 scaffold was detected.")
        return info

    info.classification = "unmanaged"
    info.notes.append("No workflow scaffold detected.")
    return info


def continuity_sources(info: RepoInfo) -> list[str]:
    lines: list[str] = []
    if info.classification == "v2":
        lines.append(f"- Handoff: `{relative_display(info.handoff_path, info.path)}`")
        lines.append(f"- Active state: `{relative_display(info.active_path, info.path)}`")
        lines.append(f"- Progress: `{relative_display(info.progress_path, info.path)}`")
        lines.append(f"- Session log: `{relative_display(info.session_log_path, info.path)}`")
        if info.has_ai:
            lines.append("- Legacy continuity preserved: `.ai/*`")
        return lines
    if info.classification == "legacy":
        if info.legacy_handoff_path:
            lines.append(f"- Handoff: `{relative_display(info.legacy_handoff_path, info.path)}`")
        if info.legacy_state_path:
            lines.append(f"- Project state: `{relative_display(info.legacy_state_path, info.path)}`")
        if info.legacy_session_log_path:
            lines.append(f"- Session log: `{relative_display(info.legacy_session_log_path, info.path)}`")
        return lines or ["- No legacy continuity files were found."]
    if info.classification == "mixed":
        if info.handoff_path:
            lines.append(f"- V2 handoff candidate: `{relative_display(info.handoff_path, info.path)}`")
        if info.legacy_handoff_path:
            lines.append(f"- Legacy handoff candidate: `{relative_display(info.legacy_handoff_path, info.path)}`")
        if info.session_log_path:
            lines.append(f"- V2 session log: `{relative_display(info.session_log_path, info.path)}`")
        if info.legacy_session_log_path:
            lines.append(f"- Legacy session log: `{relative_display(info.legacy_session_log_path, info.path)}`")
        return lines or ["- No reliable continuity files were found."]
    if info.classification == "unmanaged":
        return ["- No managed continuity files detected."]
    return ["- Continuity source is unavailable until the error is resolved."]


def build_status_context(info: RepoInfo) -> dict[str, str]:
    agents_text = read_optional(info.path / "AGENTS.md")

    if info.classification == "v2" and info.manifest is not None:
        project_text = read_optional(info.path / ".specify/memory/project.md")
        active_text = read_optional(info.path / ".specify/state/active.md")
        handoff_text = read_optional(info.path / ".specify/state/handoff.md")
        migration_text = read_optional(info.path / ".specify/state/migration.md")
        drift_text = read_optional(info.path / ".specify/state/drift.md")
        return {
            "what_project": first_nonempty_paragraph(
                extract_section(project_text, ["What this project is"]),
                first_nonempty_paragraph(
                    extract_section(agents_text, ["What this project is"]),
                    "Unavailable.",
                ),
            ),
            "current_task": first_nonempty_paragraph(
                extract_section(active_text, ["Current task"]),
                first_nonempty_paragraph(
                    extract_section(agents_text, ["Active task"]),
                    "Unavailable.",
                ),
            ),
            "next_step": first_nonempty_paragraph(
                extract_section(handoff_text, ["What to do next"]),
                "Unavailable.",
            ),
            "migration_state": clean_block(
                extract_section(migration_text, ["Current state"]),
                "Unavailable.",
            ),
            "doctor_summary": summarize_doctor_section_for_status(drift_text),
            "manifest_scaffold": info.manifest.get("scaffold", "unknown"),
        }

    if info.classification == "legacy":
        project_state = read_optional(info.path / ".ai/context/PROJECT_STATE.md")
        handoff_text = read_optional(info.path / ".ai/handoffs/NEXT_STEP.md")
        task_text = read_optional(info.path / ".ai/prompts/CURRENT_TASK.md")
        return {
            "what_project": first_nonempty_paragraph(
                extract_section(agents_text, ["What this project is"]),
                first_nonempty_paragraph(
                    extract_section(project_state, ["Known Truths"]),
                    "Legacy repo with workflow-manager v1 continuity files.",
                ),
            ),
            "current_task": first_nonempty_paragraph(
                extract_section(agents_text, ["Active task"]),
                first_nonempty_paragraph(
                    task_text,
                    "No current task was found in legacy continuity files.",
                ),
            ),
            "next_step": first_nonempty_paragraph(
                extract_section(handoff_text, ["What to do next"]),
                first_nonempty_paragraph(
                    extract_section(project_state, ["Next Validation Step"]),
                    "No next step was found in legacy continuity files.",
                ),
            ),
            "migration_state": "Legacy `.ai/*` continuity detected. `.specify/*` has not been initialized yet.",
            "doctor_summary": "Doctor is only available after the v2 scaffold is initialized.",
            "manifest_scaffold": "legacy-only",
        }

    if info.classification == "mixed":
        active_text = read_optional(info.path / ".specify/state/active.md")
        handoff_text = read_optional(info.path / ".specify/state/handoff.md")
        legacy_handoff = read_optional(info.path / ".ai/handoffs/NEXT_STEP.md")
        project_state = read_optional(info.path / ".ai/context/PROJECT_STATE.md")
        next_step_parts: list[str] = []
        if handoff_text:
            next_step_parts.append(
                f"V2 candidate: {first_nonempty_paragraph(extract_section(handoff_text, ['What to do next']), 'present')}"
            )
        if legacy_handoff:
            next_step_parts.append(
                f"Legacy candidate: {first_nonempty_paragraph(extract_section(legacy_handoff, ['What to do next']), 'present')}"
            )
        if not next_step_parts:
            next_step_parts.append("No handoff file was found in either `.specify/` or `.ai/`.")
        return {
            "what_project": first_nonempty_paragraph(
                extract_section(agents_text, ["What this project is"]),
                "Repo has mixed workflow signals and needs manual review.",
            ),
            "current_task": first_nonempty_paragraph(
                extract_section(active_text, ["Current task"]),
                first_nonempty_paragraph(
                    extract_section(agents_text, ["Active task"]),
                    "Current task is unclear because the workflow scaffold is mixed.",
                ),
            ),
            "next_step": " ".join(next_step_parts),
            "migration_state": "Mixed or half-migrated state detected. Do not assume either `.specify/*` or `.ai/*` is authoritative until the repo is reconciled.",
            "doctor_summary": "Run `workflow init` carefully or inspect the conflicting files before trusting automation.",
            "manifest_scaffold": "mixed",
        }

    if info.classification == "unmanaged":
        return {
            "what_project": first_nonempty_paragraph(
                extract_section(agents_text, ["What this project is"]),
                f"Unmanaged directory `{info.name}`.",
            ),
            "current_task": first_nonempty_paragraph(
                extract_section(agents_text, ["Active task"]),
                "No managed workflow metadata was detected.",
            ),
            "next_step": "Initialize the repo with `workflow init` if it should participate in workflow-manager v2.",
            "migration_state": "Unmanaged: neither a recognized v2 scaffold nor a legacy `.ai/` scaffold was detected.",
            "doctor_summary": "Doctor becomes meaningful after the repo is initialized as v2.",
            "manifest_scaffold": "unmanaged",
        }

    return {
        "what_project": first_nonempty_paragraph(
            extract_section(agents_text, ["What this project is"]),
            "Unavailable.",
        ),
        "current_task": "Unavailable.",
        "next_step": "Resolve the repository error before trusting workflow automation.",
        "migration_state": clean_block("\n".join(info.notes), "Unavailable."),
        "doctor_summary": "Error state detected. Fix the reported issue first.",
        "manifest_scaffold": "error",
    }


def roots_health_status_lines(roots_health: RootsHealth) -> list[str]:
    config_path = str(roots_health.config_path) if roots_health.config_path is not None else "Unavailable."
    return [
        "- Status: " + roots_health.status,
        f"- Config path: `{config_path}`",
        f"- Summary: {roots_health.summary}",
    ]


def manifest_health_status_lines(manifest_health: ManifestHealth) -> list[str]:
    return [
        "- Status: " + manifest_health.status,
        f"- Path: `{manifest_health.manifest_path}`",
        f"- Summary: {manifest_health.summary}",
    ]


def mirror_health_status_lines(mirror_health: MirrorHealth) -> list[str]:
    return [
        "- Status: " + mirror_health.status,
        f"- Path: `{mirror_health.lock_path}`",
        f"- Summary: {mirror_health.summary}",
        f"- Sync needed: {'yes' if mirror_health.sync_needed else 'no'}",
    ]


def continuity_state_health_status_lines(continuity_health: ContinuityStateHealth) -> list[str]:
    lines = [
        "- Status: " + continuity_health.status,
        f"- Path: `{continuity_health.state_root}`",
        f"- Summary: {continuity_health.summary}",
    ]
    if continuity_health.status != "pass":
        for entry in continuity_health.entries:
            if entry.status == "pass":
                continue
            lines.append(f"- {Path(entry.relative_path).name}: {entry.summary}")
    return lines


def memory_health_status_lines(memory_health: MemoryHealth) -> list[str]:
    lines = [
        "- Status: " + memory_health.status,
        f"- Path: `{memory_health.memory_root}`",
        f"- Summary: {memory_health.summary}",
    ]
    if memory_health.status != "pass":
        for entry in memory_health.entries:
            if entry.status == "pass":
                continue
            lines.append(f"- {Path(entry.relative_path).name}: {entry.summary}")
    return lines


def command_docs_health_status_lines(command_docs_health: CommandDocsHealth) -> list[str]:
    lines = [
        "- Status: " + command_docs_health.status,
        f"- Path: `{command_docs_health.manager_home}`",
        f"- Summary: {command_docs_health.summary}",
    ]
    if command_docs_health.status != "pass":
        for entry in command_docs_health.entries:
            if entry.status == "pass":
                continue
            lines.append(f"- {entry.surface}: {entry.summary}")
    return lines


def role_contract_health_status_lines(role_contract_health: RoleContractHealth) -> list[str]:
    lines = [
        "- Status: " + role_contract_health.status,
        f"- Path: `{role_contract_health.contract_path}`",
        f"- Summary: {role_contract_health.summary}",
        "- Canonical roles: " + ", ".join(role_contract_health.canonical_roles),
        "- Reserved roles: " + ", ".join(role_contract_health.reserved_roles),
    ]
    if role_contract_health.status != "pass":
        for issue in role_contract_health.issues:
            lines.append(f"- {issue.level.title()}: {issue.message}")
    return lines


def docs_health_status_lines(docs_health: DocsHealth) -> list[str]:
    lines = [
        "- Status: " + docs_health.status,
        f"- Path: `{docs_health.repo}`",
        f"- Summary: {docs_health.summary}",
    ]
    if docs_health.status != "pass":
        for issue in docs_health.issues:
            lines.append(f"- {issue.level.title()}: {issue.message}")
    return lines


def health_overview_status_lines(overview: HealthOverview) -> list[str]:
    return [
        "- Overall health: " + overview.overall_status,
        f"- Summary: {overview.summary}",
        (
            "- Subsystems: "
            f"command/help/docs={overview.command_docs_status}, "
            f"manifest={overview.manifest_status}, "
            f"mirror-lock/shim={overview.mirror_status}, "
            f"memory={overview.memory_status}, "
            f"continuity-state={overview.continuity_status}, "
            f"roots={overview.roots_status}, "
            f"role-contract={overview.role_contract_status}, "
            f"docs-health={overview.docs_status}"
        ),
        f"- Sync needed: {'yes' if overview.sync_needed else 'no'}",
        f"- Default-root operations safe: {'yes' if overview.default_root_operations_safe else 'no'}",
        f"- Pre-Hermes readiness: {overview.pre_hermes_readiness}",
    ]


def summarize_doctor_section_for_status(drift_text: str) -> str:
    latest_summary = clean_block(
        extract_section(drift_text, ["Latest summary"]),
        "No drift summary recorded.",
    )
    filtered_lines = [
        line
        for line in latest_summary.splitlines()
        if not line.startswith("- health overview")
        and not line.startswith("- health summary")
        and not line.startswith("- health subsystems")
        and not line.startswith("- overall health")
        and not line.startswith("- command/help/docs consistency")
        and not line.startswith("- command/help/docs root")
        and not line.startswith("- command/help/docs summary")
        and not line.startswith("- roots ")
        and not line.startswith("- default root operations")
        and not line.startswith("- default-root operations safe")
        and not line.startswith("- sync needed")
        and not line.startswith("- pre-hermes readiness")
        and not line.startswith("- manifest health")
        and not line.startswith("- manifest path")
        and not line.startswith("- manifest summary")
        and not line.startswith("- mirror-lock/shim health")
        and not line.startswith("- mirror-lock/shim path")
        and not line.startswith("- mirror-lock/shim summary")
        and not line.startswith("- workflow sync needed")
        and not line.startswith("- continuity-state health")
        and not line.startswith("- continuity-state root")
        and not line.startswith("- continuity-state summary")
        and not line.startswith("- command/help/docs ")
        and not line.startswith("- memory health")
        and not line.startswith("- memory root")
        and not line.startswith("- memory summary")
        and not line.startswith("- role-contract health")
        and not line.startswith("- role-contract path")
        and not line.startswith("- role-contract summary")
        and not line.startswith("- docs-health")
        and not line.startswith("- docs-health root")
        and not line.startswith("- docs-health summary")
    ]
    filtered = "\n".join(filtered_lines).strip()
    return filtered or latest_summary


def build_status_snapshot(repo: Path) -> StatusSnapshot:
    info = classify_repo(repo)
    context = build_status_context(info)
    command_docs_health = evaluate_command_docs_health()
    manifest_health = evaluate_manifest_health(info.path)
    mirror_health = evaluate_mirror_health(info.path)
    memory_health = evaluate_memory_health(info.path, manifest_health)
    roots_health = evaluate_configured_roots()
    continuity_health = evaluate_continuity_state_health(info.path, manifest_health)
    role_contract_health = evaluate_role_contract_health(info.path)
    docs_health = evaluate_docs_health(info.path)
    overview = evaluate_health_overview(
        command_docs_health,
        manifest_health,
        mirror_health,
        memory_health,
        continuity_health,
        roots_health,
        role_contract_health,
        docs_health,
    )
    return StatusSnapshot(
        repo=repo,
        info=info,
        context=context,
        command_docs_health=command_docs_health,
        manifest_health=manifest_health,
        mirror_health=mirror_health,
        memory_health=memory_health,
        continuity_health=continuity_health,
        roots_health=roots_health,
        role_contract_health=role_contract_health,
        docs_health=docs_health,
        overview=overview,
    )


def status_snapshot_payload(snapshot: StatusSnapshot) -> dict:
    return {
        "schema_version": MACHINE_OUTPUT_SCHEMA_VERSION,
        "command": "status",
        "repo_path": str(snapshot.repo),
        "classification": snapshot.info.classification,
        "project": {
            "name": snapshot.info.name,
            "what_this_project_is": snapshot.context["what_project"],
            "current_task": snapshot.context["current_task"],
            "next_step": snapshot.context["next_step"],
            "manifest_scaffold": snapshot.context["manifest_scaffold"],
        },
        "continuity": {
            "sources": status_continuity_payload(snapshot.info),
        },
        "migration": status_migration_payload(snapshot.info, snapshot.context["migration_state"]),
        "doctor_summary": {
            "summary": snapshot.context["doctor_summary"],
        },
        "health_overview": serialize_health_overview(snapshot.overview),
        "health": serialize_health_bundle(
            snapshot.command_docs_health,
            snapshot.manifest_health,
            snapshot.mirror_health,
            snapshot.memory_health,
            snapshot.continuity_health,
            snapshot.roots_health,
            snapshot.role_contract_health,
            snapshot.docs_health,
        ),
        "git": git_summary(snapshot.info.path),
        "notes": list(snapshot.info.notes),
    }


def render_status_text(repo: Path) -> str:
    snapshot = build_status_snapshot(repo)
    info = snapshot.info
    context = snapshot.context
    lines = [
        f"workflow status :: repo={info.path}",
        "",
        "Classification",
        info.classification,
        "",
        "What this project is",
        context["what_project"],
        "",
        "Current task",
        context["current_task"],
        "",
        "Next step",
        context["next_step"],
        "",
        "Continuity sources",
        *continuity_sources(info),
        "",
        "Migration state",
        context["migration_state"],
        "",
        "Doctor summary",
        context["doctor_summary"],
        "",
        "Health overview",
        *health_overview_status_lines(snapshot.overview),
        "",
        "Manifest health",
        *manifest_health_status_lines(snapshot.manifest_health),
        "",
        "Mirror-lock/shim health",
        *mirror_health_status_lines(snapshot.mirror_health),
        "",
        "Command/help/docs consistency",
        *command_docs_health_status_lines(snapshot.command_docs_health),
        "",
        "Role-contract health",
        *role_contract_health_status_lines(snapshot.role_contract_health),
        "",
        "Docs health",
        *docs_health_status_lines(snapshot.docs_health),
        "",
        "Memory health",
        *memory_health_status_lines(snapshot.memory_health),
        "",
        "Continuity-state health",
        *continuity_state_health_status_lines(snapshot.continuity_health),
        "",
        "Roots health",
        *roots_health_status_lines(snapshot.roots_health),
    ]
    if info.notes:
        lines.extend(["", "Notes"])
        lines.extend(f"- {note}" for note in info.notes)
    lines.extend(
        [
            "",
            f"Git: {git_summary(info.path)}",
            f"Manifest scaffold: {context['manifest_scaffold']}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_status_json(repo: Path) -> str:
    return render_json_output(status_snapshot_payload(build_status_snapshot(repo)))


def print_status(repo: Path, *, as_json: bool = False) -> int:
    if as_json:
        print(render_status_json(repo), end="")
        return 0
    print(render_status_text(repo), end="")
    return 0


def find_project_matches(name: str, roots: list[Path]) -> list[Path]:
    matches = []
    for root in roots:
        candidate = root / name
        if candidate.is_dir():
            matches.append(candidate.resolve())
    return matches


def roots_exit_code(roots_health: RootsHealth, *, validate: bool) -> int:
    if roots_health.status == "fail":
        return 1
    if validate and roots_health.status != "pass":
        return 1
    return 0


def roots_command(format_name: str, *, validate: bool) -> int:
    roots_health = evaluate_configured_roots()
    if format_name == "json":
        payload = {
            "schema_version": MACHINE_OUTPUT_SCHEMA_VERSION,
            "command": "roots",
            "validate_requested": validate,
            "passed_validation": roots_exit_code(roots_health, validate=validate) == 0,
            "health": serialize_roots_health(roots_health),
        }
        print(render_json_output(payload), end="")
        return roots_exit_code(roots_health, validate=validate)

    if format_name == "shell":
        if roots_health.status == "fail":
            raise WorkflowError("\n".join(roots_issue_lines(roots_health, level="error")))
        print(
            "\n".join(
                [
                    render_shell_assignments(
                        {
                            "WORKFLOW_ROOTS_CONFIG": str(roots_health.config_path) if roots_health.config_path else "",
                            "WORKFLOW_ROOTS_VALID": "1" if roots_health.status == "pass" else "",
                        }
                    ),
                    render_shell_array_assignment(
                        "WORKFLOW_CONFIGURED_ROOTS",
                        [str(root) for root in roots_health.roots],
                    ),
                    render_shell_array_assignment(
                        "WORKFLOW_EXISTING_ROOTS",
                        [str(root) for root in roots_health.usable_roots],
                    ),
                ]
            )
        )
        return roots_exit_code(roots_health, validate=validate)

    print(f"workflow roots :: source={roots_health.source_label}")
    if roots_health.config_path is not None:
        print(f"Config path: {roots_health.config_path}")
    print(f"Status: {roots_health.status}")
    print(f"Summary: {roots_health.summary}")
    for entry in roots_health.entries:
        print(f"{entry.status:<8} {entry.path}")
    for issue in roots_health.issues:
        print(f"- {issue.level.title()}: {issue.message}")
    if validate:
        print("PASS" if roots_health.status == "pass" else "FAIL")

    return roots_exit_code(roots_health, validate=validate)


def open_project(
    name: str,
    roots: list[Path],
    *,
    create: bool,
    create_root: Path | None,
    force: bool,
    skip_sync: bool,
    format_name: str,
) -> int:
    roots_health = require_usable_roots(roots)
    for warning in roots_issue_lines(roots_health, level="warning"):
        print(f"workflow open warning: {warning}", file=sys.stderr)

    matches = find_project_matches(name, roots_health.roots)
    created = False

    if len(matches) > 1:
        raise WorkflowError(
            "Project name is ambiguous across roots:\n" + "\n".join(f"- {match}" for match in matches)
        )

    if matches:
        target = matches[0]
    else:
        if not create:
            message_lines = [f"Project `{name}` was not found across {roots_health.source_label}."]
            if roots_health.warnings:
                message_lines.append("Missing roots:")
                for issue in roots_health.warnings:
                    message_lines.append(f"- {issue.message}")
            raise WorkflowError("\n".join(message_lines))
        if create_root is None:
            raise WorkflowError("`workflow open --create` requires `--root`.")
        root = create_root.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise WorkflowError(f"Creation root `{root}` does not exist or is not a directory.")
        target = root / name
        if target.exists():
            raise WorkflowError(f"Target path `{target}` already exists; refusing to overwrite it.")
        with contextlib.redirect_stdout(io.StringIO()):
            ensure_init(target, dry_run=False, force=force, skip_sync=skip_sync)
        created = True

    info = classify_repo(target)
    if format_name == "shell":
        print(
            render_shell_assignments(
                {
                    "WORKFLOW_OPEN_PATH": str(info.path),
                    "WORKFLOW_OPEN_CLASSIFICATION": info.classification,
                    "WORKFLOW_OPEN_CREATED": "1" if created else "",
                }
            )
        )
        return 0

    print(f"workflow open :: project={name}")
    print(f"Resolved path: {info.path}")
    print(f"Created: {'yes' if created else 'no'}")
    print("")
    print(render_status_text(info.path), end="")
    return 0


def list_projects(roots: list[Path]) -> int:
    roots_health = require_usable_roots(roots)
    for root in roots_health.roots:
        print(f"== {root}")
        if not root.exists() or not root.is_dir():
            print("missing-root")
            print("")
            continue
        children = sorted(
            child for child in root.iterdir()
            if child.is_dir() and not child.name.startswith(".")
        )
        if not children:
            print("(no projects)")
            print("")
            continue
        for child in children:
            info = classify_repo(child)
            print(f"{info.classification:<10} {child.name}")
        print("")
    return 0


def build_hermes_inventory_report() -> HermesInventoryReport:
    roots_health = evaluate_configured_roots()
    reports: list[HermesInventoryRoot] = []

    for entry in roots_health.entries:
        if entry.status == "missing":
            reports.append(
                HermesInventoryRoot(
                    path=entry.path,
                    classification="missing-root",
                    issues=[f"Configured root is missing on disk: `{entry.path}`."],
                )
            )
            continue
        if entry.status == "not-dir":
            reports.append(
                HermesInventoryRoot(
                    path=entry.path,
                    classification="invalid-root",
                    issues=[f"Configured root exists but is not a directory: `{entry.path}`."],
                )
            )
            continue

        children = sorted(
            child for child in entry.path.iterdir()
            if child.is_dir() and not child.name.startswith(".")
        )
        repos = [
            HermesInventoryRepo(
                path=info.path,
                name=info.name,
                classification=info.classification,
                notes=list(info.notes),
            )
            for info in (classify_repo(child) for child in children)
        ]
        reports.append(
            HermesInventoryRoot(
                path=entry.path,
                classification="configured-root",
                repos=repos,
            )
        )

    return HermesInventoryReport(
        roots_health=roots_health,
        roots=reports,
    )


def render_hermes_inventory_text(report: HermesInventoryReport) -> str:
    roots_source = report.roots_health.config_path or report.roots_health.source_label
    counts = report.classification_counts
    count_line = ", ".join(
        f"{name}={counts[name]}"
        for name in ("v2", "legacy", "mixed", "unmanaged", "error")
    )
    lines = [
        "workflow hermes inventory :: mode=dry-run",
        f"Roots source: {roots_source}",
        "Read-only: yes",
        "Depth: shallow direct-child classification only",
        f"Summary: {report.summary}",
        f"Repo classifications: {count_line}",
        "",
    ]

    for root in report.roots:
        lines.append(f"== {root.path}")
        if root.classification != "configured-root":
            lines.append(root.classification)
            for issue in root.issues:
                lines.append(f"- {issue}")
            lines.append("")
            continue

        if not root.repos:
            lines.append("(no project candidates)")
            lines.append("")
            continue

        for repo in root.repos:
            line = f"{repo.classification:<10} {repo.name}"
            if repo.classification == "error" and repo.notes:
                line += f" :: {repo.notes[0]}"
            lines.append(line)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _sorted_hermes_inventory_roots(report: HermesInventoryReport) -> list[HermesInventoryRoot]:
    return sorted(report.roots, key=lambda root: (str(root.path), root.classification))


def _sorted_hermes_inventory_projects(root: HermesInventoryRoot) -> list[HermesInventoryRepo]:
    return sorted(root.repos, key=lambda repo: (repo.name, str(repo.path)))


def hermes_inventory_payload(report: HermesInventoryReport) -> dict:
    roots: list[dict] = []
    for root in _sorted_hermes_inventory_roots(report):
        roots.append(
            {
                "path": str(root.path),
                "classification": root.classification,
                "exists": root.path.exists(),
                "is_directory": root.path.is_dir(),
                "project_count": len(root.repos),
                "issues": sorted(root.issues),
                "projects": [
                    {
                        "name": repo.name,
                        "path": str(repo.path),
                        "root": str(root.path),
                        "classification": repo.classification,
                        "notes": list(repo.notes),
                    }
                    for repo in _sorted_hermes_inventory_projects(root)
                ],
            }
        )

    counts = report.classification_counts
    return {
        "schema_version": HERMES_INVENTORY_SCHEMA_VERSION,
        "command": "hermes_inventory",
        "mode": "inventory",
        "dry_run": True,
        "roots_config_path": path_or_none(report.roots_health.config_path),
        "summary": report.summary,
        "classification_counts": {
            "v2": counts["v2"],
            "legacy": counts["legacy"],
            "mixed": counts["mixed"],
            "unmanaged": counts["unmanaged"],
            "error": counts["error"],
        },
        "roots": roots,
        "warnings": sorted(issue.message for issue in report.roots_health.warnings),
        "errors": sorted(issue.message for issue in report.roots_health.failures),
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
    }


def render_hermes_inventory_json(report: HermesInventoryReport) -> str:
    return render_json_output(hermes_inventory_payload(report))


def hermes_inventory_command(*, dry_run: bool, as_json: bool = False) -> int:
    if not dry_run:
        raise WorkflowError(
            "`workflow hermes inventory` is intentionally dry-run only in this first Hermes slice; pass `--dry-run`."
        )

    report = build_hermes_inventory_report()
    if as_json:
        print(render_hermes_inventory_json(report), end="")
        return 1 if report.roots_health.status == "fail" else 0
    print(render_hermes_inventory_text(report), end="")
    return 1 if report.roots_health.status == "fail" else 0


def _preflight_detected_flags(info: RepoInfo, nested: list[Path]) -> list[str]:
    flags: list[str] = [f"scaffold:{info.classification}"]
    if info.has_workflow_manifest:
        flags.append("workflow-manifest")
    if info.has_specify:
        flags.append("specify-continuity")
    if info.has_ai:
        flags.append("legacy-ai")
    if info.has_agents:
        flags.append("agents-md")
    if info.has_claude:
        flags.append("claude-md")
    if info.has_gemini:
        flags.append("gemini-md")
    if nested:
        flags.append("nested-workflows")
    return sorted(flags)


def _preflight_migration_track(classification: str) -> str:
    return {
        "v2": "maintain-v2",
        "legacy": "legacy-adoption-review",
        "mixed": "mixed-scaffold-repair",
        "unmanaged": "manual-scaffold-review",
        "error": "classification-repair",
    }.get(classification, "classification-review")


def _preflight_next_safe_action(
    *,
    readiness: str,
    classification: str,
    git: GitPreflightFacts,
    blocking_reasons: list[str],
) -> str:
    if readiness == "blocked":
        if git.blocks_future_apply:
            return "Resolve git state before any future apply or migration step."
        if classification == "error":
            return "Repair scaffold classification errors before any future Hermes apply step."
        return "Resolve blocking reasons before any future Hermes apply step."
    if readiness == "ready":
        return "Keep using read-only preflight until a separately approved apply design exists."
    if blocking_reasons:
        return "Review warnings and blocking reasons before selecting any future migration action."
    return "Review shallow facts manually before any future Hermes design or apply slice."


def _build_preflight_repo(info: RepoInfo, root: Path) -> HermesPreflightRepo:
    nested = detect_nested_workspaces(info.path) if info.path.exists() and info.path.is_dir() else []
    git = git_preflight_facts(info.path)
    blocking_reasons = list(info.notes)
    warnings: list[str] = []
    if nested:
        warnings.append(
            "Nested workflow-managed project(s) detected: "
            + ", ".join(str(path.relative_to(info.path)) for path in nested)
            + "."
        )
    if git.status == "not-git":
        blocking_reasons.append("Git repository is missing; future apply is blocked until git exists.")
    elif git.status == "dirty":
        blocking_reasons.append(
            f"Git worktree has {git.dirty_path_count} changed path(s); future apply is blocked until clean."
        )

    if info.classification == "error" or git.blocks_future_apply:
        readiness = "blocked"
    elif info.classification == "v2":
        readiness = "ready"
    else:
        readiness = "needs_review"

    migration_risk = {
        "ready": "low",
        "needs_review": "medium",
        "blocked": "high",
    }[readiness]

    return HermesPreflightRepo(
        path=info.path,
        name=info.name,
        root=root,
        scaffold_classification=info.classification,
        automation_readiness=readiness,
        migration_track=_preflight_migration_track(info.classification),
        migration_risk=migration_risk,
        git=git,
        detected_flags=_preflight_detected_flags(info, nested),
        blocking_reasons=sorted(blocking_reasons),
        warnings=sorted(warnings),
        next_safe_action=_preflight_next_safe_action(
            readiness=readiness,
            classification=info.classification,
            git=git,
            blocking_reasons=blocking_reasons,
        ),
    )


def build_hermes_preflight_report() -> HermesPreflightReport:
    roots_health = evaluate_configured_roots()
    reports: list[HermesPreflightRoot] = []

    for entry in roots_health.entries:
        if entry.status == "missing":
            reports.append(
                HermesPreflightRoot(
                    path=entry.path,
                    classification="missing-root",
                    issues=[f"Configured root is missing on disk: `{entry.path}`."],
                )
            )
            continue
        if entry.status == "not-dir":
            reports.append(
                HermesPreflightRoot(
                    path=entry.path,
                    classification="invalid-root",
                    issues=[f"Configured root exists but is not a directory: `{entry.path}`."],
                )
            )
            continue

        children = sorted(
            child for child in entry.path.iterdir()
            if child.is_dir() and not child.name.startswith(".")
        )
        repos = [
            _build_preflight_repo(classify_repo(child), entry.path)
            for child in children
        ]
        reports.append(
            HermesPreflightRoot(
                path=entry.path,
                classification="configured-root",
                repos=repos,
            )
        )

    return HermesPreflightReport(roots_health=roots_health, roots=reports)


def _sorted_hermes_preflight_roots(report: HermesPreflightReport) -> list[HermesPreflightRoot]:
    return sorted(report.roots, key=lambda root: (str(root.path), root.classification))


def _sorted_hermes_preflight_projects(root: HermesPreflightRoot) -> list[HermesPreflightRepo]:
    return sorted(root.repos, key=lambda repo: (repo.name, str(repo.path)))


def hermes_preflight_payload(report: HermesPreflightReport) -> dict:
    roots: list[dict] = []
    for root in _sorted_hermes_preflight_roots(report):
        roots.append(
            {
                "path": str(root.path),
                "classification": root.classification,
                "exists": root.path.exists(),
                "is_directory": root.path.is_dir(),
                "project_count": len(root.repos),
                "issues": sorted(root.issues),
                "projects": [
                    {
                        "name": repo.name,
                        "path": str(repo.path),
                        "root": str(repo.root),
                        "scaffold_classification": repo.scaffold_classification,
                        "automation_readiness": repo.automation_readiness,
                        "migration_track": repo.migration_track,
                        "migration_risk": repo.migration_risk,
                        "git": {
                            "is_git_repo": repo.git.is_git_repo,
                            "is_dirty": repo.git.is_dirty,
                            "status": repo.git.status,
                            "dirty_path_count": repo.git.dirty_path_count,
                            "blocks_future_apply": repo.git.blocks_future_apply,
                        },
                        "detected_flags": list(repo.detected_flags),
                        "blocking_reasons": list(repo.blocking_reasons),
                        "warnings": list(repo.warnings),
                        "next_safe_action": repo.next_safe_action,
                    }
                    for repo in _sorted_hermes_preflight_projects(root)
                ],
            }
        )

    return {
        "schema_version": HERMES_PREFLIGHT_SCHEMA_VERSION,
        "command": "hermes_preflight",
        "mode": "preflight",
        "dry_run": True,
        "roots_config_path": path_or_none(report.roots_health.config_path),
        "summary": report.summary,
        "roots_info": {
            "configured_root_count": report.configured_root_count,
            "usable_root_count": report.usable_root_count,
            "missing_root_count": report.missing_root_count,
            "invalid_root_count": report.invalid_root_count,
            "project_count": report.repo_count,
        },
        "readiness_counts": report.readiness_counts,
        "roots": roots,
        "warnings": sorted(issue.message for issue in report.roots_health.warnings),
        "errors": sorted(issue.message for issue in report.roots_health.failures),
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
        "report_writing_enabled": False,
        "target_repo_file_bodies_read": False,
    }


def render_hermes_preflight_json(report: HermesPreflightReport) -> str:
    return render_json_output(hermes_preflight_payload(report))


def render_hermes_preflight_text(report: HermesPreflightReport) -> str:
    roots_source = report.roots_health.config_path or report.roots_health.source_label
    counts = report.readiness_counts
    count_line = ", ".join(f"{name}={counts[name]}" for name in ("ready", "needs_review", "blocked"))
    lines = [
        "workflow hermes preflight :: mode=dry-run",
        f"Roots source: {roots_source}",
        "Read-only: yes",
        "Depth: shallow direct-child facts only",
        "Safety: no Qwen, no Graphify, no writes, no reports, no target repo file body reads",
        f"Summary: {report.summary}",
        f"Automation readiness: {count_line}",
        "",
    ]
    for root in report.roots:
        lines.append(f"== {root.path}")
        if root.classification != "configured-root":
            lines.append(root.classification)
            for issue in root.issues:
                lines.append(f"- {issue}")
            lines.append("")
            continue
        if not root.repos:
            lines.append("(no project candidates)")
            lines.append("")
            continue
        for repo in _sorted_hermes_preflight_projects(root):
            lines.append(
                f"{repo.automation_readiness:<12} {repo.name} "
                f":: scaffold={repo.scaffold_classification}; git={repo.git.status}; "
                f"risk={repo.migration_risk}; next={repo.next_safe_action}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def hermes_preflight_command(*, dry_run: bool, as_json: bool = False) -> int:
    if not dry_run:
        raise WorkflowError(
            "`workflow hermes preflight` is intentionally dry-run only; pass `--dry-run`."
        )
    report = build_hermes_preflight_report()
    if as_json:
        print(render_hermes_preflight_json(report), end="")
        return 1 if report.roots_health.status == "fail" else 0
    print(render_hermes_preflight_text(report), end="")
    return 1 if report.roots_health.status == "fail" else 0


def _analysis_blocked_actions(repo: HermesPreflightRepo) -> list[str]:
    blocked = [
        "Qwen/DashScope analysis",
        "Graphify execution",
        "report writing",
        "migration writes",
        "target-repo writes",
        "live response parsing",
        "target-repo file-body reads",
    ]
    if repo.git.blocks_future_apply:
        blocked.append("future apply until git state is resolved")
    if repo.scaffold_classification == "error":
        blocked.append("future apply until scaffold classification is repaired")
    return sorted(blocked)


def _analysis_deterministic_evidence(repo: HermesPreflightRepo) -> list[str]:
    evidence = [
        f"preflight.scaffold_classification={repo.scaffold_classification}",
        f"preflight.automation_readiness={repo.automation_readiness}",
        f"preflight.migration_track={repo.migration_track}",
        f"preflight.migration_risk={repo.migration_risk}",
        f"preflight.git.status={repo.git.status}",
        f"preflight.git.blocks_future_apply={str(repo.git.blocks_future_apply).lower()}",
    ]
    if repo.git.dirty_path_count:
        evidence.append(f"preflight.git.dirty_path_count={repo.git.dirty_path_count}")
    if repo.detected_flags:
        evidence.append("preflight.detected_flags=" + ",".join(repo.detected_flags))
    if repo.blocking_reasons:
        evidence.append(f"preflight.blocking_reason_count={len(repo.blocking_reasons)}")
    if repo.warnings:
        evidence.append(f"preflight.warning_count={len(repo.warnings)}")
    return evidence


def _analysis_recommendation(repo: HermesPreflightRepo) -> str:
    if repo.automation_readiness == "ready":
        return "Keep this repo on the maintain-v2 track; no apply, migration, report, or Qwen action is enabled."
    if repo.automation_readiness == "blocked":
        return "Require human review and resolve preflight blockers before any future Hermes design or apply step."
    return "Require human review before choosing a future migration track; keep this slice read-only."


def _build_analysis_project(repo: HermesPreflightRepo) -> HermesAnalysisProject:
    required_human_review = (
        repo.automation_readiness != "ready"
        or bool(repo.blocking_reasons)
        or bool(repo.warnings)
        or repo.git.blocks_future_apply
    )
    return HermesAnalysisProject(
        path=repo.path,
        name=repo.name,
        root=repo.root,
        scaffold_classification=repo.scaffold_classification,
        automation_readiness=repo.automation_readiness,
        migration_track=repo.migration_track,
        migration_risk=repo.migration_risk,
        git_status=repo.git.status,
        deterministic_evidence=_analysis_deterministic_evidence(repo),
        inferred_recommendation=_analysis_recommendation(repo),
        blocked_actions=_analysis_blocked_actions(repo),
        required_human_review=required_human_review,
    )


def build_hermes_analysis_report(preflight: HermesPreflightReport | None = None) -> HermesAnalysisReport:
    preflight_report = preflight or build_hermes_preflight_report()
    roots: list[HermesAnalysisRoot] = []
    for root in _sorted_hermes_preflight_roots(preflight_report):
        roots.append(
            HermesAnalysisRoot(
                path=root.path,
                classification=root.classification,
                issues=sorted(root.issues),
                analyses=[
                    _build_analysis_project(repo)
                    for repo in _sorted_hermes_preflight_projects(root)
                ],
            )
        )
    return HermesAnalysisReport(preflight=preflight_report, roots=roots)


def _sorted_hermes_analysis_roots(report: HermesAnalysisReport) -> list[HermesAnalysisRoot]:
    return sorted(report.roots, key=lambda root: (str(root.path), root.classification))


def _sorted_hermes_analysis_projects(root: HermesAnalysisRoot) -> list[HermesAnalysisProject]:
    return sorted(root.analyses, key=lambda analysis: (analysis.name, str(analysis.path)))


def hermes_analysis_payload(report: HermesAnalysisReport) -> dict:
    roots: list[dict] = []
    for root in _sorted_hermes_analysis_roots(report):
        roots.append(
            {
                "path": str(root.path),
                "classification": root.classification,
                "project_count": len(root.analyses),
                "issues": sorted(root.issues),
                "analyses": [
                    {
                        "name": analysis.name,
                        "path": str(analysis.path),
                        "root": str(analysis.root),
                        "scaffold_classification": analysis.scaffold_classification,
                        "automation_readiness": analysis.automation_readiness,
                        "migration_track": analysis.migration_track,
                        "migration_risk": analysis.migration_risk,
                        "git_status": analysis.git_status,
                        "deterministic_evidence": list(analysis.deterministic_evidence),
                        "inferred_recommendation": analysis.inferred_recommendation,
                        "blocked_actions": list(analysis.blocked_actions),
                        "required_human_review": analysis.required_human_review,
                    }
                    for analysis in _sorted_hermes_analysis_projects(root)
                ],
            }
        )

    return {
        "schema_version": HERMES_ANALYSIS_SCHEMA_VERSION,
        "command": "hermes_analysis",
        "mode": "analysis",
        "dry_run": True,
        "roots_config_path": path_or_none(report.preflight.roots_health.config_path),
        "summary": report.summary,
        "analysis_counts": report.analysis_counts,
        "roots": roots,
        "warnings": sorted(issue.message for issue in report.preflight.roots_health.warnings),
        "errors": sorted(issue.message for issue in report.preflight.roots_health.failures),
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
        "report_writing_enabled": False,
        "target_repo_file_bodies_read": False,
        "live_response_parsing_enabled": False,
    }


def render_hermes_analysis_json(report: HermesAnalysisReport) -> str:
    return render_json_output(hermes_analysis_payload(report))


def render_hermes_analysis_text(report: HermesAnalysisReport) -> str:
    roots_source = report.preflight.roots_health.config_path or report.preflight.roots_health.source_label
    counts = report.analysis_counts
    count_line = ", ".join(
        f"{name}={counts[name]}"
        for name in ("low", "medium", "high", "requires_human_review", "blocked")
    )
    lines = [
        "workflow hermes analyze :: mode=dry-run",
        f"Roots source: {roots_source}",
        "Read-only: yes",
        "Input: deterministic in-memory preflight report",
        "Depth: shallow risk summary only",
        (
            "Safety: no Qwen, no Graphify, no connectivity probe, no reports, no migration writes, "
            "no target repo writes, no live response parsing, no target repo file body reads"
        ),
        f"Summary: {report.summary}",
        f"Analysis counts: {count_line}",
        "",
    ]
    for root in _sorted_hermes_analysis_roots(report):
        lines.append(f"== {root.path}")
        if root.classification != "configured-root":
            lines.append(root.classification)
            for issue in root.issues:
                lines.append(f"- {issue}")
            lines.append("")
            continue
        if not root.analyses:
            lines.append("(no project candidates)")
            lines.append("")
            continue
        for analysis in _sorted_hermes_analysis_projects(root):
            review = "yes" if analysis.required_human_review else "no"
            lines.append(
                f"{analysis.migration_risk:<6} {analysis.name} "
                f":: readiness={analysis.automation_readiness}; git={analysis.git_status}; "
                f"review={review}; recommendation={analysis.inferred_recommendation}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def hermes_analysis_command(*, dry_run: bool, as_json: bool = False) -> int:
    if not dry_run:
        raise WorkflowError(
            "`workflow hermes analyze` is intentionally dry-run only; pass `--dry-run`."
        )
    preflight = build_hermes_preflight_report()
    report = build_hermes_analysis_report(preflight)
    if as_json:
        print(render_hermes_analysis_json(report), end="")
        return 1 if preflight.roots_health.status == "fail" else 0
    print(render_hermes_analysis_text(report), end="")
    return 1 if preflight.roots_health.status == "fail" else 0


def _empty_count_map(keys: tuple[str, ...]) -> dict[str, int]:
    return {key: 0 for key in keys}


def _count_analysis_values(
    report: HermesAnalysisReport,
    value_getter: Callable[[HermesAnalysisProject], str],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for root in _sorted_hermes_analysis_roots(report):
        for analysis in _sorted_hermes_analysis_projects(root):
            value = value_getter(analysis)
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _analysis_evidence_category_counts(report: HermesAnalysisReport) -> dict[str, int]:
    counts: dict[str, int] = {}
    for root in _sorted_hermes_analysis_roots(report):
        for analysis in _sorted_hermes_analysis_projects(root):
            for evidence in analysis.deterministic_evidence:
                key = evidence.split("=", 1)[0]
                counts[key] = counts.get(key, 0) + 1
    ordered = dict(sorted(counts.items()))
    return dict(list(ordered.items())[:HERMES_QWEN_PREVIEW_MAX_EVIDENCE_CATEGORIES])


def _analysis_blocked_action_counts(report: HermesAnalysisReport) -> dict[str, int]:
    counts: dict[str, int] = {}
    for root in _sorted_hermes_analysis_roots(report):
        for analysis in _sorted_hermes_analysis_projects(root):
            for action in analysis.blocked_actions:
                counts[action] = counts.get(action, 0) + 1
    return dict(sorted(counts.items()))


def _qwen_preview_source_summary(report: HermesAnalysisReport) -> dict[str, object]:
    roots_health = report.preflight.roots_health
    return {
        "source_command": "hermes_analysis",
        "source_schema_version": HERMES_ANALYSIS_SCHEMA_VERSION,
        "source_mode": "analysis",
        "source_dry_run": True,
        "configured_root_count": report.configured_root_count,
        "usable_root_count": report.usable_root_count,
        "repo_candidate_count": report.repo_count,
        "roots_status": roots_health.status,
        "roots_warning_count": len(roots_health.warnings),
        "roots_error_count": len(roots_health.failures),
    }


def _qwen_preview_analysis_summary(report: HermesAnalysisReport) -> dict[str, object]:
    readiness_counts = _empty_count_map(("ready", "needs_review", "blocked"))
    for key, value in _count_analysis_values(report, lambda analysis: analysis.automation_readiness).items():
        readiness_counts[key] = value

    git_status_counts = _empty_count_map(("clean", "dirty", "not-git"))
    for key, value in _count_analysis_values(report, lambda analysis: analysis.git_status).items():
        git_status_counts[key] = value

    scaffold_counts = _empty_count_map(("v2", "legacy", "mixed", "unmanaged", "error"))
    for key, value in _count_analysis_values(report, lambda analysis: analysis.scaffold_classification).items():
        scaffold_counts[key] = value

    return {
        "summary": report.summary,
        "analysis_counts": report.analysis_counts,
        "readiness_counts": readiness_counts,
        "git_status_counts": git_status_counts,
        "scaffold_classification_counts": scaffold_counts,
        "migration_track_counts": _count_analysis_values(report, lambda analysis: analysis.migration_track),
        "blocked_action_counts": _analysis_blocked_action_counts(report),
        "evidence_category_counts": _analysis_evidence_category_counts(report),
        "evidence_category_count": len(_analysis_evidence_category_counts(report)),
    }


def _bounded_preview_section(name: str, text: str) -> str:
    if len(text) > HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS:
        raise WorkflowError(
            f"Hermes Qwen preview section `{name}` exceeds the governed section budget."
        )
    return text


def _format_counts(counts: dict[str, object]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _qwen_preview_prompt_sections(
    source_summary: dict[str, object],
    analysis_summary: dict[str, object],
) -> dict[str, str]:
    analysis_counts = dict(analysis_summary["analysis_counts"])
    readiness_counts = dict(analysis_summary["readiness_counts"])
    git_status_counts = dict(analysis_summary["git_status_counts"])
    scaffold_counts = dict(analysis_summary["scaffold_classification_counts"])
    migration_track_counts = dict(analysis_summary["migration_track_counts"])
    blocked_action_counts = dict(analysis_summary["blocked_action_counts"])
    evidence_counts = dict(analysis_summary["evidence_category_counts"])
    sections = {
        "system_role": (
            "You are the future Hermes-to-Qwen analysis assistant for workflow-manager. "
            "Use only this bounded offline analysis summary."
        ),
        "task": (
            "Preview the request and prompt contract for a future Qwen review. Do not execute the prompt, "
            "call DashScope, parse a live response, write reports, write migrations, or write target repos."
        ),
        "source_summary": (
            f"Source={source_summary['source_command']}:{source_summary['source_schema_version']}; "
            f"dry_run={str(source_summary['source_dry_run']).lower()}; "
            f"roots={source_summary['usable_root_count']}/{source_summary['configured_root_count']}; "
            f"repo_candidates={source_summary['repo_candidate_count']}; "
            f"root_warnings={source_summary['roots_warning_count']}; "
            f"root_errors={source_summary['roots_error_count']}."
        ),
        "analysis_summary": (
            f"risk={_format_counts(analysis_counts)}; readiness={_format_counts(readiness_counts)}; "
            f"git={_format_counts(git_status_counts)}; scaffolds={_format_counts(scaffold_counts)}; "
            f"tracks={_format_counts(migration_track_counts)}."
        ),
        "evidence_category_summary": (
            f"Evidence categories only, capped at {HERMES_QWEN_PREVIEW_MAX_EVIDENCE_CATEGORIES}: "
            f"{_format_counts(evidence_counts)}. Blocked actions: {_format_counts(blocked_action_counts)}."
        ),
        "safety_constraints": (
            "Keep runtime_enabled=false, network_calls_allowed=false, qwen_dashscope_enabled=false, "
            "prompt_execution_enabled=false, graphify_enabled=false, migration_writes_enabled=false, "
            "report_writing_enabled=false, target_repo_file_bodies_read=false, and target_repos_modified=false."
        ),
        "expected_output_shape": (
            "Future output, if separately approved, should be concise structured metadata with readiness_status, "
            "risk_summary, evidence_references, blockers_or_open_questions, and next_safe_step."
        ),
        "redaction_policy": (
            "Do not include root paths, project paths, API-key values, Authorization headers, .env values, "
            "target source/docs/continuity bodies, AGENTS/CLAUDE/GEMINI bodies, hidden reasoning, or migration writes."
        ),
    }
    return {
        name: _bounded_preview_section(name, text)
        for name, text in sections.items()
    }


def _assemble_qwen_preview_prompt(sections: dict[str, str]) -> str:
    parts: list[str] = []
    for name, text in sections.items():
        title = name.replace("_", " ").title()
        parts.append(f"## {title}")
        parts.append(text)
        parts.append("")
    assembled = "\n".join(parts).rstrip() + "\n"
    if len(assembled) > HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS:
        raise WorkflowError("Hermes Qwen preview exceeds the governed assembled prompt budget.")
    return assembled


def _qwen_preview_safe_issue_counts(report: HermesAnalysisReport) -> tuple[list[str], list[str]]:
    roots_health = report.preflight.roots_health
    warnings: list[str] = []
    errors: list[str] = []
    if roots_health.warnings:
        warnings.append("Roots warnings are present but path details are redacted from qwen-preview output.")
    if roots_health.failures:
        errors.append("Roots configuration failed; path details are redacted from qwen-preview output.")
    return warnings, errors


def _qwen_preview_selected_model(readiness: object) -> str:
    selected_model = getattr(readiness, "selected_model_name", None) or getattr(
        readiness,
        "intended_model_name",
        DASHSCOPE_INTENDED_MODEL,
    )
    if selected_model == DASHSCOPE_INTENDED_MODEL:
        return DASHSCOPE_INTENDED_MODEL
    return "<redacted-model-override>"


def build_hermes_qwen_preview_report(
    analysis: HermesAnalysisReport | None = None,
    *,
    repo: Path | None = None,
) -> HermesQwenPreviewReport:
    analysis_report = analysis or build_hermes_analysis_report(build_hermes_preflight_report())
    readiness = inspect_dashscope_local_readiness(repo or workflow_manager_home())
    selected_model = _qwen_preview_selected_model(readiness)
    source_summary = _qwen_preview_source_summary(analysis_report)
    analysis_summary = _qwen_preview_analysis_summary(analysis_report)
    sections = _qwen_preview_prompt_sections(source_summary, analysis_summary)
    assembled_prompt = _assemble_qwen_preview_prompt(sections)
    request_preview = {
        "request_shape": "dashscope-qwen-chat-completions-preview",
        "source_command": "hermes_analysis",
        "source_schema_version": HERMES_ANALYSIS_SCHEMA_VERSION,
        "source_mode": "analysis",
        "source_dry_run": True,
        "intended_model": DASHSCOPE_INTENDED_MODEL,
        "selected_model": selected_model,
        "model_policy_status": readiness.model_policy_status,
        "model_policy_ready": readiness.model_policy_ready,
        "model_policy_requires_update": readiness.model_policy_requires_update,
        "local_config_ready": readiness.local_config_ready,
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
    }
    prompt_preview = {
        "preview_type": "bounded_prompt_preview",
        "preview_only": True,
        "prompt_execution_enabled": False,
        "section_order": list(sections.keys()),
        "section_char_counts": {name: len(text) for name, text in sections.items()},
        "sections": sections,
        "assembled_prompt_preview": assembled_prompt,
        "assembled_prompt_char_count": len(assembled_prompt),
        "max_section_chars": HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS,
        "max_assembled_prompt_chars": HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS,
    }
    warnings, errors = _qwen_preview_safe_issue_counts(analysis_report)
    return HermesQwenPreviewReport(
        analysis=analysis_report,
        selected_model=selected_model,
        model_policy_status=readiness.model_policy_status,
        model_policy_ready=readiness.model_policy_ready,
        model_policy_requires_update=readiness.model_policy_requires_update,
        local_config_ready=readiness.local_config_ready,
        source_summary=source_summary,
        analysis_summary=analysis_summary,
        request_preview=request_preview,
        prompt_preview=prompt_preview,
        warnings=warnings,
        errors=errors,
    )


def hermes_qwen_preview_payload(report: HermesQwenPreviewReport) -> dict[str, object]:
    return {
        "schema_version": HERMES_QWEN_PREVIEW_SCHEMA_VERSION,
        "command": "hermes_qwen_preview",
        "mode": "offline_qwen_preview",
        "dry_run": True,
        "source": "hermes_analysis",
        "source_schema_version": HERMES_ANALYSIS_SCHEMA_VERSION,
        "intended_model": DASHSCOPE_INTENDED_MODEL,
        "selected_model": report.selected_model,
        "model_policy_status": report.model_policy_status,
        "model_policy_ready": report.model_policy_ready,
        "model_policy_requires_update": report.model_policy_requires_update,
        "local_config_ready": report.local_config_ready,
        "preview_limits": {
            "max_section_chars": HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS,
            "max_assembled_prompt_chars": HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS,
            "max_evidence_categories": HERMES_QWEN_PREVIEW_MAX_EVIDENCE_CATEGORIES,
        },
        "source_summary": dict(report.source_summary),
        "analysis_summary": dict(report.analysis_summary),
        "request_preview": dict(report.request_preview),
        "prompt_preview": dict(report.prompt_preview),
        "warnings": list(report.warnings),
        "errors": list(report.errors),
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


def render_hermes_qwen_preview_json(report: HermesQwenPreviewReport) -> str:
    return render_json_output(hermes_qwen_preview_payload(report))


def render_hermes_qwen_preview_text(report: HermesQwenPreviewReport) -> str:
    sections = report.prompt_preview["sections"]
    source_summary = report.source_summary
    analysis_summary = report.analysis_summary
    lines = [
        "workflow hermes qwen-preview :: mode=dry-run",
        "Read-only: yes",
        "Input: bounded deterministic Hermes analysis summary",
        "Output: offline request/prompt preview only",
        (
            "Safety: no network, no connectivity probe, no prompt execution, no live response parsing, "
            "no Graphify, no reports, no migration writes, no target repo writes, no target repo file body reads"
        ),
        (
            "Redaction: root paths, project paths, .env values, API-key values, Authorization headers, "
            "target source/docs/continuity bodies, and AGENTS/CLAUDE/GEMINI bodies are excluded"
        ),
        f"Model: intended={DASHSCOPE_INTENDED_MODEL}; selected={report.selected_model}; policy={report.model_policy_status}",
        (
            f"Source summary: roots={source_summary['usable_root_count']}/{source_summary['configured_root_count']}; "
            f"repo_candidates={source_summary['repo_candidate_count']}; "
            f"root_warnings={source_summary['roots_warning_count']}; root_errors={source_summary['roots_error_count']}"
        ),
        f"Analysis summary: {analysis_summary['summary']}",
        (
            f"Preview budget: max_section_chars={HERMES_QWEN_PREVIEW_MAX_SECTION_CHARS}; "
            f"max_assembled_prompt_chars={HERMES_QWEN_PREVIEW_MAX_ASSEMBLED_CHARS}; "
            f"assembled_prompt_chars={report.prompt_preview['assembled_prompt_char_count']}"
        ),
        "",
        "Prompt preview:",
    ]
    for name in report.prompt_preview["section_order"]:
        lines.append(f"## {str(name).replace('_', ' ').title()}")
        lines.append(str(sections[name]))
        lines.append("")
    if report.warnings:
        lines.append("Warnings:")
        for warning in report.warnings:
            lines.append(f"- {warning}")
    if report.errors:
        lines.append("Errors:")
        for error in report.errors:
            lines.append(f"- {error}")
    return "\n".join(lines).rstrip() + "\n"


def hermes_qwen_preview_command(*, dry_run: bool, as_json: bool = False) -> int:
    if not dry_run:
        raise WorkflowError(
            "`workflow hermes qwen-preview` is intentionally dry-run only; pass `--dry-run`."
        )
    preflight = build_hermes_preflight_report()
    analysis = build_hermes_analysis_report(preflight)
    report = build_hermes_qwen_preview_report(analysis)
    if as_json:
        print(render_hermes_qwen_preview_json(report), end="")
        return 1 if preflight.roots_health.status == "fail" else 0
    print(render_hermes_qwen_preview_text(report), end="")
    return 1 if preflight.roots_health.status == "fail" else 0


def _bool_label(value: bool) -> str:
    return "yes" if value else "no"


def _dashscope_connectivity_operator_gate_reason(
    *,
    probe_flag: bool,
    no_content_flag: bool,
    yes_network_flag: bool,
    interactive_session: bool,
    operator_gate_satisfied: bool,
) -> str | None:
    if operator_gate_satisfied:
        return None
    if not (probe_flag and no_content_flag and yes_network_flag):
        return "network stays disabled until `--probe --no-content --yes-network` are all present."
    if not interactive_session:
        return (
            "live probing is refused in non-interactive runs; rerun the same command manually in an "
            "interactive operator session to attempt the no-content probe."
        )
    return "operator gating prevented the connectivity probe."


def build_dashscope_connectivity_json_payload(
    result: DashScopeConnectivityProbeResult | dict[str, object] | object,
    *,
    probe_flag: bool,
    no_content_flag: bool,
    yes_network_flag: bool,
    interactive_session: bool,
    operator_gate_satisfied: bool,
) -> dict[str, object]:
    payload = result.to_safe_dict() if hasattr(result, "to_safe_dict") else dict(result)
    gate_reason = _dashscope_connectivity_operator_gate_reason(
        probe_flag=probe_flag,
        no_content_flag=no_content_flag,
        yes_network_flag=yes_network_flag,
        interactive_session=interactive_session,
        operator_gate_satisfied=operator_gate_satisfied,
    )

    warnings: list[str] = []
    errors: list[str] = []
    if gate_reason:
        warnings.append(gate_reason)
    else:
        connectivity_status = payload["connectivity_status"]
        sanitized_error_category = payload["sanitized_error_category"]
        if connectivity_status == "not-configured":
            if sanitized_error_category == "missing-api-key":
                warnings.append("Local DashScope configuration is missing an active API key.")
            else:
                warnings.append("Local DashScope configuration is not ready for a live probe.")
        elif connectivity_status == "model-policy-mismatch":
            warnings.append("Selected model does not match the governed qwen3.6-plus connectivity policy.")
        elif connectivity_status != "reachable":
            errors.append(
                "Connectivity probe ended with safe status "
                f"`{connectivity_status}` and sanitized error category `{sanitized_error_category}`."
            )

    return {
        "schema_version": DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION,
        "command": "hermes_qwen_connectivity",
        "mode": payload["mode"],
        "intended_model": payload["intended_model"],
        "selected_model": payload["selected_model"],
        "selected_api_key_name": payload["selected_api_key_name"],
        "selected_api_key_category": payload["selected_api_key_category"],
        "local_config_ready": payload["local_config_ready"],
        "model_policy_status": payload["model_policy_status"],
        "probe_requested": probe_flag,
        "no_content": no_content_flag,
        "yes_network": yes_network_flag,
        "interactive_required": True,
        "interactive_session": interactive_session,
        "operator_gate_satisfied": operator_gate_satisfied,
        "network_attempted": payload["network_attempted"],
        "connectivity_status": payload["connectivity_status"],
        "sanitized_error_category": payload["sanitized_error_category"],
        "http_status_category": payload["http_status_category"],
        "request_method": payload["request_method"],
        "request_body_kind": payload["request_body_kind"],
        "request_body_bytes_length": payload["request_body_bytes_length"],
        "project_content_sent": payload["project_content_sent"],
        "inventory_content_sent": payload["inventory_content_sent"],
        "prompt_preview_content_sent": payload["prompt_preview_content_sent"],
        "target_repo_content_sent": payload["target_repo_content_sent"],
        "qwen_analysis_enabled": payload["qwen_analysis_enabled"],
        "report_writing_enabled": payload["report_writing_enabled"],
        "migration_writes_enabled": False,
        "graphify_enabled": False,
        "health_surface_integration_enabled": payload["health_surface_integration_enabled"],
        "warnings": warnings,
        "errors": errors,
    }


def render_dashscope_connectivity_text(
    result: DashScopeConnectivityProbeResult | dict[str, object] | object,
    *,
    probe_flag: bool,
    no_content_flag: bool,
    yes_network_flag: bool,
    interactive_session: bool,
    operator_gate_satisfied: bool,
) -> str:
    payload = result.to_safe_dict() if hasattr(result, "to_safe_dict") else dict(result)
    gate_reason = _dashscope_connectivity_operator_gate_reason(
        probe_flag=probe_flag,
        no_content_flag=no_content_flag,
        yes_network_flag=yes_network_flag,
        interactive_session=interactive_session,
        operator_gate_satisfied=operator_gate_satisfied,
    )
    lines = [
        "workflow hermes qwen-connectivity :: mode=explicit-opt-in-no-content",
        f"- intended model: {payload['intended_model']}",
        f"- selected model: {payload['selected_model']}",
        f"- selected api key name: {payload['selected_api_key_name'] or 'none'}",
        f"- selected api key category: {payload['selected_api_key_category'] or 'none'}",
        f"- local config ready: {_bool_label(bool(payload['local_config_ready']))}",
        f"- model policy status: {payload['model_policy_status']}",
        f"- probe flag present: {_bool_label(probe_flag)}",
        f"- no-content flag present: {_bool_label(no_content_flag)}",
        f"- yes-network flag present: {_bool_label(yes_network_flag)}",
        f"- interactive operator session: {_bool_label(interactive_session)}",
        f"- operator gate satisfied: {_bool_label(operator_gate_satisfied)}",
        f"- network attempted: {_bool_label(bool(payload['network_attempted']))}",
        f"- connectivity status: {payload['connectivity_status']}",
        f"- sanitized error category: {payload['sanitized_error_category']}",
        f"- http status category: {payload['http_status_category']}",
        f"- request method: {payload['request_method']}",
        f"- request body kind: {payload['request_body_kind']}",
        f"- request body bytes length: {payload['request_body_bytes_length']}",
        f"- no project content sent: {_bool_label(not bool(payload['project_content_sent']))}",
        f"- no Hermes inventory content sent: {_bool_label(not bool(payload['inventory_content_sent']))}",
        f"- no prompt preview content sent: {_bool_label(not bool(payload['prompt_preview_content_sent']))}",
        f"- no target-repo content sent: {_bool_label(not bool(payload['target_repo_content_sent']))}",
        f"- qwen analysis enabled: {_bool_label(bool(payload['qwen_analysis_enabled']))}",
        f"- report writing enabled: {_bool_label(bool(payload['report_writing_enabled']))}",
        "- migration writes enabled: no",
        f"- connectivity health integration enabled: {_bool_label(bool(payload['health_surface_integration_enabled']))}",
    ]

    if gate_reason is not None:
        lines.append(f"- operator gate reason: {gate_reason}")

    lines.append(
        "- safety policy: this command keeps project content, Hermes inventory content, prompt preview content, target-repo content, docs/state bodies, AGENTS/CLAUDE/GEMINI bodies, migration instructions, and secrets out of the probe."
    )
    return "\n".join(lines) + "\n"


def hermes_qwen_connectivity_command(
    *,
    probe: bool,
    no_content: bool,
    yes_network: bool,
    repo: Path | None = None,
    transport: DashScopeConnectivityTransport | None = None,
    interactive_session: bool | None = None,
    as_json: bool = False,
) -> int:
    repo_root = repo or workflow_manager_home()
    readiness = inspect_dashscope_local_readiness(repo_root)
    if interactive_session is None:
        interactive_session = sys.stdin.isatty() and sys.stdout.isatty()

    operator_gate_satisfied = probe and no_content and yes_network and interactive_session
    result = probe_dashscope_connectivity(
        readiness,
        probe_requested=operator_gate_satisfied,
        transport=transport,
    )
    if as_json:
        print(
            render_json_output(
                build_dashscope_connectivity_json_payload(
                    result,
                    probe_flag=probe,
                    no_content_flag=no_content,
                    yes_network_flag=yes_network,
                    interactive_session=interactive_session,
                    operator_gate_satisfied=operator_gate_satisfied,
                )
            ),
            end="",
        )
        return 0 if operator_gate_satisfied and result.connectivity_status == "reachable" else 1
    print(
        render_dashscope_connectivity_text(
            result,
            probe_flag=probe,
            no_content_flag=no_content,
            yes_network_flag=yes_network,
            interactive_session=interactive_session,
            operator_gate_satisfied=operator_gate_satisfied,
        ),
        end="",
    )
    return 0 if operator_gate_satisfied and result.connectivity_status == "reachable" else 1


def close_guidance(info: RepoInfo) -> tuple[list[str], Path | None]:
    if info.classification == "v2":
        lines = [
            f"workflow close :: repo={info.path}",
            "Classification: v2",
            f"- Update `{relative_display(info.handoff_path, info.path)}` before leaving.",
            f"- Update `{relative_display(info.active_path, info.path)}` if the active task or focus changed.",
            f"- Update `{relative_display(info.progress_path, info.path)}` if meaningful work completed.",
            "- Run `workflow save` to append the session marker.",
            "- Run `workflow sync` if `AGENTS.md` changed.",
            "- Run `workflow doctor --write-report` if migration-state files or generated artifacts changed.",
        ]
        if info.legacy_session_log_path:
            lines.append(
                f"- Coexistence mirror available: `{relative_display(info.legacy_session_log_path, info.path)}`"
            )
        return lines, info.handoff_path

    if info.classification == "legacy":
        lines = [
            f"workflow close :: repo={info.path}",
            "Classification: legacy",
            f"- Update `{relative_display(info.legacy_handoff_path, info.path)}` before leaving.",
            f"- Append a concise summary to `{relative_display(info.legacy_session_log_path, info.path)}`.",
            "- `project-save` will continue writing the legacy session marker for this repo.",
            "- Run `workflow init` when this repo is ready for v2 continuity.",
        ]
        return lines, info.legacy_handoff_path

    if info.classification == "mixed":
        lines = [
            f"workflow close :: repo={info.path}",
            "Classification: mixed",
            "- Mixed workflow state detected. Do not assume either continuity layer is authoritative.",
            "- Review both `.specify/*` and `.ai/*` before closing the session.",
            "- Resolve the mixed scaffold state before relying on `workflow save`.",
        ]
        if info.handoff_path:
            lines.append(f"- V2 handoff candidate: `{relative_display(info.handoff_path, info.path)}`")
        if info.legacy_handoff_path:
            lines.append(f"- Legacy handoff candidate: `{relative_display(info.legacy_handoff_path, info.path)}`")
        return lines, None

    if info.classification == "unmanaged":
        lines = [
            f"workflow close :: repo={info.path}",
            "Classification: unmanaged",
            "- No managed workflow scaffold was detected.",
            "- Either leave the repo unmanaged or run `workflow init` before expecting continuity automation.",
        ]
        return lines, None

    lines = [
        f"workflow close :: repo={info.path}",
        "Classification: error",
        "- Resolve the repository error before using workflow close/save guidance.",
    ]
    lines.extend(f"- {note}" for note in info.notes)
    return lines, None


def close_project(repo: Path, format_name: str) -> int:
    info = classify_repo(repo)
    lines, suggested_path = close_guidance(info)
    if format_name == "shell":
        print(
            render_shell_assignments(
                {
                    "WORKFLOW_CLOSE_CLASSIFICATION": info.classification,
                    "WORKFLOW_CLOSE_OPEN_PATH": str(suggested_path) if suggested_path else "",
                }
            )
        )
        return 0
    print("\n".join(lines))
    return 0


def save_project(repo: Path) -> int:
    info = classify_repo(repo)
    label = f"{now_short()}: Session closed: {info.name}"

    if info.classification == "v2":
        if info.session_log_path is None:
            raise WorkflowError("V2 repo is missing `.specify/state/session.log.md`.")
        append_text(info.session_log_path, f"- {label}\n")
        wrote_legacy = False
        if info.legacy_session_log_path is not None:
            append_text(info.legacy_session_log_path, f"[{now_short()}] Session closed: {info.name}\n")
            wrote_legacy = True
        print(f"workflow save :: repo={info.path}")
        print(f"- appended primary session marker to `{relative_display(info.session_log_path, info.path)}`")
        if wrote_legacy:
            print(f"- appended coexistence mirror to `{relative_display(info.legacy_session_log_path, info.path)}`")
        print("- reminder: update handoff, active state, and progress when the session changed them")
        return 0

    if info.classification == "legacy":
        legacy_log = info.legacy_session_log_path or (repo / ".ai/logs/session.log")
        append_text(legacy_log, f"[{now_short()}] Session closed: {info.name}\n")
        print(f"workflow save :: repo={info.path}")
        print(f"- appended legacy session marker to `{relative_display(legacy_log, info.path)}`")
        print("- reminder: update `.ai/handoffs/NEXT_STEP.md` before leaving")
        return 0

    if info.classification == "mixed":
        raise WorkflowError(
            "Refusing to save a mixed scaffold automatically. Resolve the mixed state before writing session markers."
        )
    if info.classification == "unmanaged":
        raise WorkflowError("Refusing to save an unmanaged repo. Run `workflow init` first if it should be managed.")
    raise WorkflowError("Refusing to save because the repo is in an error state.")


def doctor_roots_notes(roots_health: RootsHealth) -> list[str]:
    config_path = str(roots_health.config_path) if roots_health.config_path is not None else "Unavailable."
    safe = "safe" if roots_health.status == "pass" else "review required"
    return [
        f"roots health: {roots_health.status}",
        f"roots config: {config_path}",
        f"roots summary: {roots_health.summary}",
        f"default root operations: {safe}",
    ]


def doctor_roots_findings(roots_health: RootsHealth) -> list[str]:
    findings: list[str] = []
    for issue in roots_health.failures:
        findings.append(f"Roots error: {issue.message}")
    for issue in roots_health.warnings:
        findings.append(f"Roots warning: {issue.message}")
    return findings


def doctor_manifest_notes(manifest_health: ManifestHealth) -> list[str]:
    return [
        f"manifest health: {manifest_health.status}",
        f"manifest path: {manifest_health.manifest_path}",
        f"manifest summary: {manifest_health.summary}",
    ]


def doctor_manifest_findings(manifest_health: ManifestHealth) -> list[str]:
    findings: list[str] = []
    for issue in manifest_health.failures:
        findings.append(f"Manifest error: {issue.message}")
    for issue in manifest_health.warnings:
        findings.append(f"Manifest warning: {issue.message}")
    return findings


def doctor_mirror_notes(mirror_health: MirrorHealth) -> list[str]:
    return [
        f"mirror-lock/shim health: {mirror_health.status}",
        f"mirror-lock/shim path: {mirror_health.lock_path}",
        f"mirror-lock/shim summary: {mirror_health.summary}",
        f"workflow sync needed: {'yes' if mirror_health.sync_needed else 'no'}",
    ]


def doctor_mirror_findings(mirror_health: MirrorHealth) -> list[str]:
    findings: list[str] = []
    for issue in mirror_health.failures:
        findings.append(f"Mirror-lock/shim error: {issue.message}")
    for issue in mirror_health.warnings:
        findings.append(f"Mirror-lock/shim warning: {issue.message}")
    return findings


def doctor_continuity_notes(continuity_health: ContinuityStateHealth) -> list[str]:
    return [
        f"continuity-state health: {continuity_health.status}",
        f"continuity-state root: {continuity_health.state_root}",
        f"continuity-state summary: {continuity_health.summary}",
    ]


def doctor_continuity_findings(continuity_health: ContinuityStateHealth) -> list[str]:
    findings: list[str] = []
    for issue in continuity_health.failures:
        findings.append(f"Continuity-state error: {issue.message}")
    for issue in continuity_health.warnings:
        findings.append(f"Continuity-state warning: {issue.message}")
    return findings


def doctor_memory_notes(memory_health: MemoryHealth) -> list[str]:
    return [
        f"memory health: {memory_health.status}",
        f"memory root: {memory_health.memory_root}",
        f"memory summary: {memory_health.summary}",
    ]


def doctor_memory_findings(memory_health: MemoryHealth) -> list[str]:
    findings: list[str] = []
    for issue in memory_health.failures:
        findings.append(f"Memory error: {issue.message}")
    for issue in memory_health.warnings:
        findings.append(f"Memory warning: {issue.message}")
    return findings


def doctor_command_docs_notes(command_docs_health: CommandDocsHealth) -> list[str]:
    return [
        f"command/help/docs consistency: {command_docs_health.status}",
        f"command/help/docs root: {command_docs_health.manager_home}",
        f"command/help/docs summary: {command_docs_health.summary}",
    ]


def doctor_command_docs_findings(command_docs_health: CommandDocsHealth) -> list[str]:
    findings: list[str] = []
    for issue in command_docs_health.failures:
        findings.append(f"Command/help/docs error: {issue.message}")
    for issue in command_docs_health.warnings:
        findings.append(f"Command/help/docs warning: {issue.message}")
    return findings


def doctor_role_contract_notes(role_contract_health: RoleContractHealth) -> list[str]:
    return [
        f"role-contract health: {role_contract_health.status}",
        f"role-contract path: {role_contract_health.contract_path}",
        f"role-contract summary: {role_contract_health.summary}",
    ]


def doctor_role_contract_findings(role_contract_health: RoleContractHealth) -> list[str]:
    findings: list[str] = []
    for issue in role_contract_health.failures:
        findings.append(f"Role-contract error: {issue.message}")
    for issue in role_contract_health.warnings:
        findings.append(f"Role-contract warning: {issue.message}")
    return findings


def doctor_docs_health_notes(docs_health: DocsHealth) -> list[str]:
    return [
        f"docs-health: {docs_health.status}",
        f"docs-health root: {docs_health.repo}",
        f"docs-health summary: {docs_health.summary}",
    ]


def doctor_docs_health_findings(docs_health: DocsHealth) -> list[str]:
    findings: list[str] = []
    for issue in docs_health.failures:
        findings.append(f"Docs-health error: {issue.message}")
    for issue in docs_health.warnings:
        findings.append(f"Docs-health warning: {issue.message}")
    return findings


def doctor_health_overview_notes(overview: HealthOverview) -> list[str]:
    return [
        f"health overview: {overview.overall_status}",
        f"health summary: {overview.summary}",
        (
            "health subsystems: "
            f"command/help/docs={overview.command_docs_status}, "
            f"manifest={overview.manifest_status}, "
            f"mirror-lock/shim={overview.mirror_status}, "
            f"memory={overview.memory_status}, "
            f"continuity-state={overview.continuity_status}, "
            f"roots={overview.roots_status}, "
            f"role-contract={overview.role_contract_status}, "
            f"docs-health={overview.docs_status}"
        ),
        f"sync needed: {'yes' if overview.sync_needed else 'no'}",
        f"default-root operations safe: {'yes' if overview.default_root_operations_safe else 'no'}",
        f"pre-hermes readiness: {overview.pre_hermes_readiness}",
    ]


def render_health_section(title: str, details: list[str], issues: list[HealthIssue]) -> list[str]:
    lines = ["", title]
    lines.extend(details)
    for issue in issues:
        lines.append(f"- {issue.level.title()}: {issue.message}")
    return lines


def doctor_result_payload(result: DoctorResult) -> dict:
    findings = [parse_doctor_finding(error) for error in result.errors]
    return {
        "schema_version": MACHINE_OUTPUT_SCHEMA_VERSION,
        "command": "doctor",
        "repo_path": str(result.repo),
        "classification": result.info.classification,
        "result_status": "pass" if not result.errors else "fail",
        "passed": not result.errors,
        "wrote_report": result.wrote_report,
        "drift_report_path": path_or_none(result.drift_report_path),
        "health_overview": serialize_health_overview(result.overview),
        "health": serialize_health_bundle(
            result.command_docs_health,
            result.manifest_health,
            result.mirror_health,
            result.memory_health,
            result.continuity_health,
            result.roots_health,
            result.role_contract_health,
            result.docs_health,
        ),
        "notes": list(result.notes),
        "findings": findings,
        "errors": [finding["message"] for finding in findings if finding["level"] == "error"],
        "warnings": [finding["message"] for finding in findings if finding["level"] == "warning"],
    }


def render_doctor_report(
    errors: list[str],
    notes: list[str],
    overview: HealthOverview,
    command_docs_health: CommandDocsHealth,
    manifest_health: ManifestHealth,
    mirror_health: MirrorHealth,
    memory_health: MemoryHealth,
    continuity_health: ContinuityStateHealth,
    roots_health: RootsHealth,
    role_contract_health: RoleContractHealth,
    docs_health: DocsHealth,
) -> str:
    status = "pass" if not errors else "fail"
    lines = [
        "# Drift Report",
        "",
        f"Updated: {now_short()}",
        "",
        "## Latest summary",
        f"- Status: {status}",
    ]
    for note in notes:
        lines.append(f"- {note}")
    lines.extend(
        render_health_section(
            "## Health overview",
            [
                f"- Overall health: {overview.overall_status}",
                f"- Summary: {overview.summary}",
                (
                    "- Subsystems: "
                    f"command/help/docs={overview.command_docs_status}, "
                    f"manifest={overview.manifest_status}, "
                    f"mirror-lock/shim={overview.mirror_status}, "
                    f"memory={overview.memory_status}, "
                    f"continuity-state={overview.continuity_status}, "
                    f"roots={overview.roots_status}, "
                    f"role-contract={overview.role_contract_status}, "
                    f"docs-health={overview.docs_status}"
                ),
                f"- Sync needed: {'yes' if overview.sync_needed else 'no'}",
                (
                    "- Default-root operations safe: "
                    f"{'yes' if overview.default_root_operations_safe else 'no'}"
                ),
                f"- Pre-Hermes readiness: {overview.pre_hermes_readiness}",
            ],
            [],
        )
    )
    lines.extend(
        render_health_section(
            "## Command/help/docs consistency",
            [
                f"- Status: {command_docs_health.status}",
                f"- Path: `{command_docs_health.manager_home}`",
                f"- Summary: {command_docs_health.summary}",
            ],
            command_docs_health.issues,
        )
    )
    lines.extend(
        render_health_section(
            "## Manifest health",
            [
                f"- Status: {manifest_health.status}",
                f"- Path: `{manifest_health.manifest_path}`",
                f"- Summary: {manifest_health.summary}",
            ],
            manifest_health.issues,
        )
    )
    lines.extend(
        render_health_section(
            "## Role-contract health",
            [
                f"- Status: {role_contract_health.status}",
                f"- Path: `{role_contract_health.contract_path}`",
                f"- Summary: {role_contract_health.summary}",
                "- Canonical roles: " + ", ".join(role_contract_health.canonical_roles),
                "- Reserved roles: " + ", ".join(role_contract_health.reserved_roles),
            ],
            role_contract_health.issues,
        )
    )
    lines.extend(
        render_health_section(
            "## Docs health",
            [
                f"- Status: {docs_health.status}",
                f"- Path: `{docs_health.repo}`",
                f"- Summary: {docs_health.summary}",
            ],
            [HealthIssue(issue.level, issue.message) for issue in docs_health.issues],
        )
    )
    lines.extend(
        render_health_section(
            "## Mirror-lock/shim health",
            [
                f"- Status: {mirror_health.status}",
                f"- Path: `{mirror_health.lock_path}`",
                f"- Summary: {mirror_health.summary}",
                f"- Sync needed: {'yes' if mirror_health.sync_needed else 'no'}",
            ],
            mirror_health.issues,
        )
    )
    lines.extend(
        render_health_section(
            "## Memory health",
            [
                f"- Status: {memory_health.status}",
                f"- Path: `{memory_health.memory_root}`",
                f"- Summary: {memory_health.summary}",
            ],
            memory_health.issues,
        )
    )
    lines.extend(
        render_health_section(
            "## Continuity-state health",
            [
                f"- Status: {continuity_health.status}",
                f"- Path: `{continuity_health.state_root}`",
                f"- Summary: {continuity_health.summary}",
            ],
            continuity_health.issues,
        )
    )
    config_path = str(roots_health.config_path) if roots_health.config_path is not None else "Unavailable."
    lines.extend(
        render_health_section(
            "## Roots health",
            [
                f"- Status: {roots_health.status}",
                f"- Config path: `{config_path}`",
                f"- Summary: {roots_health.summary}",
                f"- Default root-based operations safe: {'yes' if roots_health.status == 'pass' else 'no'}",
            ],
            roots_health.issues,
        )
    )
    if errors:
        lines.append("")
        lines.append("## Findings")
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines).rstrip() + "\n"


def sanitize_committed_report_paths(text: str, repo: Path) -> str:
    repo_root = str(repo.resolve())
    return text.replace(repo_root, "<repo-root>")


def doctor(repo: Path, *, write_report: bool) -> DoctorResult:
    errors: list[str] = []
    notes: list[str] = []
    info = classify_repo(repo)
    command_docs_health = evaluate_command_docs_health()
    manifest_health = evaluate_manifest_health(repo)
    mirror_health = evaluate_mirror_health(repo)
    memory_health = evaluate_memory_health(repo, manifest_health)
    continuity_health = evaluate_continuity_state_health(repo, manifest_health)
    roots_health = evaluate_configured_roots()
    role_contract_health = evaluate_role_contract_health(repo)
    docs_health = evaluate_docs_health(repo)
    overview = evaluate_health_overview(
        command_docs_health,
        manifest_health,
        mirror_health,
        memory_health,
        continuity_health,
        roots_health,
        role_contract_health,
        docs_health,
    )

    notes.extend(doctor_health_overview_notes(overview))
    notes.extend(doctor_command_docs_notes(command_docs_health))
    errors.extend(doctor_command_docs_findings(command_docs_health))
    notes.extend(doctor_role_contract_notes(role_contract_health))
    errors.extend(doctor_role_contract_findings(role_contract_health))
    notes.extend(doctor_docs_health_notes(docs_health))
    errors.extend(doctor_docs_health_findings(docs_health))
    notes.extend(doctor_manifest_notes(manifest_health))
    errors.extend(doctor_manifest_findings(manifest_health))
    notes.extend(doctor_mirror_notes(mirror_health))
    errors.extend(doctor_mirror_findings(mirror_health))
    notes.extend(doctor_memory_notes(memory_health))
    errors.extend(doctor_memory_findings(memory_health))
    notes.extend(doctor_continuity_notes(continuity_health))
    errors.extend(doctor_continuity_findings(continuity_health))
    notes.extend(doctor_roots_notes(roots_health))
    errors.extend(doctor_roots_findings(roots_health))

    manifest = manifest_health.manifest if manifest_health.status == "pass" and manifest_health.manifest is not None else {}
    memory_root = repo / manifest.get("memory_root", DEFAULT_MEMORY_ROOT)
    state_root = repo / manifest.get("state_root", DEFAULT_STATE_ROOT)
    legacy_root = repo / manifest.get("legacy_root", DEFAULT_LEGACY_ROOT)
    report_path = state_root / "drift.md" if write_report else None

    for filename in REQUIRED_STATE_FILES:
        if filename in CONTINUITY_STATE_FILES:
            continue
        path = state_root / filename
        if not path.exists():
            errors.append(f"Missing required state file `{path.relative_to(repo)}`.")
        elif not read_text(path).strip():
            errors.append(f"Required state file `{path.relative_to(repo)}` is empty.")

    spec_dir_exists = (repo / ".specify").exists()
    workflow_dir_exists = (repo / ".workflow").exists()
    if spec_dir_exists != workflow_dir_exists:
        errors.append("Half-migrated repo detected: `.specify/` and `.workflow/` must either both exist or both be absent.")

    if manifest_health.status == "pass":
        migration = manifest.get("migration", {})
        if legacy_root.exists() and spec_dir_exists and migration.get("status") not in {"coexist", "legacy"}:
            errors.append("Legacy `.ai/` and v2 `.specify/` coexist, but manifest migration status does not allow coexistence.")

    nested = detect_nested_workspaces(repo)
    if nested and manifest.get("features") is not None and not manifest.get("features", {}).get("nested_workspaces"):
        errors.append("Nested workflow-managed workspaces were detected but `nested_workspaces` is disabled in the manifest.")

    notes.append(f"git: {git_summary(repo)}")
    notes.append("legacy coexistence: expected" if legacy_root.exists() else "legacy coexistence: none detected")

    if write_report:
        report_text = render_doctor_report(
                errors,
                notes,
                overview,
                command_docs_health,
                manifest_health,
                mirror_health,
                memory_health,
                continuity_health,
                roots_health,
                role_contract_health,
                docs_health,
        )
        write_text_atomic(report_path, sanitize_committed_report_paths(report_text, repo))

    return DoctorResult(
        repo=repo,
        info=info,
        errors=errors,
        notes=notes,
        overview=overview,
        command_docs_health=command_docs_health,
        manifest_health=manifest_health,
        mirror_health=mirror_health,
        memory_health=memory_health,
        continuity_health=continuity_health,
        roots_health=roots_health,
        role_contract_health=role_contract_health,
        docs_health=docs_health,
        wrote_report=write_report,
        drift_report_path=report_path,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize the v2 scaffold",
        description=(
            "Initialize the repo-owned v2 scaffold in the target directory without "
            "deleting preserved legacy `.ai/` state."
        ),
    )
    init_parser.add_argument("--path", help="Target repo path; defaults to the current directory")
    init_parser.add_argument("--dry-run", action="store_true")
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--skip-sync", action="store_true")
    init_parser.add_argument(
        "--adopt-manual",
        action="store_true",
        help=(
            "Preserve existing manual AGENTS.md and .specify/* files while creating missing "
            "workflow metadata, managed role pointer, generated shims, and mirror lock."
        ),
    )

    sync_parser = subparsers.add_parser(
        "sync",
        help="Generate checksum-locked tool shims from AGENTS.md",
        description=(
            "Generate checksum-locked tool shims from the canonical `AGENTS.md` contract "
            "without silently overwriting managed drift."
        ),
    )
    sync_parser.add_argument("--path", help="Target repo path; defaults to the current directory")
    sync_parser.add_argument("--dry-run", action="store_true")
    sync_parser.add_argument("--force", action="store_true")

    status_parser = subparsers.add_parser(
        "status",
        help="Show a human-readable repo summary",
        description=(
            "Show the repo-owned v2 status view, including the health overview plus the "
            "detailed manifest, mirror-lock/shim, memory, continuity-state, roots, "
            "role-contract, and command/help/docs consistency sections."
        ),
    )
    status_parser.add_argument("--path", help="Target repo path; defaults to the current directory")
    status_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Validate the v2 scaffold",
        description=(
            "Validate the repo-owned v2 scaffold and health surfaces without auto-repair. "
            "Use `workflow sync` explicitly when mirror-lock/shim drift needs repair."
        ),
    )
    doctor_parser.add_argument("--path", help="Target repo path; defaults to the current directory")
    doctor_parser.add_argument("--write-report", action="store_true")
    doctor_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")

    roots_parser = subparsers.add_parser(
        "roots",
        help="Inspect workspace roots from repo-owned config",
        description=(
            "Inspect workspace roots from the repo-owned config at `.workflow/roots.json` "
            "and validate whether the configured default roots are safe to use."
        ),
    )
    roots_parser.add_argument("--format", choices=["text", "shell", "json"], default="text")
    roots_parser.add_argument("--validate", action="store_true")

    hermes_parser = subparsers.add_parser(
        "hermes",
        help="Run Hermes inventory, preflight, analysis, preview, and the explicit no-content connectivity gate",
        description=(
            "Run deterministic read-only dry-run inventory, preflight, bounded analysis, and offline "
            "Qwen request/prompt preview, or the explicit operator-gated no-content DashScope "
            "connectivity probe. Live response parsing, migration writes, report writing, "
            "Qwen/DashScope analysis, and Graphify remain deferred."
        ),
    )
    hermes_subparsers = hermes_parser.add_subparsers(dest="hermes_command", required=True)
    hermes_inventory_parser = hermes_subparsers.add_parser(
        "inventory",
        help="Classify repos across configured roots without writing",
        description=(
            "Classify direct child repos across the repo-owned roots config in a deterministic, "
            "read-only dry-run. This first Hermes slice does not migrate, patch, or write reports "
            "into target repos."
        ),
    )
    hermes_inventory_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required for the first Hermes slice; no writes are performed.",
    )
    hermes_inventory_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    hermes_preflight_parser = hermes_subparsers.add_parser(
        "preflight",
        help="Evaluate shallow Hermes readiness facts without writing",
        description=(
            "Evaluate shallow deterministic preflight facts across configured roots. This surface is "
            "read-only, dry-run only, reads no target repo file bodies, writes no reports, and does "
            "not invoke Qwen/DashScope analysis or Graphify."
        ),
    )
    hermes_preflight_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required for Hermes preflight; no writes are performed.",
    )
    hermes_preflight_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    hermes_analysis_parser = hermes_subparsers.add_parser(
        "analyze",
        help="Summarize deterministic preflight facts without writing",
        description=(
            "Summarize deterministic in-memory Hermes preflight facts across configured roots. This "
            "bounded analysis is read-only, dry-run only, does not build Qwen request shapes, prompts, "
            "responses, or parsed outputs, and does not invoke DashScope, Graphify, connectivity, "
            "report writing, migration writes, target repo writes, or target repo file body reads."
        ),
    )
    hermes_analysis_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required for Hermes analysis; no writes are performed.",
    )
    hermes_analysis_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    hermes_qwen_preview_parser = hermes_subparsers.add_parser(
        "qwen-preview",
        help="Preview the offline Qwen request/prompt contract without writing",
        description=(
            "Preview a bounded, redacted future Qwen/DashScope request and prompt from deterministic "
            "Hermes analysis summary metadata. This surface is dry-run only, local-only, excludes root "
            "and project paths from the preview, reads no target repo file bodies beyond the existing "
            "analysis source facts, does not invoke connectivity, and does not execute prompts, parse "
            "responses, write reports, run Graphify, run migrations, or write target repos."
        ),
    )
    hermes_qwen_preview_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required for Hermes Qwen preview; no writes or network calls are performed.",
    )
    hermes_qwen_preview_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    hermes_connectivity_parser = hermes_subparsers.add_parser(
        "qwen-connectivity",
        help="Run the explicit operator-gated no-content DashScope connectivity probe",
        description=(
            "Run the explicit operator-gated no-content DashScope connectivity probe. Human-readable "
            "status remains the default, `--json` emits machine-readable status only, the command "
            "sends no project content, and it only becomes network-eligible when `--probe "
            "--no-content --yes-network` are all present in an interactive operator session."
        ),
    )
    hermes_connectivity_parser.add_argument(
        "--probe",
        action="store_true",
        help="Operator-intent flag; without it the command remains local-only.",
    )
    hermes_connectivity_parser.add_argument(
        "--no-content",
        action="store_true",
        help="Required no-content guard for the governed GET/no-body probe.",
    )
    hermes_connectivity_parser.add_argument(
        "--yes-network",
        action="store_true",
        help="Required network opt-in flag; non-interactive runs still remain local-only.",
    )
    hermes_connectivity_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON status instead of text.",
    )

    open_parser = subparsers.add_parser(
        "open",
        help="Resolve or create a project across configured roots",
        description=(
            "Resolve or create a project across repo-owned workspace roots. Use `--roots` "
            "only to override the repo-owned workspace roots for this command."
        ),
    )
    open_parser.add_argument("name", help="Project directory name")
    open_parser.add_argument(
        "--roots",
        action="append",
        default=[],
        help="Override the repo-owned workspace roots for this command (repeatable)",
    )
    open_parser.add_argument("--create", action="store_true", help="Create the project if it does not exist")
    open_parser.add_argument("--root", help="Creation root for a missing project")
    open_parser.add_argument("--force", action="store_true", help="Forwarded to `workflow init` during creation")
    open_parser.add_argument("--skip-sync", action="store_true", help="Forwarded to `workflow init` during creation")
    open_parser.add_argument("--format", choices=["text", "shell"], default="text")

    list_parser = subparsers.add_parser(
        "list",
        help="List projects across configured roots",
        description=(
            "List shallow project classifications across the repo-owned workspace roots. "
            "Use `--roots` only to override the repo-owned workspace roots for this command."
        ),
    )
    list_parser.add_argument(
        "--roots",
        action="append",
        default=[],
        help="Override the repo-owned workspace roots for this command (repeatable)",
    )

    close_parser = subparsers.add_parser(
        "close",
        help="Show close-out guidance for the current repo",
        description=(
            "Show close-out guidance for the current repo. For v2 repos the primary "
            "continuity targets live under `.specify/state/`, while `.ai/*` remains "
            "preserved legacy/coexistence state."
        ),
    )
    close_parser.add_argument("--path", help="Target repo path; defaults to the current directory")
    close_parser.add_argument("--format", choices=["text", "shell"], default="text")

    save_parser = subparsers.add_parser(
        "save",
        help="Append a session marker for the current repo",
        description=(
            "Append a session marker for the current repo. For v2 repos the primary log is "
            "`.specify/state/session.log.md`, with legacy `.ai/logs/session.log` used only "
            "for coexistence when present."
        ),
    )
    save_parser.add_argument("--path", help="Target repo path; defaults to the current directory")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return ensure_init(
                ensure_repo_target(args.path),
                dry_run=args.dry_run,
                force=args.force,
                skip_sync=args.skip_sync,
                adopt_manual=args.adopt_manual,
            )
        if args.command == "sync":
            return sync(ensure_repo_target(args.path), dry_run=args.dry_run, force=args.force)
        if args.command == "status":
            return print_status(ensure_repo_target(args.path), as_json=args.json)
        if args.command == "doctor":
            repo = ensure_repo_target(args.path)
            result = doctor(repo, write_report=args.write_report)
            if args.json:
                print(render_json_output(doctor_result_payload(result)), end="")
                return 0 if result.passed else 1
            print(f"workflow doctor :: repo={repo}")
            for note in result.notes:
                print(f"- {note}")
            if result.errors:
                print("FAIL")
                for error in result.errors:
                    print(f"- {error}")
                return 1
            print("PASS")
            return 0
        if args.command == "roots":
            return roots_command(args.format, validate=args.validate)
        if args.command == "hermes":
            if args.hermes_command == "inventory":
                return hermes_inventory_command(dry_run=args.dry_run, as_json=args.json)
            if args.hermes_command == "preflight":
                return hermes_preflight_command(dry_run=args.dry_run, as_json=args.json)
            if args.hermes_command == "analyze":
                return hermes_analysis_command(dry_run=args.dry_run, as_json=args.json)
            if args.hermes_command == "qwen-preview":
                return hermes_qwen_preview_command(dry_run=args.dry_run, as_json=args.json)
            if args.hermes_command == "qwen-connectivity":
                return hermes_qwen_connectivity_command(
                    probe=args.probe,
                    no_content=args.no_content,
                    yes_network=args.yes_network,
                    as_json=args.json,
                )
        if args.command == "open":
            roots = [Path(root) for root in args.roots]
            create_root = Path(args.root) if args.root else None
            return open_project(
                args.name,
                roots,
                create=args.create,
                create_root=create_root,
                force=args.force,
                skip_sync=args.skip_sync,
                format_name=args.format,
            )
        if args.command == "list":
            return list_projects([Path(root) for root in args.roots])
        if args.command == "close":
            return close_project(ensure_repo_target(args.path), args.format)
        if args.command == "save":
            return save_project(ensure_repo_target(args.path))
    except WorkflowError as exc:
        if args.command == "status" and getattr(args, "json", False):
            repo_path = str(Path(args.path).expanduser().resolve()) if args.path else str(Path.cwd().resolve())
            print(render_json_output(build_workflow_error_payload("status", str(exc), repo_path=repo_path)), end="")
            return 1
        if args.command == "doctor" and getattr(args, "json", False):
            repo_path = str(Path(args.path).expanduser().resolve()) if args.path else str(Path.cwd().resolve())
            print(render_json_output(build_workflow_error_payload("doctor", str(exc), repo_path=repo_path)), end="")
            return 1
        if args.command == "roots" and getattr(args, "format", None) == "json":
            print(render_json_output(build_workflow_error_payload("roots", str(exc), repo_path=str(workflow_manager_home()))), end="")
            return 1
        if (
            args.command == "hermes"
            and getattr(args, "hermes_command", None) == "qwen-connectivity"
            and getattr(args, "json", False)
        ):
            print(
                render_json_output(
                    {
                        "schema_version": DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION,
                        "command": "hermes_qwen_connectivity",
                        "mode": DASHSCOPE_CONNECTIVITY_MODE,
                        "intended_model": DASHSCOPE_INTENDED_MODEL,
                        "selected_model": DASHSCOPE_INTENDED_MODEL,
                        "selected_api_key_name": None,
                        "selected_api_key_category": None,
                        "local_config_ready": False,
                        "model_policy_status": "error",
                        "probe_requested": bool(getattr(args, "probe", False)),
                        "no_content": bool(getattr(args, "no_content", False)),
                        "yes_network": bool(getattr(args, "yes_network", False)),
                        "interactive_required": True,
                        "interactive_session": False,
                        "operator_gate_satisfied": False,
                        "network_attempted": False,
                        "connectivity_status": "not-requested",
                        "sanitized_error_category": "none",
                        "http_status_category": "not-attempted",
                        "request_method": DASHSCOPE_CONNECTIVITY_REQUEST_METHOD,
                        "request_body_kind": DASHSCOPE_CONNECTIVITY_REQUEST_BODY_KIND,
                        "request_body_bytes_length": 0,
                        "project_content_sent": False,
                        "inventory_content_sent": False,
                        "prompt_preview_content_sent": False,
                        "target_repo_content_sent": False,
                        "qwen_analysis_enabled": False,
                        "report_writing_enabled": False,
                        "migration_writes_enabled": False,
                        "graphify_enabled": False,
                        "health_surface_integration_enabled": False,
                        "warnings": [],
                        "errors": [str(exc)],
                    }
                ),
                end="",
            )
            return 1
        print(f"workflow error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
