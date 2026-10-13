import unittest

from doctables import filled, table
from traceability import check

from openspec import Change, Proposal, Requirement, Scenario

SHA = "a" * 40

PRD = """# 요구사항

## 요구사항 추적표

| REQ | 요구사항 | 우선순위 | AC·인수조건 | FLOW | Issue·코드 | TC | 상태 |
|---|---|---|---|---|---|---|---|
| REQ-01 | 할 일 등록 | 필수 | AC-01 거부, AC-02 유지 | FLOW-01 | #3 | TC-01 | 완료 |
| REQ-02 | 목록 | 필수 | AC-03 | | #4 | | 미완료 |
| REQ-03 | 공유 | 추가 | AC-04 | | | | 완료 |

## 변경 기록
"""

E2E = f"""# 시험

## 테스트 시나리오

| TC | REQ·AC·FLOW | 종류 | 사전 조건 | 입력·행동 | 예상 결과 | 실행 명령 |
|---|---|---|---|---|---|---|
| TC-01 | REQ-01 · AC-01 | E2E | | | | |
| TC-02 | AC-04 | 단위 | | | | |

## 실행 결과

| TC | 소스 SHA | 실행 시각·환경 | 실제 결과 | 상태 | 로그·화면 등 근거 경로 |
|---|---|---|---|---|---|
| TC-01 | {SHA} | 2026-10-14 CI | 통과 | PASS | run/1 |
| TC-02 | {SHA} | 2026-10-14 CI | 실패 | FAIL | run/1 |
"""

DEV = """# 개발 과정

## AI 활용과 검증

| Issue | 담당자 | AI 도구·사용 목적 | 변경 코드·활용 기록 | 검증·발견 문제 | 수정·재시험 근거 |
|---|---|---|---|---|---|
| #3 (add-todo) | gray | Claude Code 구현 | PR #7 | 경계값 누락 발견 | TC-01 재실행 |
| #9 (add-share) | gray | | | | |
"""


def change(
    change_id: str, *, archived: bool = False, reqs=("REQ-01",), owner="gray"
) -> Change:
    links = ["FLOW-01", "SEC-04"]
    return Change(
        id=change_id,
        path=f"openspec/changes/{change_id}",
        archived=archived,
        proposal=Proposal(
            title="t", requirements=list(reqs), owner=owner, scope="필수", why="w"
        ),
        requirements=[
            Requirement(
                "REQ-01",
                "등록",
                [
                    # Only add-todo links a flow and a security item.
                    Scenario("AC-01", "거부", links if change_id == "add-todo" else []),
                    Scenario("AC-09", "새 조건"),
                ],
            )
        ],
        tasks=(0, 0),
    )


class TableTest(unittest.TestCase):
    def test_reads_first_table_of_section(self) -> None:
        rows = table(PRD, "요구사항 추적표")
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["REQ"], "REQ-01")
        self.assertEqual(rows[1]["상태"], "미완료")
        self.assertEqual(filled(rows[1]), 6)

    def test_missing_section_or_text(self) -> None:
        self.assertEqual(table(PRD, "없는 섹션"), [])
        self.assertEqual(table(None, "요구사항 추적표"), [])

    def test_escaped_pipes_stay_in_cell(self) -> None:
        rows = table("## T\n\n| A | B |\n|---|---|\n| x \\| y | z |\n", "T")
        self.assertEqual(rows[0]["A"], "x | y")


class TraceTest(unittest.TestCase):
    def docs(self, **overrides):
        return {
            "docs/prd.md": PRD,
            "docs/e2e-test.md": E2E,
            "docs/development.md": DEV,
            "docs/experience.md": "| FLOW-01 | 등록 |",
            "docs/security-compliance.md": "| SEC-03 | 접근 권한 |",
            **overrides,
        }

    def test_archived_change_needs_a_filled_development_row(self) -> None:
        failures, _ = check(
            self.docs(),
            [],
            archived={"add-todo", "add-share", "add-x"},
            touched=set(),
            claims_changed=False,
        )
        self.assertEqual(len(failures), 2)
        self.assertIn("add-share", failures[0])
        self.assertIn("add-x", failures[1])

    def test_completed_requirement_needs_pass_with_sha(self) -> None:
        failures, notes = check(
            self.docs(), [], archived=set(), touched=set(), claims_changed=True
        )
        self.assertEqual(
            failures,
            [
                "docs/prd.md: REQ-03이 완료인데 e2e-test.md 실행 결과에 PASS와 40자 SHA가 있는 TC가 없습니다 (확인한 TC: TC-02)"
            ],
        )
        self.assertEqual(notes, {})

    def test_unchanged_claims_are_only_notes(self) -> None:
        failures, notes = check(
            self.docs(), [], archived=set(), touched=set(), claims_changed=False
        )
        self.assertEqual(failures, [])
        self.assertEqual(list(notes), ["근거 없는 완료 (이번 PR에서 바뀌지 않음)"])

    def test_notes_for_touched_changes(self) -> None:
        changes = [
            change("add-todo", archived=True),
            change("other", reqs=("REQ-05",), owner=None),
        ]
        _, notes = check(
            self.docs(),
            changes,
            archived=set(),
            touched={"add-todo", "other"},
            claims_changed=False,
        )
        self.assertEqual(
            notes["OpenSpec의 REQ가 docs/prd.md 추적표에 없음"], ["other: REQ-05"]
        )
        self.assertEqual(
            notes["OpenSpec의 AC가 docs/prd.md에 없음"],
            ["add-todo: AC-09", "other: AC-09"],
        )
        self.assertEqual(
            notes["archive된 변경의 AC에 e2e-test.md 테스트 시나리오가 없음"],
            ["add-todo: AC-09"],
        )
        self.assertEqual(notes["proposal에 요구사항·담당 줄이 없음"], ["other: 담당"])
        self.assertEqual(
            notes["시나리오의 연결 ID가 문서에 없음"],
            ["add-todo: SEC-04 → docs/security-compliance.md"],
        )

    def test_untouched_changes_are_not_reported(self) -> None:
        _, notes = check(
            self.docs(),
            [change("other", reqs=("REQ-05",))],
            archived=set(),
            touched=set(),
            claims_changed=False,
        )
        self.assertNotIn("OpenSpec의 REQ가 docs/prd.md 추적표에 없음", notes)


if __name__ == "__main__":
    unittest.main()
