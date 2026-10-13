"""Check that OpenSpec changes and the evaluation docs stay linked by ID.

Failures block the PR (harness/checks); notes only show in the gate comment.
See docs/adr/001-openspec-docs-traceability.md, section 4.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from doctables import cell, filled, table

from openspec import Change

PRD = "docs/prd.md"
E2E = "docs/e2e-test.md"
DEV = "docs/development.md"
EXPERIENCE = "docs/experience.md"
SECURITY = "docs/security-compliance.md"

SHA40 = re.compile(r"\b[0-9a-f]{40}\b")
REQ = re.compile(r"\bREQ-\d+\b")
AC = re.compile(r"\bAC-\d+\b")
TC = re.compile(r"\bTC-\d+\b")
MIN_DEVELOPMENT_CELLS = 4


def is_done(status: str) -> bool:
    return "완료" in status and "미완료" not in status


def unsupported_completions(
    docs: dict[str, str | None], sha_exists: Callable[[str], bool] | None = None
) -> list[str]:
    """REQ rows marked 완료 whose TCs have no latest PASS result with a real full SHA.

    Rows of the 실행 결과 table are taken in order, so a later FAIL for a TC
    replaces an earlier PASS. With sha_exists, the SHA must name a commit.
    """
    scenarios = table(docs.get(E2E), "테스트 시나리오")
    latest: dict[str, dict[str, str]] = {}
    for row in table(docs.get(E2E), "실행 결과"):
        for tc in TC.findall(cell(row, "TC")):
            latest[tc] = row
    passed = set()
    for tc, row in latest.items():
        sha = SHA40.search(cell(row, "소스 SHA"))
        if (
            "PASS" in cell(row, "상태").upper()
            and sha
            and (sha_exists is None or sha_exists(sha.group()))
        ):
            passed.add(tc)
    problems = []
    for row in table(docs.get(PRD), "요구사항 추적표"):
        if not is_done(cell(row, "상태")):
            continue
        for req in REQ.findall(cell(row, "REQ")):
            keys = {req, *AC.findall(cell(row, "AC"))}
            tcs = set(TC.findall(cell(row, "TC")))
            for scenario in scenarios:
                if keys & set(
                    REQ.findall(cell(scenario, "REQ"))
                    + AC.findall(cell(scenario, "REQ"))
                ):
                    tcs.update(TC.findall(cell(scenario, "TC")))
            if not tcs & passed:
                checked = ", ".join(sorted(tcs)) or "없음"
                problems.append(
                    f"{PRD}: {req}이 완료인데 e2e-test.md 실행 결과에서 최신 결과가 PASS이고 실제 커밋 SHA(40자)가 있는 TC가 없습니다 "
                    f"(확인한 TC: {checked})"
                )
    return problems


def check(
    docs: dict[str, str | None],
    changes: list[Change],
    *,
    archived: set[str],
    touched: set[str],
    claims_changed: bool,
    sha_exists: Callable[[str], bool] | None = None,
) -> tuple[list[str], dict[str, list[str]]]:
    """Return (failures, notes).

    archived: change ids this PR archives. touched: change ids this PR edits.
    claims_changed: whether this PR edits prd.md or e2e-test.md.
    """
    failures: list[str] = []
    notes: dict[str, list[str]] = {}

    def note(title: str, item: str) -> None:
        notes.setdefault(title, []).append(item)

    development = table(docs.get(DEV), "AI 활용과 검증")
    for change_id in sorted(archived):
        mention = re.compile(rf"(?<![\w-]){re.escape(change_id)}(?![\w-])")
        rows = [r for r in development if any(mention.search(v) for v in r.values())]
        if not any(filled(r) >= MIN_DEVELOPMENT_CELLS for r in rows):
            failures.append(
                f"{DEV}: archive한 변경 {change_id}의 'AI 활용과 검증' 행이 없거나 비어 있습니다 "
                f"(Issue 칸에 `#번호 ({change_id})`, {MIN_DEVELOPMENT_CELLS}칸 이상)"
            )

    for problem in unsupported_completions(docs, sha_exists):
        if claims_changed:
            failures.append(problem)
        else:
            note("근거 없는 완료 (이번 PR에서 바뀌지 않음)", problem)

    prd_text = docs.get(PRD) or ""
    prd_reqs = {
        req
        for row in table(prd_text, "요구사항 추적표")
        for req in REQ.findall(cell(row, "REQ"))
    }
    scenario_keys = " ".join(
        cell(r, "REQ") for r in table(docs.get(E2E), "테스트 시나리오")
    )
    for change in changes:
        if change.id not in touched:
            continue
        reqs = sorted(
            {
                *change.proposal.requirements,
                *(r.id for r in change.requirements if r.id),
            }
        )
        for req in reqs:
            if req not in prd_reqs:
                note(
                    "OpenSpec의 REQ가 docs/prd.md 추적표에 없음", f"{change.id}: {req}"
                )
        acs = [s.id for s in change.scenarios if s.id]
        for ac in acs:
            if not re.search(rf"\b{ac}\b", prd_text):
                note("OpenSpec의 AC가 docs/prd.md에 없음", f"{change.id}: {ac}")
        if change.archived:
            for ac in acs:
                if not re.search(rf"\b{ac}\b", scenario_keys):
                    note(
                        "archive된 변경의 AC에 e2e-test.md 테스트 시나리오가 없음",
                        f"{change.id}: {ac}",
                    )
        for link in sorted({link for s in change.scenarios for link in s.links}):
            doc = (
                EXPERIENCE
                if link.startswith("FLOW")
                else SECURITY
                if link.startswith("SEC")
                else E2E
            )
            if not re.search(rf"\b{link}\b", docs.get(doc) or ""):
                note("시나리오의 연결 ID가 문서에 없음", f"{change.id}: {link} → {doc}")
        missing = [
            name
            for name, value in (
                ("요구사항", change.proposal.requirements),
                ("담당", change.proposal.owner),
            )
            if not value
        ]
        if missing:
            note(
                "proposal에 요구사항·담당 줄이 없음",
                f"{change.id}: {', '.join(missing)}",
            )
        unnamed = sum(1 for r in change.requirements if not r.id) + sum(
            1 for s in change.scenarios if not s.id
        )
        if unnamed:
            note("REQ·AC ID가 없는 Requirement·Scenario", f"{change.id}: {unnamed}개")
    return failures, notes
