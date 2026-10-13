import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import submission_check
from submission_check import FAIL, OK, WARN, Repo, evaluate, evaluate_github

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
SHA = "c" * 40
PRD = """## 요구사항 추적표

| REQ | 요구사항 | 우선순위 | AC·인수조건 | FLOW | Issue·코드 | TC | 상태 |
|---|---|---|---|---|---|---|---|
| REQ-01 | 등록 | 필수 | AC-01 | | #1 | TC-01 | 완료 |
"""
E2E_PASS = f"""## 실행 결과

| TC | 소스 SHA | 실행 시각·환경 | 실제 결과 | 상태 | 로그·화면 등 근거 경로 |
|---|---|---|---|---|---|
| TC-01 | {SHA} | CI | 통과 | PASS | run |
"""
FILLED = "| A | B |\n|---|---|\n| 내용 | 있음 |\n"


class SubmissionCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "-C", self.tmp.name, "init", "-q"], check=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def commit(self, files: dict[str, str]) -> str:
        for path, text in files.items():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(text)
        run = lambda *a: (
            subprocess.run(
                ["git", "-C", self.tmp.name, *a],
                check=True,
                capture_output=True,
                text=True,
                env=GIT_ENV,
            ).stdout
        )
        run("add", "-A")
        run("commit", "-q", "-m", "c")
        return run("rev-parse", "HEAD").strip()

    def docs(self, **overrides: str) -> dict[str, str]:
        files = {
            "README.md": "[문서](docs/README.md)\n",
            "docs/README.md": "project-brief.md prd.md arch.md experience.md development.md security-compliance.md e2e-test.md\n",
            "docs/project-brief.md": FILLED,
            "docs/prd.md": PRD,
            "docs/arch.md": FILLED,
            "docs/experience.md": FILLED,
            "docs/development.md": FILLED,
            "docs/security-compliance.md": FILLED,
            "docs/e2e-test.md": E2E_PASS,
            "docs/security-policy.md": "정책\n",
        }
        files.update(overrides)
        return files

    def results(self, sha: str) -> dict[str, str]:
        return {name: mark for name, mark, _ in evaluate(Repo(self.tmp.name), sha)}

    def test_complete_submission(self) -> None:
        first = self.commit(self.docs(**{"docs/e2e-test.md": "## 실행 결과\n"}))
        # Evidence must name a real commit: record the result of the first commit.
        sha = self.commit({"docs/e2e-test.md": E2E_PASS.replace(SHA, first)})
        results = self.results(sha)
        self.assertNotIn(FAIL, results.values())
        self.assertEqual(results["필수 REQ 근거"], OK)
        self.assertEqual(results["README 연결"], OK)
        self.assertEqual(results["TC 연결"], OK)

    def test_duplicate_ids_fail(self) -> None:
        prd = PRD + "| REQ-01 | 목록 | 추가 | AC-02 | | | | 계획 |\n"
        results = self.results(self.commit(self.docs(**{"docs/prd.md": prd})))
        self.assertEqual(results["ID 중복"], FAIL)

    def test_tc_link_problems_warn(self) -> None:
        files = self.docs(
            **{"backend/tests/api/test_x.py": "def test_tc_09_orphan():\n    pass\n"}
        )
        sha = self.commit(files)
        detail = {
            name: (mark, text)
            for name, mark, text in evaluate(Repo(self.tmp.name), sha)
        }
        self.assertEqual(detail["TC 연결"][0], WARN)
        self.assertIn("TC-09", detail["TC 연결"][1])

    def test_missing_doc_and_unsupported_completion_fail(self) -> None:
        files = self.docs(**{"docs/e2e-test.md": "## 실행 결과\n"})
        del files["docs/arch.md"]
        results = self.results(self.commit(files))
        self.assertEqual(results["문서 8개"], FAIL)
        self.assertEqual(results["필수 REQ 근거"], FAIL)

    def test_unknown_commit(self) -> None:
        self.commit(self.docs())
        self.assertEqual(self.results("d" * 40), {"소스 SHA": FAIL})

    def test_template_docs_and_active_change_warn(self) -> None:
        files = self.docs(
            **{
                "docs/experience.md": "| FLOW | 목적 |\n|---|---|\n",
                "openspec/changes/x/proposal.md": "# X\n",
            }
        )
        results = self.results(self.commit(files))
        self.assertEqual(results["문서 작성"], WARN)
        self.assertEqual(results["OpenSpec"], WARN)

    def test_docs_untouched_since_the_template_warn(self) -> None:
        self.commit(self.docs())  # what "Use this template" copies
        sha = self.commit(
            {"docs/prd.md": PRD + "| REQ-02 | 목록 | 추가 | AC-02 | | | | 계획 |\n"}
        )
        detail = {
            name: detail for name, _, detail in evaluate(Repo(self.tmp.name), sha)
        }
        self.assertIn("docs/arch.md", detail["문서 작성"])
        self.assertNotIn("docs/prd.md", detail["문서 작성"])

    def test_made_up_evidence_sha_fails(self) -> None:
        results = self.results(
            self.commit(self.docs())
        )  # E2E_PASS uses a SHA that is not a commit
        self.assertEqual(results["필수 REQ 근거"], FAIL)


class EvaluateGithubTest(unittest.TestCase):
    def run_with(self, runs: list[dict], statuses: list[dict]) -> tuple[str, str]:
        def fake(*args: str) -> object:
            url = args[-1]
            if "/check-runs" in url:
                return [{"check_runs": runs}]
            if url.endswith("/status?per_page=100"):
                return {"statuses": statuses}
            return [[{"state": "closed", "state_reason": "completed"}]]

        with mock.patch.object(submission_check, "_gh_json", fake):
            items = evaluate_github("o/r", "a" * 40, frozenset({"check"}))
        return items[0][1], items[0][2]

    def test_own_job_is_ignored_and_running_checks_only_warn(self) -> None:
        runs = [
            {"id": 1, "name": "check", "status": "in_progress", "conclusion": None},
            {
                "id": 2,
                "name": "test-backend",
                "status": "completed",
                "conclusion": "success",
            },
            {"id": 3, "name": "test-frontend", "status": "queued", "conclusion": None},
        ]
        self.assertEqual(self.run_with(runs, [])[0], WARN)
        self.assertEqual(
            self.run_with(
                runs[:2], [{"context": "harness/checks", "state": "success"}]
            )[0],
            OK,
        )

    def test_failed_gate_status_fails(self) -> None:
        runs = [
            {
                "id": 2,
                "name": "test-backend",
                "status": "completed",
                "conclusion": "success",
            }
        ]
        mark, detail = self.run_with(
            runs, [{"context": "harness/checks", "state": "failure"}]
        )
        self.assertEqual(mark, FAIL)
        self.assertIn("harness/checks", detail)

    def test_latest_rerun_wins(self) -> None:
        runs = [
            {
                "id": 2,
                "name": "test-backend",
                "status": "completed",
                "conclusion": "failure",
            },
            {
                "id": 5,
                "name": "test-backend",
                "status": "completed",
                "conclusion": "success",
            },
        ]
        self.assertEqual(self.run_with(runs, [])[0], OK)


if __name__ == "__main__":
    unittest.main()
