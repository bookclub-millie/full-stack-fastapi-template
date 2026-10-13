#!/usr/bin/env python3
"""Print the next free REQ·AC·FLOW·TC numbers before you write a proposal.

    python3 -I scripts/harness/next_ids.py [--github] [--base origin/master] [--no-fetch]

Numbers in use come from the tables of docs/prd.md, docs/e2e-test.md and
docs/experience.md and from OpenSpec files (openspec/changes/**, openspec/specs/**),
in the working tree and on the base branch (fetched first). With --github it
also reads the lines that open pull requests add to those files, so proposals in
flight do not pick the same numbers. The numbers are claimed once the proposal
PR (its spec and tasks.md) is merged; the Harness Gate fails a PR whose new
numbers another change already claims. See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import idregistry
from doctables import all_rows

DEFAULT_BASES = ("origin/HEAD", "origin/master", "origin/main")
SPEC_DIRS = ("openspec/changes", "openspec/specs")
# A number this large in someone's open PR is a typo, not a claim to skip past.
MAX_FROM_PRS = 999


def _run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},  # never wait for a password
    ).stdout


def _ids_in_docs(texts: dict[str, str | None]) -> set[str]:
    """Ids in any table row of the registry docs (not in their prose examples)."""
    return {
        identifier
        for text in texts.values()
        for row in all_rows(text)
        for value in row.values()
        for identifier in idregistry.ids_in(value)
    }


def from_worktree(root: Path) -> set[str]:
    docs = {
        path: (root / path).read_text(encoding="utf-8", errors="replace")
        for path in idregistry.DOCS
        if (root / path).is_file()
    }
    used = _ids_in_docs(docs)
    for directory in SPEC_DIRS:
        for file in (root / directory).rglob("*.md"):
            used |= idregistry.ids_in(
                file.read_text(encoding="utf-8", errors="replace")
            )
    return used


def from_ref(root: Path, ref: str) -> set[str]:
    def show(path: str) -> str | None:
        try:
            return _run("git", "show", f"{ref}:{path}", cwd=root)
        except subprocess.CalledProcessError:
            return None

    used = _ids_in_docs({path: show(path) for path in idregistry.DOCS})
    listed = _run(
        "git", "ls-tree", "-r", "-z", "--name-only", ref, "--", *SPEC_DIRS, cwd=root
    )
    for path in filter(None, listed.split("\0")):
        if path.endswith(".md"):
            used |= idregistry.ids_in(show(path))
    return used


def from_open_prs(root: Path) -> tuple[set[str], int, list[str]]:
    """Ids on lines that open PRs add to the registry docs and OpenSpec files.

    Returns (ids, number of open PRs, warnings).
    """
    repo = _run(
        "gh",
        "repo",
        "view",
        "--json",
        "nameWithOwner",
        "--jq",
        ".nameWithOwner",
        cwd=root,
    ).strip()
    numbers = json.loads(
        _run(
            "gh",
            "pr",
            "list",
            "-R",
            repo,
            "--state",
            "open",
            "--limit",
            "1000",
            "--json",
            "number",
            cwd=root,
        )
    )
    used: set[str] = set()
    warnings: list[str] = []
    for pr in numbers:
        pages = json.loads(
            _run(
                "gh",
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repo}/pulls/{pr['number']}/files?per_page=100",
                cwd=root,
            )
        )
        for file in (f for page in pages for f in page):
            name = file.get("filename", "")
            if not (name in idregistry.DOCS or name.startswith(SPEC_DIRS)):
                continue
            if "patch" not in file:
                warnings.append(
                    f"PR #{pr['number']} {name}: diff가 커서 읽지 못했습니다"
                )
                continue
            added = "\n".join(
                line[1:]
                for line in file["patch"].splitlines()
                if line.startswith("+") and not line.startswith("+++")
            )
            for identifier in idregistry.ids_in(added):
                if int(identifier.split("-")[1]) > MAX_FROM_PRS:
                    warnings.append(f"PR #{pr['number']} {name}: {identifier} 무시함")
                else:
                    used.add(identifier)
    return used, len(numbers), warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repo", default=".", help="any directory in the checkout")
    parser.add_argument(
        "--base", help="base branch (default: origin/HEAD, origin/master, origin/main)"
    )
    parser.add_argument(
        "--no-fetch", action="store_true", help="do not run git fetch first"
    )
    parser.add_argument(
        "--github", action="store_true", help="also avoid numbers in open PRs (gh)"
    )
    args = parser.parse_args()

    try:
        root = Path(
            _run("git", "rev-parse", "--show-toplevel", cwd=Path(args.repo)).strip()
        )
    except (subprocess.CalledProcessError, OSError):
        print(f"git 저장소가 아닙니다: {args.repo}", file=sys.stderr)
        return 2

    sources = ["작업 트리"]
    used = from_worktree(root)
    if not args.no_fetch:
        try:
            _run("git", "fetch", "--quiet", "origin", cwd=root)
        except (subprocess.CalledProcessError, OSError):
            print(
                "주의: git fetch에 실패해 로컬에 있는 기준 브랜치로 계산합니다.",
                file=sys.stderr,
            )
    for ref in (args.base,) if args.base else DEFAULT_BASES:
        try:
            commit = _run(
                "git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", cwd=root
            ).strip()
        except subprocess.CalledProcessError:
            continue
        used |= from_ref(root, commit)
        sources.append(ref)
        break
    else:
        print("주의: 기준 브랜치를 찾지 못해 작업 트리만 봤습니다.", file=sys.stderr)
    if args.github:
        try:
            in_prs, count, warnings = from_open_prs(root)
        except (subprocess.CalledProcessError, OSError, ValueError) as error:
            print(
                f"주의: 열린 PR을 읽지 못해 빼고 계산했습니다(gh 설치·로그인 확인): {error}",
                file=sys.stderr,
            )
        else:
            used |= in_prs
            sources.append(f"열린 PR {count}개")
            for warning in warnings:
                print(f"주의: {warning}", file=sys.stderr)

    nexts = idregistry.next_free(used)
    print("다음 빈 번호: " + "  ".join(nexts[kind] for kind in idregistry.KINDS))
    print(f"(확인한 곳: {', '.join(sources)})")
    print(
        "여러 개가 필요하면 이어서 씁니다(예: REQ-04, REQ-05). 제안 PR(spec·tasks.md)이 "
        "머지되면 번호가 확정되고, 그 전에 다른 제안이 먼저 머지되면 게이트가 알려 줍니다."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
