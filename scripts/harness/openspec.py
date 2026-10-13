"""Read OpenSpec changes (proposal, delta specs, tasks) as plain data.

The ID conventions (REQ-xx, AC-xx, FLOW-xx, SEC-xx) come from
openspec/config.yaml; see docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import tcnames

CHANGES_DIR = "openspec/changes"
SPECS_DIR = "openspec/specs"
ARCHIVE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
GENERIC_TITLES = {"proposal", "제안", "제안서"}

REQ_ID = re.compile(r"\bREQ-\d+\b")
LINK_ID = re.compile(r"\b(?:FLOW|SEC|TC)-\d+\b")
LEADING_ID = re.compile(r"^((?:REQ|AC)-\d+)\s*[:.\-–—]?\s*")
DELTA_SECTION = re.compile(
    r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+Requirements", re.IGNORECASE
)
TASK_ITEM = re.compile(r"^\s*-\s*\[([ xX])\]")
# A test-writing task names its file: `- [ ] 2.3 TC-07 (AC-07) backend/tests/x/test_y.py::test_tc_07_...`
TASK_TEST_PATH = re.compile(r"([\w./-]+\.(?:py|[cm]?[jt]sx?))::")


@dataclass
class Proposal:
    title: str | None
    requirements: list[str]
    owner: str | None
    scope: str | None
    why: str


@dataclass
class Scenario:
    id: str | None
    name: str
    links: list[str] = field(default_factory=list)


@dataclass
class Requirement:
    id: str | None
    name: str
    scenarios: list[Scenario] = field(default_factory=list)
    added: bool = True  # False under "## MODIFIED Requirements"


@dataclass
class Change:
    id: str
    path: str  # repository-relative
    archived: bool
    proposal: Proposal
    requirements: list[Requirement]
    tasks: tuple[int, int]  # (done, total)
    test_tasks: list[tuple[str, str]] = field(default_factory=list)  # (TC id, file)

    @property
    def scenarios(self) -> list[Scenario]:
        return [s for r in self.requirements for s in r.scenarios]


def _split_id(text: str) -> tuple[str | None, str]:
    match = LEADING_ID.match(text.strip())
    if not match:
        return None, text.strip()
    return match.group(1), text.strip()[match.end() :].strip()


def _section(text: str, heading: str) -> str:
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside:
            lines.append(line)
    return "\n".join(lines).strip()


def parse_proposal(text: str) -> Proposal:
    title = None
    for line in text.splitlines():
        if line.startswith("# "):
            candidate = line[2:].strip()
            title = None if candidate.lower() in GENERIC_TITLES else candidate
            break

    def meta(key: str) -> str | None:
        match = re.search(rf"^\s*{key}\s*[:：]\s*(.+?)\s*$", text, re.MULTILINE)
        return match.group(1) if match else None

    owner = meta("담당")
    owner_match = re.match(r"@?([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)", owner or "")
    return Proposal(
        title=title,
        requirements=REQ_ID.findall(meta("요구사항") or ""),
        owner=owner_match.group(1) if owner_match else None,
        scope=meta("범위"),
        why=_section(text, "Why"),
    )


def parse_spec(text: str) -> list[Requirement]:
    """Requirements and scenarios from ADDED/MODIFIED delta sections."""
    requirements: list[Requirement] = []
    operation = "ADDED"
    for line in text.splitlines():
        if section := DELTA_SECTION.match(line):
            operation = section.group(1).upper()
            continue
        if operation not in ("ADDED", "MODIFIED"):
            continue
        if line.startswith("### Requirement:"):
            req_id, name = _split_id(line.split(":", 1)[1])
            requirements.append(Requirement(req_id, name, added=operation == "ADDED"))
        elif line.startswith("#### Scenario:") and requirements:
            ac_id, name = _split_id(line.split(":", 1)[1])
            requirements[-1].scenarios.append(Scenario(ac_id, name))
        elif "연결" in line and requirements and requirements[-1].scenarios:
            requirements[-1].scenarios[-1].links.extend(LINK_ID.findall(line))
    return requirements


def parse_tasks(text: str | None) -> tuple[int, int]:
    marks = [
        m.group(1) for line in (text or "").splitlines() if (m := TASK_ITEM.match(line))
    ]
    return sum(1 for mark in marks if mark in "xX"), len(marks)


def parse_test_tasks(text: str | None) -> list[tuple[str, str]]:
    """(TC id, test file) for each `<file>::<test name>` on a task line.

    The TC comes from the test name after `::`, so other TC ids on the line
    (for example the scenario row the task also adds) do not count.
    """
    found = []
    for line in (text or "").splitlines():
        if not TASK_ITEM.match(line):
            continue
        paths = list(TASK_TEST_PATH.finditer(line))
        for i, path in enumerate(paths):
            end = paths[i + 1].start() if i + 1 < len(paths) else len(line)
            name = line[path.end() : end]
            if tc := tcnames.pytest_tc(name) or tcnames.title_tc(name):
                found.append((tc, path.group(1)))
    return found


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def locate(path: str) -> tuple[str, str, bool] | None:
    """(change directory, change id, archived) for a file inside openspec/changes."""
    prefix = f"{CHANGES_DIR}/"
    if not path.startswith(prefix):
        return None
    parts = path[len(prefix) :].split("/")
    if parts[0] == "archive":
        if len(parts) < 3:
            return None
        return f"{prefix}archive/{parts[1]}", ARCHIVE_PREFIX.sub("", parts[1]), True
    if len(parts) < 2:
        return None
    return f"{prefix}{parts[0]}", parts[0], False


def changes_from_files(files: dict[str, str]) -> list[Change]:
    """Changes from repository-relative path -> text (only openspec/changes/** is used).

    Active changes come first, then archived ones; a change needs a proposal.md.
    """
    directories: dict[str, tuple[str, bool]] = {}
    for path in files:
        if found := locate(path):
            directory, change_id, archived = found
            directories[directory] = (change_id, archived)

    changes: list[Change] = []
    for directory, (change_id, archived) in sorted(
        directories.items(), key=lambda kv: (kv[1][1], kv[0])
    ):
        proposal = files.get(f"{directory}/proposal.md")
        if proposal is None:
            continue
        specs = sorted(
            p
            for p in files
            if p.startswith(f"{directory}/specs/") and p.endswith("/spec.md")
        )
        changes.append(
            Change(
                id=change_id,
                path=directory,
                archived=archived,
                proposal=parse_proposal(proposal),
                requirements=[r for spec in specs for r in parse_spec(files[spec])],
                tasks=parse_tasks(files.get(f"{directory}/tasks.md")),
                test_tasks=parse_test_tasks(files.get(f"{directory}/tasks.md")),
            )
        )
    return changes


def load_changes(root: Path) -> list[Change]:
    """Active and archived changes in a checkout."""
    base = root / CHANGES_DIR
    files: dict[str, str] = {}
    if base.is_dir():
        for path in base.rglob("*.md"):
            if (text := _read(path)) is not None:
                files[path.relative_to(root).as_posix()] = text
    return changes_from_files(files)
