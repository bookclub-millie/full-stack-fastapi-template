from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}
PRD = """예: `요구사항: REQ-40`

## 요구사항 추적표

| REQ | 요구사항 | 우선순위 | AC·인수조건 | FLOW | Issue·코드 | TC | 상태 |
|---|---|---|---|---|---|---|---|
| REQ-01 | 등록 | 필수 | AC-01, AC-02 | FLOW-01 | | TC-03 | 계획 |
"""


class NextIdsCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git("init", "-q")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", self.tmp.name, *args],
            check=True,
            capture_output=True,
            env=GIT_ENV,
        )

    def write(self, files: dict[str, str]) -> None:
        for path, text in files.items():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(text)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-I", str(HARNESS / "next_ids.py"), "--no-fetch", *args],
            capture_output=True,
            check=False,
            text=True,
            cwd=self.root,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_counts_base_branch_and_working_tree(self) -> None:
        self.write({"docs/prd.md": PRD})
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.git("branch", "base")
        # Another change merged on the base branch after this checkout started ...
        self.git("switch", "-q", "-c", "other")
        self.write(
            {
                "openspec/changes/b/specs/x/spec.md": "### Requirement: REQ-05 b\n#### Scenario: AC-07 c\n"
            }
        )
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "other")
        self.git("branch", "-f", "base", "other")
        self.git("switch", "-q", "-")
        # ... and this checkout has its own work in progress.
        self.write(
            {
                "openspec/changes/a/tasks.md": "- [ ] 2.1 TC-08 (AC-02) x.py::test_tc_08\n"
            }
        )
        result = self.run_cli("--base", "base")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("다음 빈 번호: REQ-06  AC-08  FLOW-02  TC-09", result.stdout)
        self.assertIn("확인한 곳: 작업 트리, base", result.stdout)


if __name__ == "__main__":
    unittest.main()
