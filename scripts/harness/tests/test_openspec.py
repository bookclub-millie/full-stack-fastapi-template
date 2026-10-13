import tempfile
import unittest
from pathlib import Path

from openspec import (
    load_changes,
    parse_proposal,
    parse_spec,
    parse_tasks,
    parse_test_tasks,
)

PROPOSAL = """# 할 일 등록
요구사항: REQ-01, REQ-02
담당: @gray-dx
범위: 필수

## Why

사용자가 할 일을 등록하고
다시 조회할 수 있어야 한다.

## What Changes

- 등록 API
"""

SPEC = """# Spec Delta

## ADDED Requirements

### Requirement: REQ-01 할 일 등록
The system SHALL store todos.

#### Scenario: AC-01 필수 입력값이 없으면 거부한다
- **WHEN** 제목 없이 등록한다
- **THEN** 400을 반환한다
- **연결**: FLOW-01, SEC-04

#### Scenario: AC-02 저장 후 새로고침해도 보인다
- **WHEN** 등록 후 새로고침한다
- **THEN** 같은 내용이 보인다

## REMOVED Requirements

### Requirement: REQ-09 옛 기능
#### Scenario: AC-09 사라질 시나리오
"""

TASKS = """# Tasks

## 1. 구현
- [x] 1.1 API
- [ ] 1.2 화면

## 2. 문서·근거
- [X] 2.1 prd.md
"""


class ProposalTest(unittest.TestCase):
    def test_metadata_and_why(self) -> None:
        proposal = parse_proposal(PROPOSAL)
        self.assertEqual(proposal.title, "할 일 등록")
        self.assertEqual(proposal.requirements, ["REQ-01", "REQ-02"])
        self.assertEqual(proposal.owner, "gray-dx")
        self.assertEqual(proposal.scope, "필수")
        self.assertEqual(
            proposal.why, "사용자가 할 일을 등록하고\n다시 조회할 수 있어야 한다."
        )

    def test_generic_title_and_missing_metadata(self) -> None:
        proposal = parse_proposal("# Proposal\n\n## Why\n\nx\n")
        self.assertIsNone(proposal.title)
        self.assertEqual(proposal.requirements, [])
        self.assertIsNone(proposal.owner)


class SpecTest(unittest.TestCase):
    def test_added_requirements_and_scenarios(self) -> None:
        requirements = parse_spec(SPEC)
        self.assertEqual([r.id for r in requirements], ["REQ-01"])
        scenarios = requirements[0].scenarios
        self.assertEqual([s.id for s in scenarios], ["AC-01", "AC-02"])
        self.assertEqual(scenarios[0].name, "필수 입력값이 없으면 거부한다")
        self.assertEqual(scenarios[0].links, ["FLOW-01", "SEC-04"])
        self.assertEqual(scenarios[1].links, [])

    def test_requirement_without_id(self) -> None:
        requirements = parse_spec(
            "## ADDED Requirements\n### Requirement: 그냥 이름\n#### Scenario: 이름만\n"
        )
        self.assertIsNone(requirements[0].id)
        self.assertEqual(requirements[0].name, "그냥 이름")
        self.assertIsNone(requirements[0].scenarios[0].id)


class TasksTest(unittest.TestCase):
    def test_progress(self) -> None:
        self.assertEqual(parse_tasks(TASKS), (2, 3))
        self.assertEqual(parse_tasks(None), (0, 0))

    def test_test_tasks_name_their_file(self) -> None:
        text = (
            "- [ ] 2.3 TC-07 (AC-07) backend/tests/api/routes/test_items.py::test_tc_07_reject\n"
            '- [x] 2.4 TC-8 (AC-08) `frontend/tests/e2e/items.spec.ts::"TC-08 저장"`\n'
            "- [ ] 3.1 docs/e2e-test.md 테스트 시나리오에 TC-07 행 추가\n"
            "TC-09 backend/tests/test_x.py::test_tc_09 (작업 줄이 아님)\n"
            # The TC comes from the name after ::, not from other ids on the line.
            "- [ ] 2.5 Replace TC-03 check: backend/tests/a.py::test_tc_10_x, "
            'TC-11 (AC-11) frontend/tests/e2e/b.spec.ts::"TC-11 y"\n'
            "- [ ] 2.6 backend/tests/c.py::test_without_tc\n"
        )
        self.assertEqual(
            parse_test_tasks(text),
            [
                ("TC-07", "backend/tests/api/routes/test_items.py"),
                ("TC-08", "frontend/tests/e2e/items.spec.ts"),
                ("TC-10", "backend/tests/a.py"),
                ("TC-11", "frontend/tests/e2e/b.spec.ts"),
            ],
        )


class LoadChangesTest(unittest.TestCase):
    def test_active_and_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            active = root / "openspec/changes/add-todo"
            (active / "specs/todo").mkdir(parents=True)
            (active / "proposal.md").write_text(PROPOSAL)
            (active / "specs/todo/spec.md").write_text(SPEC)
            (active / "tasks.md").write_text(TASKS)
            archived = root / "openspec/changes/archive/2026-10-14-add-login"
            archived.mkdir(parents=True)
            (archived / "proposal.md").write_text("# 로그인\n요구사항: REQ-03\n")
            (root / "openspec/changes/no-proposal").mkdir()

            changes = {c.id: c for c in load_changes(root)}

        self.assertEqual(set(changes), {"add-todo", "add-login"})
        self.assertFalse(changes["add-todo"].archived)
        self.assertEqual(changes["add-todo"].path, "openspec/changes/add-todo")
        self.assertEqual(
            [s.id for s in changes["add-todo"].scenarios], ["AC-01", "AC-02"]
        )
        self.assertEqual(changes["add-todo"].tasks, (2, 3))
        self.assertTrue(changes["add-login"].archived)
        self.assertEqual(
            changes["add-login"].path, "openspec/changes/archive/2026-10-14-add-login"
        )


if __name__ == "__main__":
    unittest.main()
