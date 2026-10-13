"""REQ·AC·FLOW·TC numbers: who claims them, duplicates, and the next free one.

A number is claimed by the OpenSpec change that defines it: REQ/AC under ADDED
Requirements (or a new scenario under MODIFIED), TC in a tasks.md test line
(`TC-07 ... <file>::<test>`). The proposal PR is merged before implementation,
so its numbers are on the base branch from then on. The docs tables (prd.md,
e2e-test.md, experience.md) register the same ids later, one row per id.
Numbers are normalized like TC ids (AC-7 == AC-07). SEC ids follow the
organizer's policy and are not assigned here.
See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import re

from doctables import cell, table

from openspec import Change, Requirement

KINDS = ("REQ", "AC", "FLOW", "TC")
ID = re.compile(r"\b(REQ|AC|FLOW|TC)-(\d{1,6})\b")

PRD = "docs/prd.md"
E2E = "docs/e2e-test.md"
EXPERIENCE = "docs/experience.md"
# kind -> (document, section, column) of the table whose rows register the ids
REGISTRY = {
    "REQ": (PRD, "요구사항 추적표", "REQ"),
    "AC": (PRD, "요구사항 추적표", "AC"),
    "FLOW": (EXPERIENCE, "핵심 사용자 흐름", "FLOW"),
    "TC": (E2E, "테스트 시나리오", "TC"),
}
DOCS = (PRD, E2E, EXPERIENCE)
# An id that starts the cell or a list item ("AC-01 거부, AC-02 유지") is
# registered there; one mentioned in passing ("(AC-01 참고)") is not.
_LEADING = r"(?:^|[,;·/]|<br\s*/?>)\s*({kind}-\d{{1,6}})\b"


def norm(kind: str, number: str) -> str:
    return f"{kind}-{int(number):02d}"


def normalize(identifier: str) -> str:
    match = ID.fullmatch(identifier.strip())
    return norm(*match.groups()) if match else identifier


def ids_in(text: str | None, kinds: tuple[str, ...] = KINDS) -> set[str]:
    return {norm(k, n) for k, n in ID.findall(text or "") if k in kinds}


def _leading(kind: str, value: str) -> list[str]:
    found = re.findall(_LEADING.format(kind=kind), value)
    return sorted({normalize(i) for i in found})


def registered(docs: dict[str, str | None]) -> dict[str, list[list[str]]]:
    """kind -> ids registered by each row, in table order."""
    rows: dict[str, list[list[str]]] = {}
    for kind, (doc, section, column) in REGISTRY.items():
        rows[kind] = [
            _leading(kind, cell(row, column)) for row in table(docs.get(doc), section)
        ]
    return rows


def all_registered(docs: dict[str, str | None]) -> set[str]:
    return {i for rows in registered(docs).values() for row in rows for i in row}


def duplicates(docs: dict[str, str | None]) -> dict[str, str]:
    """id -> document for each id registered by more than one row."""
    found = {}
    for kind, rows in registered(docs).items():
        counts: dict[str, int] = {}
        for row in rows:
            for identifier in row:
                counts[identifier] = counts.get(identifier, 0) + 1
        for identifier, count in counts.items():
            if count > 1:
                found[identifier] = REGISTRY[kind][0]
    return found


def scenario_ids(requirements: list[Requirement]) -> dict[str, set[str]]:
    """REQ id -> its AC ids (from main specs or changes)."""
    acs: dict[str, set[str]] = {}
    for requirement in requirements:
        for req in ids_in(requirement.id, ("REQ",)):
            acs.setdefault(req, set()).update(
                ids_in(" ".join(s.id or "" for s in requirement.scenarios), ("AC",))
            )
    return acs


def claimed(change: Change, existing: dict[str, set[str]] | None = None) -> set[str]:
    """Ids a change claims: REQ/AC under ADDED Requirements and TCs of its test tasks.

    existing: REQ -> AC ids already on the base branch. When given, a scenario
    under MODIFIED Requirements that is not among them is a new claim too.
    """
    found: set[str] = set()
    for requirement in change.requirements:
        reqs = ids_in(requirement.id, ("REQ",))
        acs = ids_in(" ".join(s.id or "" for s in requirement.scenarios), ("AC",))
        if requirement.added:
            found |= reqs | acs
        elif existing is not None:
            known = set().union(*(existing.get(r, set()) for r in reqs))
            found |= acs - known
    found |= {tc for tc, _ in change.test_tasks}
    return found


def next_free(used: set[str]) -> dict[str, str]:
    """kind -> the number after the largest one in use."""
    result = {}
    for kind in KINDS:
        numbers = [int(i.split("-")[1]) for i in used if i.startswith(f"{kind}-")]
        result[kind] = norm(kind, str(max(numbers, default=0) + 1))
    return result
