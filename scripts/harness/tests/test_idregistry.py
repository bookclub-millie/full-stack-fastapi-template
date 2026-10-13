import unittest

from idregistry import claimed, duplicates, ids_in, next_free, registered, scenario_ids

from openspec import Change, Proposal, Requirement, Scenario

PRD = """# 요구사항

예: `요구사항: REQ-09`처럼 쓴다.

## 요구사항 추적표

| REQ | 요구사항 | 우선순위 | AC·인수조건 | FLOW | Issue·코드 | TC | 상태 |
|---|---|---|---|---|---|---|---|
| REQ-01 | 등록 | 필수 | AC-01 빈 제목 거부, AC-02 저장 | FLOW-01 | | TC-01 | 계획 |
| REQ-1 | 목록 | 필수 | AC-03 · AC-2 (AC-01 참고) | | | | 계획 |
"""
E2E = """## 테스트 시나리오

| TC | REQ·AC·FLOW | 종류 | 사전 조건 | 입력·행동 | 예상 결과 | 실행 명령 |
|---|---|---|---|---|---|---|
| TC-01 | AC-01 | 단위 | | | | |
| TC-02 | AC-03 | 단위 | | | | |

본문의 `test_tc_01_…` 예시는 행이 아니다.
"""
EXPERIENCE = """## 핵심 사용자 흐름

| FLOW | 사용자·목적 | 관련 REQ·AC | 시작 조건 | 사용 순서 | 기대 화면·출력·저장 결과 | TC |
|---|---|---|---|---|---|---|
| FLOW-01 | 사용자 | REQ-01 | | | | TC-01 |
"""
DOCS = {"docs/prd.md": PRD, "docs/e2e-test.md": E2E, "docs/experience.md": EXPERIENCE}


def change(change_id: str, requirements: list[Requirement], test_tasks=()) -> Change:
    return Change(
        id=change_id,
        path=f"openspec/changes/{change_id}",
        archived=False,
        proposal=Proposal(title="t", requirements=[], owner=None, scope=None, why=""),
        requirements=requirements,
        tasks=(0, 0),
        test_tasks=list(test_tasks),
    )


class RegistryTest(unittest.TestCase):
    def test_ids_are_normalized(self) -> None:
        self.assertEqual(
            ids_in("REQ-1 AC-007 FLOW-2 TC-3 SEC-04"),
            {"REQ-01", "AC-07", "FLOW-02", "TC-03"},
        )

    def test_rows_register_leading_ids_only(self) -> None:
        rows = registered(DOCS)
        self.assertEqual(rows["REQ"], [["REQ-01"], ["REQ-01"]])
        # "(AC-01 참고)" mentions AC-01; it does not register it again.
        self.assertEqual(rows["AC"], [["AC-01", "AC-02"], ["AC-02", "AC-03"]])
        self.assertEqual(rows["TC"], [["TC-01"], ["TC-02"]])
        self.assertEqual(rows["FLOW"], [["FLOW-01"]])

    def test_duplicates(self) -> None:
        self.assertEqual(
            duplicates(DOCS), {"REQ-01": "docs/prd.md", "AC-02": "docs/prd.md"}
        )

    def test_claims(self) -> None:
        c = change(
            "x",
            [
                Requirement("REQ-04", "새것", [Scenario("AC-09", "a")]),
                Requirement(
                    "REQ-01",
                    "고침",
                    [Scenario("AC-01", "기존"), Scenario("AC-10", "추가")],
                    added=False,
                ),
            ],
            test_tasks=[("TC-12", "backend/tests/test_x.py")],
        )
        self.assertEqual(claimed(c), {"REQ-04", "AC-09", "TC-12"})
        existing = scenario_ids(
            [Requirement("REQ-01", "원래", [Scenario("AC-1", "s")])]
        )
        self.assertEqual(existing, {"REQ-01": {"AC-01"}})
        # Under MODIFIED, only scenarios the base branch does not have are claims.
        self.assertEqual(claimed(c, existing), {"REQ-04", "AC-09", "AC-10", "TC-12"})

    def test_next_free(self) -> None:
        self.assertEqual(
            next_free({"REQ-01", "REQ-03", "AC-12", "TC-1"} | ids_in("TC-02")),
            {"REQ": "REQ-04", "AC": "AC-13", "FLOW": "FLOW-01", "TC": "TC-03"},
        )


if __name__ == "__main__":
    unittest.main()
