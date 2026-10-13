"""Read OpenSpec changes (proposal, delta specs, tasks) as plain data.

The ID conventions (REQ-xx, AC-xx, FLOW-xx, SEC-xx) come from
openspec/config.yaml; see docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CHANGES_DIR = "openspec/changes"
ARCHIVE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
GENERIC_TITLES = {"proposal", "제안", "제안서"}

REQ_ID = re.compile(r"\bREQ-\d+\b")
LINK_ID = re.compile(r"\b(?:FLOW|SEC|TC)-\d+\b")
LEADING_ID = re.compile(r"^((?:REQ|AC)-\d+)\s*[:.\-–—]?\s*")
DELTA_SECTION = re.compile(
    r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+Requirements", re.IGNORECASE
)
TASK_ITEM = re.compile(r"^\s*-\s*\[([ xX])\]")


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


@dataclass
class Change:
    id: str
    path: str  # repository-relative
    archived: bool
    proposal: Proposal
    requirements: list[Requirement]
    tasks: tuple[int, int]  # (done, total)

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
    included = True
    for line in text.splitlines():
        if section := DELTA_SECTION.match(line):
            included = section.group(1).upper() in ("ADDED", "MODIFIED")
            continue
        if not included:
            continue
        if line.startswith("### Requirement:"):
            req_id, name = _split_id(line.split(":", 1)[1])
            requirements.append(Requirement(req_id, name))
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


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _load(root: Path, directory: Path, change_id: str, archived: bool) -> Change | None:
    proposal = _read(directory / "proposal.md")
    if proposal is None:
        return None
    requirements: list[Requirement] = []
    for spec in sorted((directory / "specs").rglob("spec.md")):
        requirements.extend(parse_spec(_read(spec) or ""))
    return Change(
        id=change_id,
        path=directory.relative_to(root).as_posix(),
        archived=archived,
        proposal=parse_proposal(proposal),
        requirements=requirements,
        tasks=parse_tasks(_read(directory / "tasks.md")),
    )


def load_changes(root: Path) -> list[Change]:
    """Active and archived changes that have a proposal.md."""
    base = root / CHANGES_DIR
    changes: list[Change] = []
    if not base.is_dir():
        return changes
    for directory in sorted(
        p for p in base.iterdir() if p.is_dir() and p.name != "archive"
    ):
        if change := _load(root, directory, directory.name, archived=False):
            changes.append(change)
    archive = base / "archive"
    if archive.is_dir():
        for directory in sorted(p for p in archive.iterdir() if p.is_dir()):
            if change := _load(
                root, directory, ARCHIVE_PREFIX.sub("", directory.name), archived=True
            ):
                changes.append(change)
    return changes
