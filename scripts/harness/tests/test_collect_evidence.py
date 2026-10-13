import json
import unittest
from pathlib import Path
from unittest import mock

import collect_evidence
from collect_evidence import merge, parse_junit, parse_playwright, render_rows

SHA = "b" * 40
JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest">
  <testcase classname="tests.api.test_items" name="test_tc_01_create_item" time="0.1"/>
  <testcase classname="tests.api.test_items" name="test_tc_02_reject_empty"><failure message="assert 422"/></testcase>
  <testcase classname="tests.api.test_items" name="test_tc_3_later"><skipped message="todo"/></testcase>
  <testcase classname="tests.api.test_items" name="test_read_item"/>
</testsuite></testsuites>
"""
# Shape of `playwright merge-reports --reporter json` output (checked with Playwright 1.63).
PLAYWRIGHT = json.dumps(
    {
        "suites": [
            {
                "title": "items.spec.ts",
                "specs": [
                    {
                        "title": "TC-01 저장 후 새로고침해도 보인다",
                        "ok": True,
                        "tests": [{"status": "expected"}],
                    },
                    {
                        "title": "TC-04 권한 없는 사용자 거부",
                        "ok": False,
                        "tests": [{"status": "unexpected"}],
                    },
                    {
                        "title": "TC-05 플래키",
                        "ok": True,
                        "tests": [{"status": "flaky"}],
                    },
                    {
                        "title": "TC 없는 테스트",
                        "ok": True,
                        "tests": [{"status": "expected"}],
                    },
                ],
                "suites": [
                    {
                        "title": "nested",
                        "specs": [
                            {
                                "title": "TC-06 건너뜀",
                                "ok": True,
                                "tests": [{"status": "skipped"}],
                            }
                        ],
                    }
                ],
            }
        ]
    }
)


class ParseTest(unittest.TestCase):
    def test_junit(self) -> None:
        results, untagged = parse_junit(JUNIT)
        self.assertEqual(
            [(r.tc, r.status) for r in results],
            [("TC-01", "PASS"), ("TC-02", "FAIL"), ("TC-3", "SKIP")],
        )
        self.assertEqual(untagged, 1)

    def test_playwright(self) -> None:
        results, untagged = parse_playwright(PLAYWRIGHT)
        self.assertEqual(
            [(r.tc, r.status) for r in results],
            [
                ("TC-01", "PASS"),
                ("TC-04", "FAIL"),
                ("TC-05", "FAIL"),
                ("TC-06", "SKIP"),
            ],
        )
        self.assertEqual(untagged, 1)


class MergeRenderTest(unittest.TestCase):
    def test_worst_status_wins_and_rows_render(self) -> None:
        backend = ("Test Backend", "https://x/run/1", "2026-10-14T01:00:00Z")
        e2e = ("Playwright Tests", "https://x/run/2", "2026-10-14T01:05:00Z")
        junit, _ = parse_junit(JUNIT)
        playwright, _ = parse_playwright(PLAYWRIGHT)
        evidence = merge([(r, backend) for r in junit] + [(r, e2e) for r in playwright])
        tc01 = evidence[0]
        self.assertEqual(
            (tc01.tc, tc01.status, len(tc01.sources)), ("TC-01", "PASS", 2)
        )
        rows = render_rows(evidence, SHA).splitlines()
        self.assertEqual(rows[0].split(" | ")[0], "| TC-01")
        self.assertIn(SHA, rows[0])
        self.assertIn("https://x/run/1 https://x/run/2", rows[0])
        self.assertTrue(rows[0].endswith("|"))


class CollectTest(unittest.TestCase):
    def test_downloads_reports_and_warns_about_missing_ones(self) -> None:
        runs = {
            "workflow_runs": [
                {
                    "id": 1,
                    "name": "Test Backend",
                    "status": "completed",
                    "html_url": "u1",
                    "created_at": "t1",
                },
                {
                    "id": 3,
                    "name": "Test Backend",
                    "status": "completed",
                    "html_url": "u3",
                    "created_at": "t3",
                },
                {
                    "id": 2,
                    "name": "Playwright Tests",
                    "status": "in_progress",
                    "html_url": "u2",
                    "created_at": "t2",
                },
            ]
        }

        def fake_gh(*args: str) -> str:
            if args[0] == "api":
                return json.dumps(runs)
            if args[:2] == ("run", "download"):
                self.assertEqual(args[2], "3")  # the latest run wins
                Path(args[args.index("-D") + 1], "junit.xml").write_text(JUNIT)
                return ""
            raise AssertionError(args)

        with mock.patch.object(collect_evidence, "_gh", fake_gh):
            evidence, warnings = collect_evidence.collect("o/r", SHA)
        self.assertEqual([e.tc for e in evidence], ["TC-01", "TC-02", "TC-3"])
        self.assertEqual(evidence[0].sources, [("Test Backend", "u3", "t3")])
        self.assertIn("Playwright Tests: 아직 실행 중입니다 (u2)", warnings)
        self.assertIn(
            "Test Backend: TC ID가 없는 테스트 1개는 집계하지 않았습니다", warnings
        )


if __name__ == "__main__":
    unittest.main()
