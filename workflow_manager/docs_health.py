from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


DOCS_HEALTH_SCHEMA_VERSION = "1.0.0"
DOCS_HEALTH_STATUS_VALUES = ("pass", "warning", "fail")
DOCS_HEALTH_DEFAULT_BUDGETS = {
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
DOCS_HEALTH_REQUIRED_AGENTS_KEY_FILES = (
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
DOCS_HEALTH_ALLOWED_DUPLICATE_HEADINGS = {
    "manual live no-content connectivity probe runbook",
}


@dataclass(frozen=True)
class DocsHealthIssue:
    level: str
    message: str


@dataclass(frozen=True)
class DocsHealthEntry:
    relative_path: str
    status: str
    line_count: int
    budget: int
    summary: str


@dataclass(frozen=True)
class DocsHealth:
    repo: Path
    status: str
    summary: str
    entries: list[DocsHealthEntry] = field(default_factory=list)
    issues: list[DocsHealthIssue] = field(default_factory=list)

    @property
    def warnings(self) -> list[DocsHealthIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    @property
    def failures(self) -> list[DocsHealthIssue]:
        return [issue for issue in self.issues if issue.level == "error"]


def evaluate_docs_health(
    repo: Path,
    *,
    budgets: dict[str, int] | None = None,
) -> DocsHealth:
    active_budgets = dict(DOCS_HEALTH_DEFAULT_BUDGETS)
    if budgets:
        active_budgets.update(budgets)

    entries: list[DocsHealthEntry] = []
    issues: list[DocsHealthIssue] = []
    texts: dict[str, str] = {}

    for relative_path, budget in active_budgets.items():
        path = repo / relative_path
        if not path.exists():
            if relative_path != "AGENTS.md":
                continue
            entries.append(
                DocsHealthEntry(
                    relative_path=relative_path,
                    status="fail",
                    line_count=0,
                    budget=budget,
                    summary=f"`{relative_path}` is missing.",
                )
            )
            issues.append(DocsHealthIssue("error", f"Missing governed doc `{relative_path}`."))
            continue
        text = path.read_text(encoding="utf-8")
        texts[relative_path] = text
        line_count = len(text.splitlines())
        if line_count > budget:
            status = "fail"
            summary = f"`{relative_path}` has {line_count} lines, over budget {budget}."
            issues.append(DocsHealthIssue("error", summary))
        else:
            status = "pass"
            summary = f"`{relative_path}` is within budget ({line_count}/{budget} lines)."
        entries.append(
            DocsHealthEntry(
                relative_path=relative_path,
                status=status,
                line_count=line_count,
                budget=budget,
                summary=summary,
            )
        )

    _check_agents_key_files(repo, texts.get("AGENTS.md", ""), issues)
    _check_milestone_test_references(repo, texts.get("MILESTONES.md", ""), issues)
    _check_gemini_adapter_claims(texts, issues)
    if (repo / "workflow_manager/cli.py").exists():
        _check_role_contract_doc_alignment(texts.get("ROLES.md", ""), issues)
    _check_duplicate_headings(texts, issues)

    failure_count = sum(1 for issue in issues if issue.level == "error")
    warning_count = sum(1 for issue in issues if issue.level == "warning")
    if failure_count:
        status = "fail"
        summary = f"{failure_count} documentation health issue(s) require repair."
        if warning_count:
            summary += f" {warning_count} additional warning(s) need review."
    elif warning_count:
        status = "warning"
        summary = f"{warning_count} documentation health warning(s) need review."
    else:
        status = "pass"
        summary = f"All {len(entries)} governed documentation files are within budget and aligned."

    return DocsHealth(repo=repo, status=status, summary=summary, entries=entries, issues=issues)


def _check_agents_key_files(repo: Path, agents_text: str, issues: list[DocsHealthIssue]) -> None:
    if not agents_text:
        return
    if (repo / "workflow_manager/cli.py").exists():
        for relative_path in DOCS_HEALTH_REQUIRED_AGENTS_KEY_FILES:
            if f"`{relative_path}`" not in agents_text:
                issues.append(DocsHealthIssue("error", f"`AGENTS.md` Key files must list `{relative_path}`."))
            if not (repo / relative_path).exists():
                issues.append(DocsHealthIssue("error", f"`AGENTS.md` Key files entry `{relative_path}` does not exist."))

    key_files_block = _extract_heading_block(agents_text, "Key files")
    for token in re.findall(r"`([^`]+)`", key_files_block):
        if token.endswith("/*") or token.startswith("workflow ") or token.startswith("--"):
            continue
        if token.startswith("~/"):
            path = Path.home() / token[2:]
        elif token.startswith("/"):
            path = Path(token)
        else:
            path = repo / token
        if not path.exists() and not any(char in token for char in "*{}"):
            issues.append(DocsHealthIssue("error", f"`AGENTS.md` Key files entry `{token}` does not exist."))


def _check_milestone_test_references(repo: Path, milestones_text: str, issues: list[DocsHealthIssue]) -> None:
    if not milestones_text:
        return
    governed_text = milestones_text.split("\n## M1.11", 1)[0]
    for token in sorted(set(re.findall(r"`(tests/[a-zA-Z0-9_./-]+\.py)`", governed_text))):
        if not (repo / token).exists():
            issues.append(DocsHealthIssue("error", f"`MILESTONES.md` references missing test file `{token}`."))


def _check_role_contract_doc_alignment(roles_text: str, issues: list[DocsHealthIssue]) -> None:
    if not roles_text:
        return
    required = (
        "Architect → Product",
        "Coder → Code",
        "Verifier → Reliability",
        "Claude Code CLI",
        "OpenCode",
        "Factory Droid",
        "Codex CLI",
        "Gemini CLI",
        "Antigravity IDE",
        "Cursor",
    )
    for snippet in required:
        if snippet not in roles_text:
            issues.append(DocsHealthIssue("error", f"`ROLES.md` is missing role-contract mapping snippet `{snippet}`."))
    forbidden_gemini_role_paths = (
        ".gemini/agents/architect.md",
        ".gemini/agents/coder.md",
        ".gemini/agents/verifier.md",
    )
    for snippet in forbidden_gemini_role_paths:
        if snippet in roles_text:
            issues.append(
                DocsHealthIssue(
                    "error",
                    f"`ROLES.md` must not claim premature Gemini role adapter path `{snippet}`.",
                )
            )


def _check_gemini_adapter_claims(texts: dict[str, str], issues: list[DocsHealthIssue]) -> None:
    stale_single_adapter_claims = (
        "only managed Gemini subagent adapter",
        "only managed Gemini adapter",
        "only declared managed Gemini",
    )
    premature_role_adapter_claims = (
        ".gemini/agents/architect.md",
        ".gemini/agents/coder.md",
        ".gemini/agents/verifier.md",
    )
    for relative_path, text in texts.items():
        for snippet in stale_single_adapter_claims:
            if snippet in text:
                issues.append(
                    DocsHealthIssue(
                        "error",
                        f"`{relative_path}` has stale Gemini adapter ownership claim `{snippet}`.",
                    )
                )
        for snippet in premature_role_adapter_claims:
            if snippet in text:
                issues.append(
                    DocsHealthIssue(
                        "error",
                        f"`{relative_path}` claims premature Gemini role adapter path `{snippet}`.",
                    )
                )


def _check_duplicate_headings(texts: dict[str, str], issues: list[DocsHealthIssue]) -> None:
    headings: dict[str, list[str]] = {}
    for relative_path, text in texts.items():
        if relative_path.startswith(".specify/"):
            continue
        for heading in re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE):
            normalized = _normalize_heading(heading)
            if normalized in DOCS_HEALTH_ALLOWED_DUPLICATE_HEADINGS:
                continue
            headings.setdefault(normalized, []).append(relative_path)

    for heading, paths in sorted(headings.items()):
        unique_paths = sorted(set(paths))
        if len(unique_paths) > 1:
            issues.append(
                DocsHealthIssue(
                    "warning",
                    f"Heading `{heading}` appears in multiple top-level docs: {', '.join(unique_paths)}.",
                )
            )


def _extract_heading_block(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", flags=re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end]


def _normalize_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", heading.strip().lower())
