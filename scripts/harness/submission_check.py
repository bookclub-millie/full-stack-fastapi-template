#!/usr/bin/env python3
"""Pre-submission checklist for one commit (the SHA you will submit to the portal).

    python3 -I scripts/harness/submission_check.py --sha <40-char SHA> [--github owner/repo]

Reads the commit from git only. With --github it also asks the `gh` CLI for the
commit's check results and the openspec Issue counts. Prints a Markdown
checklist and exits 1 when an item is ❌. See docs/adr/001-openspec-docs-traceability.md.
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


class Repo:
    def __init__(self, path: str) -> None:
        self.path = path

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", self.path, *args], check=True, capture_output=True, text=True
        ).stdout

    def show(self, sha: str, path: str) -> str | None:
        try:
            return self.git("show", f"{sha}:{path}")
        except subprocess.CalledProcessError:
            return None


def _gh_json(*args: str) -> object:
    out = subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout
    return json.loads(out)


def evaluate(repo: Repo, sha: str) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    try:
        repo.git("rev-parse", "--verify", "--end-of-options", f"{sha}^{{commit}}")
    except subprocess.CalledProcessError:
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

    empty = [
        path
        for path in DOCS[1:]
        if texts[path] is not None
        and not any(filled(r) >= 2 for r in all_rows(texts[path]))
    ]
    items.append(
        (
            "문서 작성",
            WARN if empty else OK,
            "표가 비어 있음(템플릿 그대로): " + ", ".join(empty)
            if empty
            else "모든 문서 표에 내용이 있음",
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
    unsupported = traceability.unsupported_completions(docs)
    required = [
        r
        for r in table(texts[traceability.PRD], "요구사항 추적표")
        if "필수" in cell(r, "우선순위")
    ]
    not_done = [
        cell(r, "REQ") or "?"
        for r in required
        if not ("완료" in cell(r, "상태") and "미완료" not in cell(r, "상태"))
    ]
    if unsupported:
        items.append(("필수 REQ 근거", FAIL, " / ".join(unsupported)))
    elif not required:
        items.append(("필수 REQ 근거", WARN, "prd.md 추적표에 필수 REQ가 없습니다"))
    else:
        detail = f"필수 {len(required)}개 중 완료 {len(required) - len(not_done)}개"
        items.append(
            (
                "필수 REQ 근거",
                WARN if not_done else OK,
                detail + (f", 미완료: {', '.join(not_done)}" if not_done else ""),
            )
        )

    results = table(texts[traceability.E2E], "실행 결과")
    with_sha = [r for r in results if traceability.SHA40.search(cell(r, "소스 SHA"))]
    at_sha = [r for r in with_sha if sha in cell(r, "소스 SHA")]
    items.append(
        (
            "시험 결과",
            OK if with_sha else WARN,
            f"실행 결과 {len(results)}행, SHA 있음 {len(with_sha)}행, 제출 SHA와 같은 행 {len(at_sha)}행",
        )
    )

    listed = repo.git(
        "ls-tree", "-r", "--name-only", sha, "--", openspec.CHANGES_DIR
    ).splitlines()
    files = {
        p: t
        for p in listed
        if p.endswith(".md") and (t := repo.show(sha, p)) is not None
    }
    changes = openspec.changes_from_files(files)
    archived = {c.id for c in changes if c.archived}
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
    active = [c.id for c in changes if not c.archived]
    items.append(
        (
            "OpenSpec",
            WARN if active else OK,
            f"archive 안 된 변경: {', '.join(active)}"
            if active
            else "진행 중인 변경 없음",
        )
    )

    policy = texts[SECURITY_POLICY]
    unverified = sum(
        1
        for r in table(texts["docs/security-compliance.md"], "적용·검증 결과")
        if "미검증" in cell(r, "상태")
    )
    items.append(
        (
            "보안",
            WARN if policy is None or unverified else OK,
            ("docs/security-policy.md 없음(주최 측 제공). " if policy is None else "")
            + f"security-compliance.md 미검증 {unverified}개",
        )
    )
    return items


def evaluate_github(repo_name: str, sha: str) -> list[tuple[str, str, str]]:
    items = []
    runs = _gh_json("api", f"repos/{repo_name}/commits/{sha}/check-runs?per_page=100")[
        "check_runs"
    ]
    bad = sorted(
        {
            r["name"]
            for r in runs
            if r.get("conclusion") not in ("success", "skipped", "neutral")
        }
    )
    items.append(
        (
            "CI 검사",
            FAIL if bad else (OK if runs else WARN),
            "성공 아님: " + ", ".join(bad)
            if bad
            else f"{len(runs)}개 확인"
            if runs
            else "이 커밋의 검사가 없습니다",
        )
    )
    issues = _gh_json(
        "api",
        "--paginate",
        "--slurp",
        f"repos/{repo_name}/issues?labels=openspec&state=all&per_page=100",
    )
    flat = [i for page in issues for i in page if "pull_request" not in i]
    open_count = sum(1 for i in flat if i["state"] == "open")
    completed = sum(1 for i in flat if i.get("state_reason") == "completed")
    items.append(
        (
            "Issue",
            WARN if open_count else OK,
            f"openspec Issue {len(flat)}개: 열림 {open_count}, completed {completed}",
        )
    )
    return items


def render(sha: str, items: list[tuple[str, str, str]]) -> str:
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
    args = parser.parse_args()
    if not SHA40.match(args.sha):
        print(render(args.sha, [("소스 SHA", FAIL, "전체 40자 커밋 SHA가 아닙니다")]))
        return 1
    items = evaluate(Repo(args.repo), args.sha)
    if args.github:
        items += evaluate_github(args.github, args.sha)
    print(render(args.sha, items))
    return 1 if any(mark == FAIL for _, mark, _ in items) else 0


if __name__ == "__main__":
    sys.exit(main())
