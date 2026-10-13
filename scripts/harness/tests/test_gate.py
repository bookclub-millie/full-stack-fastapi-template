import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import gate
from registry import NotFound, Release

NOW = datetime(2026, 10, 13, tzinfo=timezone.utc)
GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}

BUNFIG = "[install]\nminimumReleaseAge = 604800\n"
UV_LOCK = 'version = 1\n\n[options]\nexclude-newer-span = "P7D"\n'


def bun_lock(*entries: str) -> str:
    body = ",\n".join(
        f'    "{name}": ["{name}@{version}", "", {{}}, "sha512-x"]'
        for name, version in entries
    )
    return '{\n  "lockfileVersion": 1,\n  "packages": {\n' + body + ",\n  }\n}\n"


class FakeRegistry:
    def __init__(self, releases: dict[tuple[str, str], Release | Exception]) -> None:
        self.releases = releases
        self.calls: list[tuple[str, str, bool]] = []

    def __call__(self, package, *, need_first: bool) -> Release:
        self.calls.append((package.name, package.version, need_first))
        result = self.releases[(package.name, package.version)]
        if isinstance(result, Exception):
            raise result
        return result


def days_ago(days: int) -> datetime:
    return NOW - timedelta(days=days)


class GateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.write(
            {
                "bunfig.toml": BUNFIG,
                "bun.lock": bun_lock(("axios", "1.0.0")),
                "uv.lock": UV_LOCK,
                "backend/tests/test_a.py": "def test_a():\n    assert 1\n",
                "backend/app/main.py": "x = 1\n",
            }
        )
        self.base = self.commit("base")

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

    def write(self, files: dict[str, str | None]) -> None:
        for path, text in files.items():
            target = self.repo / path
            if text is None:
                target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def analyze(self, head: str, lookup=None, **kwargs) -> dict:
        options = {
            "gitleaks_exit": "0",
            "gitleaks_report": None,
            "zizmor_exit": "skipped",
            "zizmor_log": None,
        }
        options.update(kwargs)
        return gate.analyze(
            str(self.repo),
            self.base,
            head,
            now=NOW,
            lookup=lookup or FakeRegistry({}),
            **options,
        )

    def check(self, report: dict, check_id: str) -> dict:
        return next(c for c in report["checks"] if c["id"] == check_id)

    def test_clean_change(self) -> None:
        self.write({"backend/app/main.py": "x = 2\n"})
        report = self.analyze(self.commit("clean"))
        self.assertFalse(report["deterministic_failed"])
        self.assertFalse(report["needs_ack"])
        self.assertEqual(self.check(report, "workflows")["status"], "skip")
        self.assertEqual(self.check(report, "supply-chain")["status"], "pass")

    def test_too_young_version_fails(self) -> None:
        self.write({"bun.lock": bun_lock(("axios", "1.1.0"))})
        registry = FakeRegistry(
            {("axios", "1.1.0"): Release(days_ago(2), days_ago(4000))}
        )
        report = self.analyze(self.commit("bump"), lookup=registry)
        self.assertTrue(report["deterministic_failed"])
        self.assertIn("axios@1.1.0", self.check(report, "supply-chain")["items"][0])
        self.assertEqual(registry.calls, [("axios", "1.1.0", False)])

    def test_cooldown_exclusion_allows_young_version(self) -> None:
        self.write(
            {
                "bunfig.toml": BUNFIG + 'minimumReleaseAgeExcludes = ["axios"]\n',
                "bun.lock": bun_lock(("axios", "1.1.0")),
            }
        )
        registry = FakeRegistry(
            {("axios", "1.1.0"): Release(days_ago(2), days_ago(4000))}
        )
        report = self.analyze(self.commit("security fix"), lookup=registry)
        self.assertFalse(report["deterministic_failed"])
        self.assertIn("harness-config", {s["id"] for s in report["signals"]})

    def test_young_new_package_is_a_signal(self) -> None:
        self.write({"bun.lock": bun_lock(("axios", "1.0.0"), ("brand-new", "1.0.0"))})
        registry = FakeRegistry(
            {("brand-new", "1.0.0"): Release(days_ago(10), days_ago(12))}
        )
        report = self.analyze(self.commit("add"), lookup=registry)
        self.assertFalse(report["deterministic_failed"])
        signal = next(s for s in report["signals"] if s["id"] == "young-package")
        self.assertIn("brand-new", signal["items"][0])
        self.assertEqual(registry.calls, [("brand-new", "1.0.0", True)])

    def test_missing_package_and_lookup_errors_fail_closed(self) -> None:
        self.write(
            {
                "bun.lock": bun_lock(
                    ("axios", "1.0.0"), ("ghost", "1.0.0"), ("flaky", "1.0.0")
                )
            }
        )
        registry = FakeRegistry(
            {
                ("ghost", "1.0.0"): NotFound("ghost"),
                ("flaky", "1.0.0"): TimeoutError("slow"),
            }
        )
        report = self.analyze(self.commit("add"), lookup=registry)
        items = " ".join(self.check(report, "supply-chain")["items"])
        self.assertIn("ghost@1.0.0", items)
        self.assertIn("flaky@1.0.0", items)
        self.assertTrue(report["deterministic_failed"])

    def test_non_registry_source_fails(self) -> None:
        lock = bun_lock(("axios", "1.0.0")).replace(
            "  }\n}",
            '    "evil": ["evil@https://example.com/evil.tgz", {}, "sha512-y"],\n  }\n}',
        )
        self.write({"bun.lock": lock})
        report = self.analyze(self.commit("tarball"))
        self.assertTrue(report["deterministic_failed"])
        self.assertIn("evil", self.check(report, "supply-chain")["items"][0])

    def test_disabling_cooldown_fails(self) -> None:
        self.write({"bunfig.toml": "[install]\n", "uv.lock": "version = 1\n"})
        report = self.analyze(self.commit("disable"))
        items = self.check(report, "supply-chain")["items"]
        self.assertEqual(len(items), 2)
        self.assertTrue(report["deterministic_failed"])

    def test_gitleaks_findings_and_errors(self) -> None:
        head = self.commit("empty")
        findings = [
            {
                "RuleID": "github-pat",
                "File": "a.py",
                "StartLine": 3,
                "Commit": "abcdef123456",
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(findings, handle)
        try:
            report = self.analyze(head, gitleaks_exit="3", gitleaks_report=handle.name)
        finally:
            os.unlink(handle.name)
        self.assertEqual(
            self.check(report, "secrets")["items"],
            ["a.py:3 github-pat (commit abcdef1)"],
        )
        report = self.analyze(head, gitleaks_exit="1")
        self.assertEqual(self.check(report, "secrets")["status"], "fail")

    def test_zizmor_failure_keeps_log(self) -> None:
        head = self.commit("empty")
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as handle:
            handle.write("error[unpinned-uses]: unpinned action reference\n")
        try:
            report = self.analyze(head, zizmor_exit="13", zizmor_log=handle.name)
        finally:
            os.unlink(handle.name)
        workflows = self.check(report, "workflows")
        self.assertEqual(workflows["status"], "fail")
        self.assertIn("unpinned-uses", workflows["log"])

    def test_deleted_test_needs_ack(self) -> None:
        self.write({"backend/tests/test_a.py": None})
        report = self.analyze(self.commit("delete test"))
        self.assertTrue(report["needs_ack"])
        self.assertFalse(report["deterministic_failed"])
        self.assertEqual([s["id"] for s in report["signals"]], ["test-removed"])

    def test_unknown_revision_is_an_error(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError):
            self.analyze("0" * 40)

    def test_archiving_without_development_row_fails_docs_check(self) -> None:
        header = "## AI 활용과 검증\n\n| Issue | 담당자 | AI 도구·사용 목적 | 변경 코드·활용 기록 | 검증·발견 문제 | 수정·재시험 근거 |\n|---|---|---|---|---|---|\n"
        self.write(
            {
                "docs/development.md": "# 개발 과정\n\n" + header,
                "openspec/changes/foo/proposal.md": "# Foo\n요구사항: REQ-01\n",
            }
        )
        self.base = self.commit("propose")
        self.write(
            {
                "openspec/changes/foo/proposal.md": None,
                "openspec/changes/archive/2026-10-14-foo/proposal.md": "# Foo\n요구사항: REQ-01\n",
            }
        )
        report = self.analyze(self.commit("archive"))
        docs = self.check(report, "docs")
        self.assertEqual(docs["status"], "fail")
        self.assertIn("foo", docs["items"][0])
        self.assertIn(
            "OpenSpec의 REQ가 docs/prd.md 추적표에 없음",
            [n["title"] for n in report["notes"]],
        )

        row = "| #3 (foo) | gray | Claude Code 구현 | PR #7 | 경계값 누락 | 재실행 |\n"
        self.write({"docs/development.md": "# 개발 과정\n\n" + header + row})
        report = self.analyze(self.commit("record"))
        self.assertEqual(self.check(report, "docs")["status"], "pass")

    def test_editing_an_old_archive_is_not_archiving(self) -> None:
        self.write({"openspec/changes/archive/2026-01-01-old/proposal.md": "# Old\n"})
        self.base = self.commit("old archive")
        self.write({"openspec/changes/archive/2026-01-01-old/notes.md": "추가 메모\n"})
        report = self.analyze(self.commit("note"))
        self.assertEqual(self.check(report, "docs")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
