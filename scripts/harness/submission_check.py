#!/usr/bin/env python3
"""Pre-submission checklist for one commit (the SHA you will submit to the portal).

    python3 -I scripts/harness/submission_check.py --sha <40-char SHA> [--github owner/repo]

Reads the commit from git only. With --github it also asks the `gh` CLI for the
commit's check runs and commit statuses (Harness Gate) and the openspec Issue
counts. Prints a Markdown checklist and exits 1 when an item is ❌.
See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tc_check
import tcnames
import traceability
from doctables import all_rows, cell, filled, table

import openspec

DOCS = (
    "README.md",
    "docs/project-brief.md",
    "docs/prd.md",
    "docs/arch.md",
    "docs/experience.md",
    "docs/development.md",
    "docs/security-compliance.md",
    "docs/e2e-test.md",
)
SECURITY_POLICY = "docs/security-policy.md"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
OK, WARN, FAIL = "✅", "⚠️", "❌"
PASSING_CONCLUSIONS = {"success", "skipped", "neutral"}

Item = tuple[str, str, str]


class Repo:
    def __init__(self, path: str) -> None:
        self.path = path

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", self.path, *args], check=True, capture_output=True, text=True
        ).stdout

    def ok(self, *args: str) -> bool:
        return (
            subprocess.run(
                ["git", "-C", self.path, *args], capture_output=True, check=False
            ).returncode
            == 0
        )

    def exists(self, sha: str) -> bool:
        return self.ok("cat-file", "-e", f"{sha}^{{commit}}")

    def show(self, sha: str, path: str) -> str | None:
        try:
            return self.git("show", f"{sha}:{path}")
        except subprocess.CalledProcessError:
            return None

    def unchanged_since_first_commit(self, sha: str, path: str) -> bool:
        """True when `path` is exactly as in a root commit (a repo made from the template)."""
        roots = self.git("rev-list", "--max-parents=0", sha).split()
        return any(
            self.show(root, path) is not None
            and self.ok("diff", "--quiet", root, sha, "--", path)
            for root in roots
        )


def _gh_json(*args: str) -> object:
    out = subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout
    return json.loads(out)


def evaluate(repo: Repo, sha: str) -> list[Item]:
    items: list[Item] = []
    if not repo.exists(sha):
        return [("소스 SHA", FAIL, f"`{sha}` 커밋이 저장소에 없습니다")]
    items.append(("소스 SHA", OK, f"`{sha}` — 포털에는 이 40자 SHA를 입력합니다"))

    texts = {path: repo.show(sha, path) for path in (*DOCS, SECURITY_POLICY)}
    missing = [path for path in DOCS if texts[path] is None]
    items.append(
        (
            "문서 8개",
            FAIL if missing else OK,
            "없음: " + ", ".join(missing) if missing else "모두 있음",
        )
    )

    untouched = [
        path
        for path in DOCS[1:]
        if texts[path] is not None
        and (
            repo.unchanged_since_first_commit(sha, path)
            or not any(filled(r) >= 2 for r in all_rows(texts[path]))
        )
    ]
    items.append(
        (
            "문서 작성",
            WARN if untouched else OK,
            "템플릿 그대로이거나 표가 비어 있음: " + ", ".join(untouched)
            if untouched
            else "모든 문서를 작성함",
        )
    )

    readme = texts["README.md"] or ""
    index = repo.show(sha, "docs/README.md") or ""
    unlinked = [
        path
        for path in DOCS[1:]
        if path not in readme
        and not ("docs/README.md" in readme and Path(path).name in index)
    ]
    items.append(
        (
            "README 연결",
            WARN if unlinked else OK,
            "README에서 닿지 않음: " + ", ".join(unlinked)
            if unlinked
            else "README에서 문서 7개로 연결됨",
        )
    )

    docs = {
        path: texts[path]
        for path in (traceability.PRD, traceability.E2E, traceability.DEV)
    }
    unsupported = traceability.unsupported_completions(docs, repo.exists)
    required = [
        r
        for r in table(texts[traceability.PRD], "요구사항 추적표")
        if "필수" in cell(r, "우선순위")
    ]
    not_done = [
        cell(r, "REQ") or "?"
        for r in required
        if not traceability.is_done(cell(r, "상태"))
    ]
    if unsupported:
        items.append(("필수 REQ 근거", FAIL, " / ".join(unsupported)))
    elif not required:
        items.append(("필수 REQ 근거", WARN, "prd.md 추적표에 필수 REQ가 없습니다"))
    else:
        detail = f"필수 {len(required)}개 중 완료 {len(required) - len(not_done)}개"
        if not_done:
            detail += f", 미완료: {', '.join(not_done)}"
        items.append(("필수 REQ 근거", WARN if not_done else OK, detail))

    results = table(texts[traceability.E2E], "실행 결과")
    with_sha = [r for r in results if traceability.SHA40.search(cell(r, "소스 SHA"))]
    at_sha = [r for r in with_sha if sha in cell(r, "소스 SHA")]
    # The latest result of each TC should be from a commit with the submitted code:
    # only docs and OpenSpec may differ between them.
    latest: dict[str, str] = {}
    for row in with_sha:
        found = traceability.SHA40.search(cell(row, "소스 SHA"))
        for tc in tcnames.ids(cell(row, "TC")):
            latest[tc] = found.group() if found else ""
    same_code: dict[str, bool] = {}
    for evidence_sha in set(latest.values()):
        same_code[evidence_sha] = repo.exists(evidence_sha) and repo.ok(
            "diff",
            "--quiet",
            evidence_sha,
            sha,
            "--",
            ".",
            ":(exclude)docs",
            ":(exclude)README.md",
            ":(exclude)openspec",
        )
    stale = sorted(
        tc for tc, evidence_sha in latest.items() if not same_code[evidence_sha]
    )
    detail = f"실행 결과 {len(results)}행, SHA 있음 {len(with_sha)}행, 제출 SHA와 같은 행 {len(at_sha)}행"
    if stale:
        shown = ", ".join(stale[:5]) + (
            f" 외 {len(stale) - 5}개" if len(stale) > 5 else ""
        )
        detail += (
            f". 최신 결과 이후 코드가 바뀐 TC: {shown} "
            "(`python3 scripts/harness/run_evidence.py`로 제출 커밋의 결과를 다시 만드세요)"
        )
    items.append(("시험 결과", OK if with_sha and not stale else WARN, detail))

    # Change ids only: which changes exist and whether they are archived.
    listed = repo.git(
        "ls-tree", "-r", "-z", "--name-only", sha, "--", openspec.CHANGES_DIR
    ).split("\0")
    changes = {
        found
        for path in listed
        if path.endswith("/proposal.md") and (found := openspec.locate(path))
    }
    archived = {change_id for _, change_id, is_archive in changes if is_archive}
    active = sorted(
        {change_id for _, change_id, is_archive in changes if not is_archive}
    )
    failures, _ = traceability.check(
        docs, [], archived=archived, touched=set(), claims_changed=False
    )
    items.append(
        (
            "development.md 기록",
            WARN if failures else OK,
            " / ".join(failures)
            if failures
            else f"archive된 변경 {len(archived)}개 모두 기록됨",
        )
    )
    items.append(
        (
            "OpenSpec",
            WARN if active else OK,
            f"archive 안 된 변경: {', '.join(active)}"
            if active
            else "진행 중인 변경 없음",
        )
    )

    tests = {
        path: text
        for path in repo.git(
            "ls-tree", "-r", "-z", "--name-only", sha, "--", *tcnames.SCAN_ROOTS
        ).split("\0")
        if tcnames.is_test_file(path) and (text := repo.show(sha, path)) is not None
    }
    change_files = {
        path: text
        for path in listed
        if path.endswith(".md") and (text := repo.show(sha, path)) is not None
    }
    tc_failures, _ = tc_check.strict(
        texts[traceability.E2E], tests, openspec.changes_from_files(change_files)
    )
    shown = " / ".join(tc_failures[:5])
    if len(tc_failures) > 5:
        shown += f" 외 {len(tc_failures) - 5}건"
    items.append(
        (
            "TC 연결",
            WARN if tc_failures else OK,
            shown
            or "테스트 이름의 TC가 시나리오와 이어지고, archive된 변경의 AC마다 TC 테스트가 있음",
        )
    )

    unverified = sum(
        1
        for r in table(texts["docs/security-compliance.md"], "적용·검증 결과")
        if "미검증" in cell(r, "상태")
    )
    policy_missing = texts[SECURITY_POLICY] is None
    items.append(
        (
            "보안",
            WARN if policy_missing or unverified else OK,
            ("docs/security-policy.md 없음(주최 측 제공). " if policy_missing else "")
            + f"security-compliance.md 미검증 {unverified}개",
        )
    )
    return items


def evaluate_github(
    repo_name: str, sha: str, ignore: frozenset[str] = frozenset()
) -> list[Item]:
    pages = _gh_json(
        "api",
        "--paginate",
        "--slurp",
        f"repos/{repo_name}/commits/{sha}/check-runs?per_page=100",
    )
    latest: dict[str, dict] = {}
    for run in (r for page in pages for r in page["check_runs"]):
        if run["name"] not in ignore and (
            run["name"] not in latest or run["id"] > latest[run["name"]]["id"]
        ):
            latest[run["name"]] = run
    failed = [
        n
        for n, r in latest.items()
        if r["status"] == "completed" and r.get("conclusion") not in PASSING_CONCLUSIONS
    ]
    running = [n for n, r in latest.items() if r["status"] != "completed"]
    # Harness Gate reports harness/checks and harness/ack as commit statuses.
    statuses = _gh_json(
        "api", f"repos/{repo_name}/commits/{sha}/status?per_page=100"
    ).get("statuses", [])
    failed += [s["context"] for s in statuses if s["state"] in ("failure", "error")]
    running += [s["context"] for s in statuses if s["state"] == "pending"]
    if failed:
        ci = (FAIL, "성공 아님: " + ", ".join(sorted(failed)))
    elif running:
        ci = (WARN, "진행 중: " + ", ".join(sorted(running)))
    elif latest or statuses:
        ci = (OK, f"검사 {len(latest)}개·상태 {len(statuses)}개 모두 통과")
    else:
        ci = (WARN, "이 커밋의 검사 결과가 없습니다")
    items = [("CI 검사", *ci)]

    issue_pages = _gh_json(
        "api",
        "--paginate",
        "--slurp",
        f"repos/{repo_name}/issues?labels=openspec&state=all&per_page=100",
    )
    issues = [i for page in issue_pages for i in page if "pull_request" not in i]
    open_count = sum(1 for i in issues if i["state"] == "open")
    completed = sum(1 for i in issues if i.get("state_reason") == "completed")
    items.append(
        (
            "Issue",
            WARN if open_count else OK,
            f"openspec Issue {len(issues)}개: 열림 {open_count}, completed {completed}",
        )
    )
    return items


def render(sha: str, items: list[Item]) -> str:
    lines = [
        f"## 제출 점검 — `{sha[:12]}`",
        "",
        "| 항목 | 결과 | 내용 |",
        "|---|---|---|",
    ]
    for name, mark, detail in items:
        escaped = detail.replace("|", "\\|")
        lines.append(f"| {name} | {mark} | {escaped} |")
    lines += ["", "❌는 제출 전에 고쳐야 하고, ⚠️는 확인이 필요한 항목입니다."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument(
        "--sha", required=True, help="full 40-character commit SHA to submit"
    )
    parser.add_argument(
        "--github",
        metavar="OWNER/REPO",
        help="also check CI results and Issues with gh",
    )
    parser.add_argument(
        "--ignore-check",
        action="append",
        default=[],
        help="check run to skip (this job itself)",
    )
    args = parser.parse_args()
    if not SHA40.match(args.sha):
        print(render(args.sha, [("소스 SHA", FAIL, "전체 40자 커밋 SHA가 아닙니다")]))
        return 1
    items = evaluate(Repo(args.repo), args.sha)
    if args.github:
        items += evaluate_github(args.github, args.sha, frozenset(args.ignore_check))
    print(render(args.sha, items))
    return 1 if any(mark == FAIL for _, mark, _ in items) else 0


if __name__ == "__main__":
    sys.exit(main())
