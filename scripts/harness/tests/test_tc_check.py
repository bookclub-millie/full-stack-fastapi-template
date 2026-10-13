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
E2E = """## 테스트 시나리오

| TC | REQ·AC·FLOW | 종류 | 사전 조건 | 입력·행동 | 예상 결과 | 실행 명령 |
|---|---|---|---|---|---|---|
| TC-01 | REQ-01 · AC-01 | 단위 | | | | |
"""
SPEC = "### Requirement: REQ-01 등록\n\n#### Scenario: AC-01 거부\n"


class TcCheckCliTest(unittest.TestCase):
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

    def write(self, files: dict[str, str], *, add: bool = True) -> None:
        for path, text in files.items():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text(text)
        if add:
            self.git("add", "-A")

    def run_cli(
        self, *args: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-I", str(HARNESS / "tc_check.py"), *args],
            capture_output=True,
            check=False,
            text=True,
            cwd=cwd or self.root,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_tracked_test_files_are_checked(self) -> None:
        self.write(
            {
                "docs/e2e-test.md": E2E,
                "backend/tests/api/test_a.py": "def test_tc_01_ok(): pass\n",
            }
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        spec = {
            "frontend/tests/e2e/a.spec.ts": 'test("TC-02 새 시험", async () => {})\n'
        }
        self.write(spec, add=False)  # not added yet: not what will be committed
        self.assertEqual(self.run_cli().returncode, 0)
        self.git("add", "-A")
        # Works from a subdirectory too.
        result = self.run_cli(cwd=self.root / "backend")
        self.assertEqual(result.returncode, 1)
        self.assertIn("실패: frontend/tests/e2e/a.spec.ts:1 TC-02", result.stdout)

    def test_only_archives_new_to_the_base_branch_fail(self) -> None:
        old = "openspec/changes/archive/2026-10-01-old"
        self.write(
            {
                "docs/e2e-test.md": E2E,
                f"{old}/proposal.md": "# Old\n요구사항: REQ-01\n",
                f"{old}/specs/old/spec.md": SPEC,
            }
        )
        self.git("commit", "-q", "-m", "base")
        self.git("branch", "base")
        result = self.run_cli("--base", "base")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("archive된 변경의 AC ↔ TC ↔ 테스트 누락", result.stdout)

        new = "openspec/changes/archive/2026-10-14-foo"
        self.write(
            {
                f"{new}/proposal.md": "# Foo\n요구사항: REQ-01\n",
                f"{new}/specs/foo/spec.md": SPEC,
            }
        )
        result = self.run_cli("--base", "base")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "실패: foo의 AC-01: TC-01를 확인하는 실행되는 테스트가 없습니다",
            result.stdout,
        )
        self.assertNotIn("실패: old", result.stdout)

    def test_outside_a_repository(self) -> None:
        with tempfile.TemporaryDirectory() as elsewhere:
            result = self.run_cli("--repo", elsewhere)
        self.assertEqual(result.returncode, 2)
        self.assertIn("git 저장소가 아닙니다", result.stderr)


if __name__ == "__main__":
    unittest.main()
