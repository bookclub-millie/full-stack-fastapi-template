import unittest

from doctables import filled, table
from traceability import check, check_tests

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
                "docs/prd.md: REQ-03이 완료인데 e2e-test.md 실행 결과에서 최신 결과가 PASS이고 실제 커밋 SHA(40자)가 있는 TC가 없습니다 (확인한 TC: TC-02)"
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

    def test_latest_result_per_tc_wins(self) -> None:
        regressed = (
            E2E + f"| TC-01 | {'c' * 40} | 2026-10-15 CI | 실패 | FAIL | run/2 |\n"
        )
        failures, _ = check(
            self.docs(**{"docs/e2e-test.md": regressed}),
            [],
            archived=set(),
            touched=set(),
            claims_changed=True,
        )
        self.assertTrue(any("REQ-01" in f for f in failures))

    def test_tc_padding_does_not_matter(self) -> None:
        prd = PRD.replace("| TC-01 | 완료 |", "| TC-1 | 완료 |")
        e2e = E2E.replace("| TC-01 | REQ-01", "| TC-001 | REQ-01")
        failures, _ = check(
            self.docs(**{"docs/prd.md": prd, "docs/e2e-test.md": e2e}),
            [],
            archived=set(),
            touched=set(),
            claims_changed=True,
        )
        self.assertFalse(any("REQ-01" in f for f in failures))

    def test_manual_tc_is_not_evidence(self) -> None:
        e2e = E2E.replace(
            "| TC-01 | REQ-01 · AC-01 | E2E |", "| TC-01 | REQ-01 · AC-01 | 수동 |"
        )
        failures, _ = check(
            self.docs(**{"docs/e2e-test.md": e2e}),
            [],
            archived=set(),
            touched=set(),
            claims_changed=True,
        )
        self.assertTrue(
            any(
                "REQ-01" in f and "수동 TC TC-01는 근거로 세지 않음" in f
                for f in failures
            )
        )

    def test_made_up_sha_is_not_evidence(self) -> None:
        failures, _ = check(
            self.docs(),
            [],
            archived=set(),
            touched=set(),
            claims_changed=True,
            sha_exists=lambda sha: False,
        )
        self.assertTrue(any("REQ-01" in f for f in failures))
        failures, _ = check(
            self.docs(),
            [],
            archived=set(),
            touched=set(),
            claims_changed=True,
            sha_exists=lambda sha: True,
        )
        self.assertFalse(any("REQ-01" in f for f in failures))


BACKEND = "backend/tests/api/test_todo.py"
E2E_SPEC = "frontend/tests/e2e/todo.spec.ts"


class CheckTestsTest(unittest.TestCase):
    def run_check(self, tests, changes=(), *, archived=(), changed=(), e2e=E2E):
        return check_tests(
            {"docs/e2e-test.md": e2e},
            tests,
            list(changes),
            archived=set(archived),
            changed=set(changed),
        )

    def test_name_problems_fail_only_in_changed_files(self) -> None:
        tests = {E2E_SPEC: 'test("TC01 잘못", async () => {})\n'}
        failures, _ = self.run_check(tests, changed={E2E_SPEC})
        self.assertEqual(len(failures), 1)
        self.assertIn(f"{E2E_SPEC}:1", failures[0])
        failures, notes = self.run_check(tests)
        self.assertEqual(failures, [])
        self.assertIn("테스트 이름의 TC 표기 (이번 PR에서 바뀌지 않음)", notes)

    def test_tc_missing_from_scenarios(self) -> None:
        tests = {BACKEND: "def test_tc_01_ok(): pass\ndef test_tc_09_new(): pass\n"}
        failures, _ = self.run_check(tests, changed={BACKEND})
        self.assertEqual(len(failures), 1)
        self.assertIn("TC-09", failures[0])
        # An unchanged test fails too when this PR edits the scenarios.
        failures, _ = self.run_check(tests, changed={"docs/e2e-test.md"})
        self.assertEqual(len(failures), 1)
        failures, notes = self.run_check(tests)
        self.assertEqual(failures, [])
        self.assertIn("시나리오에 없는 TC 테스트 (이번 PR에서 바뀌지 않음)", notes)

    def test_archiving_needs_a_test_for_every_ac(self) -> None:
        archived = change("add-todo", archived=True)
        failures, _ = self.run_check({}, [archived], archived={"add-todo"})
        self.assertEqual(
            failures,
            [
                (
                    "add-todo의 AC-01: TC-01를 확인하는 실행되는 테스트가 없습니다 (pytest `test_tc_01_<설명>` 또는 "
                    'Playwright·vitest `test("TC-01 <설명>", ...)`, 위치: backend/tests/(pytest), frontend/tests/e2e/(Playwright), '
                    "frontend/src/**/*.test.ts(vitest))"
                ),
                "docs/e2e-test.md: add-todo의 AC-09를 확인하는 테스트 시나리오(TC) 행이 없습니다",
            ],
        )
        e2e = E2E.replace(
            "| TC-02 | AC-04 | 단위 |",
            "| TC-02 | AC-04 | 단위 |\n| TC-03 | AC-09 | 수동 |",
        )
        failures, notes = self.run_check(
            {BACKEND: "def test_tc_1_reject(): pass\n"},
            [archived],
            archived={"add-todo"},
            e2e=e2e,
        )
        self.assertEqual(failures, [])
        self.assertEqual(
            notes["수동 TC만 있는 AC (결과가 수집되지 않아 미검증으로 남음)"],
            ["add-todo: AC-09"],
        )

    def test_test_must_be_in_the_file_tasks_md_names(self) -> None:
        archived = change("add-todo", archived=True)
        archived.test_tasks = [("TC-01", BACKEND)]
        e2e = E2E.replace(
            "| TC-02 | AC-04 | 단위 |",
            "| TC-02 | AC-04 | 단위 |\n| TC-03 | AC-09 | 수동 |",
        )
        elsewhere = "backend/tests/api/test_other.py"
        failures, _ = self.run_check(
            {elsewhere: "def test_tc_01_reject(): pass\n"},
            [archived],
            archived={"add-todo"},
            e2e=e2e,
        )
        self.assertEqual(
            failures,
            [
                (
                    f"add-todo의 tasks.md: {BACKEND}에서 TC-01 이름의 테스트를 찾지 못했습니다 (있는 곳: {elsewhere}). "
                    "테스트를 옮기거나 tasks.md 경로를 고치세요"
                )
            ],
        )
        failures, _ = self.run_check(
            {BACKEND: "def test_tc_01_reject(): pass\n"},
            [archived],
            archived={"add-todo"},
            e2e=e2e,
        )
        self.assertEqual(failures, [])

    def test_skipped_tests_and_unnamed_scenarios_do_not_cover(self) -> None:
        archived = change("add-todo", archived=True)
        archived.requirements[0].scenarios.append(Scenario(None, "이름만"))
        e2e = E2E.replace(
            "| TC-02 | AC-04 | 단위 |",
            "| TC-02 | AC-04 | 단위 |\n| TC-03 | AC-9 | 수동 |",  # AC-9 == AC-09
        )
        failures, _ = self.run_check(
            {
                BACKEND: "import pytest\n@pytest.mark.skip\ndef test_tc_01_reject(): pass\n"
            },
            [archived],
            archived={"add-todo"},
            e2e=e2e,
        )
        self.assertEqual(len(failures), 2)
        self.assertIn("AC ID가 없는 Scenario 1개", failures[0])
        self.assertIn("건너뛰는 테스트만 있음: TC-01", failures[1])

    def test_manual_must_be_exact(self) -> None:
        archived = change("add-todo", archived=True)
        e2e = E2E.replace(
            "| TC-02 | AC-04 | 단위 |",
            "| TC-02 | AC-04 | 단위 |\n| TC-03 | AC-09 | 자동(수동 보조) |",
        )
        failures, _ = self.run_check(
            {BACKEND: "def test_tc_01_reject(): pass\n"},
            [archived],
            archived={"add-todo"},
            e2e=e2e,
        )
        self.assertEqual(len(failures), 1)
        self.assertIn("TC-03를 확인하는 실행되는 테스트가 없습니다", failures[0])

    def test_already_archived_change_is_only_a_note(self) -> None:
        failures, notes = self.run_check(
            {}, [change("add-todo", archived=True)], changed={"docs/prd.md"}
        )
        self.assertEqual(failures, [])
        self.assertEqual(len(notes["archive된 변경의 AC ↔ TC ↔ 테스트 누락"]), 2)

    def test_scenarios_without_tests_are_noted_when_relevant(self) -> None:
        title = "테스트가 없는 TC 시나리오 (구현 전이면 정상, 결과가 수집되지 않음)"
        _, notes = self.run_check({}, changed={"docs/e2e-test.md"})
        self.assertEqual(notes[title], ["TC-01", "TC-02"])
        _, notes = self.run_check({}, changed={"backend/app/main.py"})
        self.assertNotIn(title, notes)


if __name__ == "__main__":
    unittest.main()
