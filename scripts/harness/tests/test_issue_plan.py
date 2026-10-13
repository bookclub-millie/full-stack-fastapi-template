import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from issue_plan import TEST_RESULT_ITEM, plan

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
PROPOSAL = "# 할 일 등록\n요구사항: REQ-01\n담당: @gray\n범위: 필수\n\n## Why\n\n할 일을 저장한다.\n"
SPEC = (
    "## ADDED Requirements\n### Requirement: REQ-01 할 일 등록\n"
    "#### Scenario: AC-01 제목 없이 등록하면 거부한다\n#### Scenario: 아이디 없는 시나리오\n"
)


class IssuePlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
            env=GIT_ENV,
        ).stdout.strip()

    def commit(self, files: dict[str, str], message: str) -> str:
        for path, text in files.items():
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def plan(self) -> dict[str, dict]:
        return {
            item["id"]: item
            for item in plan(self.repo, "https://github.com/o/r", "master")
        }

    def test_active_change_renders_aidx_format(self) -> None:
        proposal_commit = self.commit(
            {
                "openspec/changes/add-todo/proposal.md": PROPOSAL,
                "openspec/changes/add-todo/specs/todo/spec.md": SPEC,
                "openspec/changes/add-todo/tasks.md": "- [x] 1.1 a\n- [ ] 1.2 b\n",
            },
            "propose",
        )
        item = self.plan()["add-todo"]
        self.assertEqual(item["title"], "[REQ-01] 할 일 등록")
        self.assertFalse(item["archived"])
        self.assertEqual(item["owner"], "gray")
        self.assertEqual(item["proposal_commit"], proposal_commit)
        self.assertIsNone(item["archive_commit"])
        self.assertEqual(
            item["criteria"],
            [
                "AC-01 제목 없이 등록하면 거부한다",
                "아이디 없는 시나리오",
                TEST_RESULT_ITEM,
            ],
        )
        body = item["managed"]
        self.assertTrue(
            body.startswith(
                "<!-- openspec-change: add-todo -->\n## 목적\n할 일을 저장한다.\n"
            )
        )
        for line in (
            "## 완료 조건",
            "- [ ] AC-01 제목 없이 등록하면 거부한다",
            "## 담당자 / 연결 문서",
            "담당: @gray",
            "요구사항: docs/prd.md의 REQ-01",
            "OpenSpec: [openspec/changes/add-todo](https://github.com/o/r/tree/master/openspec/changes/add-todo) (작업 1/2)",
            "범위: 필수",
        ):
            self.assertIn(line + "\n", body)

    def test_archived_change_keeps_both_commits(self) -> None:
        proposal_commit = self.commit(
            {"openspec/changes/add-todo/proposal.md": PROPOSAL}, "propose"
        )
        # What `openspec archive` does: move the change under archive/ with a date prefix.
        (self.repo / "openspec/changes/archive").mkdir()
        (self.repo / "openspec/changes/add-todo").rename(
            self.repo / "openspec/changes/archive/2026-10-14-add-todo"
        )
        archive_commit = self.commit({}, "archive")
        item = self.plan()["add-todo"]
        self.assertTrue(item["archived"])
        self.assertEqual(item["proposal_commit"], proposal_commit)
        self.assertEqual(item["archive_commit"], archive_commit)
        self.assertIn("openspec/changes/archive/2026-10-14-add-todo", item["managed"])

    def test_missing_metadata_is_visible(self) -> None:
        self.commit(
            {"openspec/changes/x/proposal.md": "# Proposal\n\n## Why\n\n"}, "propose"
        )
        item = self.plan()["x"]
        self.assertEqual(item["title"], "[OpenSpec] x")
        self.assertIn("proposal.md에 `담당:` 줄이 없습니다", item["managed"])
        self.assertIn("proposal.md에 `요구사항:` 줄이 없습니다", item["managed"])
        self.assertIn("proposal.md의 Why가 비어 있습니다", item["managed"])

    def test_active_change_wins_over_archived_with_same_id(self) -> None:
        self.commit(
            {
                "openspec/changes/archive/2026-10-01-add-todo/proposal.md": PROPOSAL,
                "openspec/changes/add-todo/proposal.md": PROPOSAL,
            },
            "both",
        )
        self.assertFalse(self.plan()["add-todo"]["archived"])


if __name__ == "__main__":
    unittest.main()
