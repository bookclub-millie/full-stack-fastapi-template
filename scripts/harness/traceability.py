"""Check that OpenSpec changes and the evaluation docs stay linked by ID.

Failures block the PR (harness/checks); notes only show in the gate comment.
See docs/adr/001-openspec-docs-traceability.md, section 4.
"""

from __future__ import annotations

import re
from collections.abc import Callable

import tcnames
from doctables import cell, filled, table

from openspec import Change

PRD = "docs/prd.md"
E2E = "docs/e2e-test.md"
DEV = "docs/development.md"
EXPERIENCE = "docs/experience.md"
SECURITY = "docs/security-compliance.md"

SHA40 = re.compile(r"\b[0-9a-f]{40}\b")
MIN_DEVELOPMENT_CELLS = 4
MANUAL = "수동"


def is_done(status: str) -> bool:
    return "완료" in status and "미완료" not in status


def _ids(kind: str, text: str) -> list[str]:
    """REQ or AC ids in text, normalized like TC ids (AC-7 == AC-07)."""
    return [
        f"{kind}-{int(n):02d}" for n in re.findall(rf"\b{kind}-(\d{{1,6}})\b", text)
    ]


def _norm(identifier: str) -> str:
    found = _ids(identifier.split("-")[0], identifier)
    return found[0] if found else identifier


def _manual_tcs(scenarios: list[dict[str, str]]) -> set[str]:
    """TCs whose 종류 is exactly 수동: they have no collected result."""
    return {
        tc
        for row in scenarios
        if cell(row, "종류").strip() == MANUAL
        for tc in tcnames.ids(cell(row, "TC"))
    }


def unsupported_completions(
    docs: dict[str, str | None], sha_exists: Callable[[str], bool] | None = None
) -> list[str]:
    """REQ rows marked 완료 whose TCs have no latest PASS result with a real full SHA.

    Rows of the 실행 결과 table are taken in order, so a later FAIL for a TC
    replaces an earlier PASS. With sha_exists, the SHA must name a commit.
    수동 TCs never count: collect_evidence cannot produce a result for them.
    """
    scenarios = table(docs.get(E2E), "테스트 시나리오")
    manual = _manual_tcs(scenarios)
    latest: dict[str, dict[str, str]] = {}
    for row in table(docs.get(E2E), "실행 결과"):
        for tc in tcnames.ids(cell(row, "TC")):
            latest[tc] = row
    passed = set()
    for tc, row in latest.items():
        sha = SHA40.search(cell(row, "소스 SHA"))
        if (
            "PASS" in cell(row, "상태").upper()
            and sha
            and (sha_exists is None or sha_exists(sha.group()))
            and tc not in manual
        ):
            passed.add(tc)
    problems = []
    for row in table(docs.get(PRD), "요구사항 추적표"):
        if not is_done(cell(row, "상태")):
            continue
        for req in _ids("REQ", cell(row, "REQ")):
            keys = {req, *_ids("AC", cell(row, "AC"))}
            tcs = set(tcnames.ids(cell(row, "TC")))
            for scenario in scenarios:
                if keys & set(
                    _ids("REQ", cell(scenario, "REQ"))
                    + _ids("AC", cell(scenario, "REQ"))
                ):
                    tcs.update(tcnames.ids(cell(scenario, "TC")))
            if not tcs & passed:
                checked = ", ".join(sorted(tcs)) or "없음"
                if tcs & manual:
                    checked += f"; 수동 TC {', '.join(sorted(tcs & manual))}는 근거로 세지 않음"
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
    prd_acs = set(_ids("AC", prd_text))
    prd_reqs = {
        req
        for row in table(prd_text, "요구사항 추적표")
        for req in _ids("REQ", cell(row, "REQ"))
    }
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
            if _norm(req) not in prd_reqs:
                note(
                    "OpenSpec의 REQ가 docs/prd.md 추적표에 없음", f"{change.id}: {req}"
                )
        acs = [s.id for s in change.scenarios if s.id]
        for ac in acs:
            if _norm(ac) not in prd_acs:
                note("OpenSpec의 AC가 docs/prd.md에 없음", f"{change.id}: {ac}")
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


def check_tests(
    docs: dict[str, str | None],
    tests: dict[str, str],
    changes: list[Change],
    *,
    archived: set[str],
    changed: set[str],
) -> tuple[list[str], dict[str, list[str]]]:
    """TC ids in test names ↔ e2e-test.md 테스트 시나리오. Returns (failures, notes).

    tests: test file path → text. archived: change ids this PR archives.
    changed: paths this PR adds or edits.
    """
    failures: list[str] = []
    notes: dict[str, list[str]] = {}

    def note(title: str, item: str) -> None:
        notes.setdefault(title, []).append(item)

    scenarios = table(docs.get(E2E), "테스트 시나리오")
    in_scenarios = {tc for row in scenarios for tc in tcnames.ids(cell(row, "TC"))}
    manual = _manual_tcs(scenarios)
    rows_by_ac: dict[str, list[dict[str, str]]] = {}
    for row in scenarios:
        for ac in set(_ids("AC", cell(row, "REQ"))):
            rows_by_ac.setdefault(ac, []).append(row)
    e2e_changed = E2E in changed

    tagged: dict[str, list[tcnames.TaggedTest]] = {}
    for path in sorted(tests):
        found, problems = tcnames.scan(path, tests[path])
        for problem in problems:
            item = f"{problem.path}:{problem.line} `{problem.name}`: {problem.reason}"
            if path in changed:
                failures.append(item)
            else:
                note("테스트 이름의 TC 표기 (이번 PR에서 바뀌지 않음)", item)
        for test in found:
            tagged.setdefault(test.tc, []).append(test)
            if test.tc in in_scenarios:
                continue
            item = (
                f"{test.path}:{test.line} {test.tc}: {E2E} 테스트 시나리오에 {test.tc} 행이 없습니다. "
                "테스트와 같은 커밋에 행을 추가하세요"
            )
            if path in changed or e2e_changed:
                failures.append(item)
            else:
                note("시나리오에 없는 TC 테스트 (이번 PR에서 바뀌지 않음)", item)
    running = {tc for tc, found in tagged.items() if any(t.runs for t in found)}

    def gap(change: Change, problem: str) -> None:
        # Archiving closes the Issue as completed, so the PR that archives must link
        # every AC to a TC and a running test. For older archives this is only a note.
        if change.id in archived:
            failures.append(problem)
        else:
            note("archive된 변경의 AC ↔ TC ↔ 테스트 누락", problem)

    for change in changes:
        if not change.archived:
            continue
        unnamed = sum(1 for s in change.scenarios if not s.id)
        if unnamed:
            gap(
                change,
                f"{change.id}: AC ID가 없는 Scenario {unnamed}개는 TC와 이을 수 없습니다 "
                "(`#### Scenario: AC-xx <이름>`)",
            )
        for scenario in change.scenarios:
            if not scenario.id:
                continue
            ac = _norm(scenario.id)
            rows = rows_by_ac.get(ac, [])
            automated = [
                tc
                for r in rows
                if cell(r, "종류").strip() != MANUAL
                for tc in tcnames.ids(cell(r, "TC"))
            ]
            missing = [tc for tc in automated if tc not in running]
            if not rows:
                problem = f"{E2E}: {change.id}의 {ac}를 확인하는 테스트 시나리오(TC) 행이 없습니다"
            elif missing:
                skipped = [tc for tc in missing if tc in tagged]
                problem = (
                    f"{change.id}의 {ac}: {', '.join(missing)}를 확인하는 실행되는 테스트가 없습니다 "
                    f"({tcnames.pytest_form(missing[0])} 또는 {tcnames.title_form(missing[0])}, "
                    f"위치: {tcnames.LOCATIONS})"
                    + (
                        f". 건너뛰는 테스트만 있음: {', '.join(skipped)}"
                        if skipped
                        else ""
                    )
                )
            else:
                if not automated:
                    note(
                        "수동 TC만 있는 AC (결과가 수집되지 않아 미검증으로 남음)",
                        f"{change.id}: {ac}",
                    )
                continue
            gap(change, problem)
        for tc, path in change.test_tasks:
            places = sorted({t.path for t in tagged.get(tc, [])})
            if path in places:
                continue
            gap(
                change,
                f"{change.id}의 tasks.md: {path}에서 {tc} 이름의 테스트를 찾지 못했습니다"
                + (
                    f" (있는 곳: {', '.join(places)}). 테스트를 옮기거나 tasks.md 경로를 고치세요"
                    if places
                    else f". 위치({tcnames.LOCATIONS})와 이름({tcnames.pytest_form(tc)}, {tcnames.title_form(tc)})을 확인하세요"
                ),
            )

    if e2e_changed or archived or any(path in changed for path in tests):
        for tc in sorted(in_scenarios - manual - set(tagged)):
            note(
                "테스트가 없는 TC 시나리오 (구현 전이면 정상, 결과가 수집되지 않음)", tc
            )
    return failures, notes
