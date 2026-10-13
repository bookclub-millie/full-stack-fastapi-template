#!/usr/bin/env python3
"""Collect TC results for one commit from CI and print docs/e2e-test.md rows.

    python3 scripts/harness/collect_evidence.py --sha <40-char SHA>

Reads the CI runs for that commit with the `gh` CLI (your login), downloads the
test reports they uploaded (pytest JUnit XML from Test Backend, Playwright JSON
from Playwright Tests, vitest JSON from Frontend Quality), maps test names
with a TC id (pytest `test_tc_01_...`, Playwright and vitest `TC-01 ...`; TC-1
and TC-01 are the same TC) to PASS / FAIL / SKIP,
and prints one row per TC for the 실행 결과 table. Copy the rows as they are;
a TC that did not run is not printed and stays 미검증.
See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tcnames

SOURCES = (
    # (workflow name, artifact name, report file, parser key)
    ("Test Backend", "junit-backend", "junit.xml", "junit"),
    ("Playwright Tests", "playwright-results", "results.json", "playwright"),
    ("Frontend Quality", "frontend-unit-results", "unit.json", "vitest"),
)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ORDER = {"FAIL": 0, "PASS": 1, "SKIP": 2}


@dataclass
class TestResult:
    tc: str
    name: str
    status: str  # PASS | FAIL | SKIP


@dataclass
class Evidence:
    tc: str
    status: str
    names: list[str] = field(default_factory=list)
    sources: list[tuple[str, str, str]] = field(
        default_factory=list
    )  # (workflow, url, time)


def parse_junit(text: str) -> tuple[list[TestResult], int]:
    """(results with a TC id, number of tests without one)."""
    results, untagged = [], 0
    for case in ET.fromstring(text).iter("testcase"):
        name = case.get("name", "")
        tc = tcnames.pytest_tc(name)
        if not tc:
            untagged += 1
            continue
        if case.find("failure") is not None or case.find("error") is not None:
            status = "FAIL"
        elif case.find("skipped") is not None:
            status = "SKIP"
        else:
            status = "PASS"
        results.append(TestResult(tc, name, status))
    return results, untagged


def parse_playwright(text: str) -> tuple[list[TestResult], int]:
    results, untagged = [], 0

    def walk(suite: dict) -> None:
        nonlocal untagged
        for spec in suite.get("specs", []):
            title = spec.get("title", "")
            tc = tcnames.title_tc(title)
            if not tc:
                untagged += 1
                continue
            tests = spec.get("tests", [])
            statuses = {test.get("status") for test in tests}
            if statuses == {"skipped"}:
                status = "SKIP"
            elif any(test.get("expectedStatus") == "failed" for test in tests):
                status = "FAIL"  # test.fail(): "passes" by failing, so no evidence
            elif spec.get("ok") and statuses <= {"expected", "skipped"}:
                status = "PASS"
            else:  # unexpected, or flaky (CI runs with --fail-on-flaky-tests)
                status = "FAIL"
            results.append(TestResult(tc, title, status))
        for child in suite.get("suites", []):
            walk(child)

    for suite in json.loads(text).get("suites", []):
        walk(suite)
    return results, untagged


def parse_vitest(text: str) -> tuple[list[TestResult], int]:
    """frontend/evidence-reporter.ts output. The TC id comes from the test's own
    title, not its describe blocks. Expected failures (`fails`) and tests that
    passed only after a retry are FAIL, as in the Playwright parser."""
    results, untagged = [], 0
    for test in json.loads(text).get("tests", []):
        tc = tcnames.title_tc(str(test.get("title", "")))
        if not tc:
            untagged += 1
            continue
        state = test.get("state")
        if state == "skipped":
            status = "SKIP"
        elif state == "passed" and not test.get("fails") and not test.get("flaky"):
            status = "PASS"
        else:  # failed, pending, `fails`, or flaky
            status = "FAIL"
        results.append(TestResult(tc, str(test.get("fullName", "")), status))
    return results, untagged


def merge(collected: list[tuple[TestResult, tuple[str, str, str]]]) -> list[Evidence]:
    """One row per TC: FAIL if any test failed, else PASS if any passed, else SKIP."""
    by_tc: dict[str, Evidence] = {}
    for result, source in collected:
        evidence = by_tc.setdefault(result.tc, Evidence(result.tc, "SKIP"))
        if ORDER[result.status] < ORDER[evidence.status]:
            evidence.status = result.status
        evidence.names.append(f"{result.name} {result.status}")
        if source not in evidence.sources:
            evidence.sources.append(source)
    return sorted(by_tc.values(), key=lambda e: int(e.tc.split("-")[1]))


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_rows(evidence: list[Evidence], sha: str) -> str:
    rows = []
    for item in evidence:
        times = ", ".join(
            f"{time} · GitHub Actions {workflow}" for workflow, _, time in item.sources
        )
        links = " ".join(url for _, url, _ in item.sources)
        rows.append(
            f"| {item.tc} | {sha} | {_cell(times)} | {_cell('; '.join(item.names))} | {item.status} | {links} |"
        )
    return "\n".join(rows)


def _gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def latest_runs(repo: str, sha: str) -> dict[str, dict]:
    pages = json.loads(
        _gh(
            "api",
            "--paginate",
            "--slurp",
            f"repos/{repo}/actions/runs?head_sha={sha}&per_page=100",
        )
    )
    latest: dict[str, dict] = {}
    for run in (r for page in pages for r in page["workflow_runs"]):
        name = run.get("name", "")
        if name not in latest or run["id"] > latest[name]["id"]:
            latest[name] = run
    return latest


def collect(repo: str, sha: str) -> tuple[list[Evidence], list[str]]:
    runs = latest_runs(repo, sha)
    collected: list[tuple[TestResult, tuple[str, str, str]]] = []
    warnings: list[str] = []
    for workflow, artifact, filename, kind in SOURCES:
        run = runs.get(workflow)
        if run is None:
            warnings.append(f"{workflow}: 이 커밋의 실행이 없습니다")
            continue
        if run.get("status") != "completed":
            warnings.append(f"{workflow}: 아직 실행 중입니다 ({run['html_url']})")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                _gh(
                    "run",
                    "download",
                    str(run["id"]),
                    "-R",
                    repo,
                    "-n",
                    artifact,
                    "-D",
                    tmp,
                )
            except subprocess.CalledProcessError:
                warnings.append(
                    f"{workflow}: '{artifact}' 결과 파일이 없습니다 ({run['html_url']})"
                )
                continue
            report = Path(tmp) / filename
            if not report.is_file():
                warnings.append(f"{workflow}: {artifact} 안에 {filename}이 없습니다")
                continue
            parse = {
                "junit": parse_junit,
                "playwright": parse_playwright,
                "vitest": parse_vitest,
            }[kind]
            results, untagged = parse(report.read_text(encoding="utf-8"))
        if untagged:
            warnings.append(
                f"{workflow}: TC ID가 없는 테스트 {untagged}개는 집계하지 않았습니다"
            )
        source = (workflow, run["html_url"], run["created_at"])
        collected.extend((result, source) for result in results)
    return merge(collected), warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--sha", required=True, help="full 40-character commit SHA the CI ran on"
    )
    parser.add_argument(
        "--repo", help="owner/repo (default: the current gh repository)"
    )
    args = parser.parse_args()

    if not SHA40.match(args.sha):
        parser.error("--sha must be the full 40-character commit SHA")
    repo = (
        args.repo
        or _gh(
            "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        ).strip()
    )
    evidence, warnings = collect(repo, args.sha)
    for warning in warnings:
        print(f"주의: {warning}", file=sys.stderr)
    if not evidence:
        print("TC 결과를 찾지 못했습니다. 아무것도 기록하지 마세요.", file=sys.stderr)
        return 1
    print(
        "| TC | 소스 SHA | 실행 시각·환경 | 실제 결과 | 상태 | 로그·화면 등 근거 경로 |"
    )
    print("|---|---|---|---|---|---|")
    print(render_rows(evidence, args.sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
