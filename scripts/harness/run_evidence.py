#!/usr/bin/env python3
"""Run every test workflow on one commit and print its docs/e2e-test.md rows.

    python3 scripts/harness/run_evidence.py [--ref master] [--repo owner/repo] [--timeout 45]

Pushes and pull requests only run the tests their changed files need, so a
docs-only commit (often the one you submit) can lack E2E or vitest results.
This dispatches Test Backend, Playwright Tests and Frontend Quality on `ref`
(a manual run tests everything), waits for them, and then prints the rows of
collect_evidence.py for that commit. Needs `gh` logged in with write access.
See docs/ci-harness.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_evidence

WORKFLOWS = ("test-backend.yml", "playwright.yml", "frontend-quality.yml")
POLL_SECONDS = 20


def _gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout


def _runs(repo: str, workflow: str) -> list[dict]:
    """Recent manual runs of `workflow`, newest first."""
    return json.loads(
        _gh(
            "run",
            "list",
            "-R",
            repo,
            "--workflow",
            workflow,
            "--event",
            "workflow_dispatch",
            "--limit",
            "20",
            "--json",
            "databaseId,headSha,status,conclusion,url",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ref", default="master", help="branch or tag to test")
    parser.add_argument(
        "--repo", help="owner/repo (default: the current gh repository)"
    )
    parser.add_argument("--timeout", type=int, default=45, help="minutes to wait")
    args = parser.parse_args()

    repo = (
        args.repo
        or _gh(
            "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        ).strip()
    )
    sha = _gh("api", f"repos/{repo}/commits/{args.ref}", "--jq", ".sha").strip()
    print(f"{args.ref} = {sha}: 시험 워크플로 {len(WORKFLOWS)}개를 수동 실행합니다.")
    # Runs are recognized by id, not by time: a newer id than any run seen before.
    seen = {
        w: max((r["databaseId"] for r in _runs(repo, w)), default=0) for w in WORKFLOWS
    }
    for workflow in WORKFLOWS:
        _gh("workflow", "run", workflow, "-R", repo, "--ref", args.ref)

    deadline = time.monotonic() + args.timeout * 60
    runs: dict[str, dict | None] = dict.fromkeys(WORKFLOWS)
    while time.monotonic() < deadline:
        for workflow in WORKFLOWS:
            run = runs[workflow]
            if run is None or run["status"] != "completed":
                new = [
                    r for r in _runs(repo, workflow) if r["databaseId"] > seen[workflow]
                ]
                runs[workflow] = new[-1] if new else None  # the oldest new run is ours
        moved = [r for r in runs.values() if r and r["headSha"] != sha]
        if moved:
            print(
                f"{args.ref}가 {sha[:12]}에서 {moved[0]['headSha'][:12]}로 바뀌어 다른 커밋을 "
                "시험하고 있습니다. 다시 실행하세요",
                file=sys.stderr,
            )
            return 1
        if all(run and run["status"] == "completed" for run in runs.values()):
            break
        time.sleep(POLL_SECONDS)

    ok = True
    for workflow, run in runs.items():
        if run is None:
            ok = False
            print(f"{workflow}: 수동 실행을 찾지 못했습니다", file=sys.stderr)
        elif run["status"] != "completed":
            ok = False
            print(
                f"{workflow}: {args.timeout}분 안에 끝나지 않았습니다 ({run['url']})",
                file=sys.stderr,
            )
        else:
            ok &= run["conclusion"] == "success"
            print(f"{workflow}: {run['conclusion']} ({run['url']})")

    evidence, warnings = collect_evidence.collect(repo, sha)
    for warning in warnings:
        print(f"주의: {warning}", file=sys.stderr)
    if not evidence:
        print("TC 결과를 찾지 못했습니다. 아무것도 기록하지 마세요.", file=sys.stderr)
        return 1
    print(
        "\n| TC | 소스 SHA | 실행 시각·환경 | 실제 결과 | 상태 | 로그·화면 등 근거 경로 |"
    )
    print("|---|---|---|---|---|---|")
    print(collect_evidence.render_rows(evidence, sha))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
