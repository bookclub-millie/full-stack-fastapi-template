#!/usr/bin/env python3
"""Plan one GitHub Issue per OpenSpec change, in the 개발 작업·검증 format.

Reads the checkout and its git history only (no token, no network) and writes
JSON for the OpenSpec Issues workflow, which applies it with the GitHub API.
See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import openspec

MARKER = "<!-- openspec-change: {id} -->"
TEST_RESULT_ITEM = "정상·오류 테스트 결과를 남긴다"


def first_added(repo: Path, path: str) -> str | None:
    """Commit that first added `path` (renames count as adds)."""
    try:
        out = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "log",
                "--no-renames",
                "--diff-filter=A",
                "--format=%H",
                "--",
                path,
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
    except subprocess.CalledProcessError:
        return None
    return out[-1] if out else None


def render(change: openspec.Change, repo_url: str, branch: str) -> dict:
    proposal = change.proposal
    name = proposal.title or change.id
    prefix = ", ".join(proposal.requirements) or "OpenSpec"
    criteria = [f"{s.id} {s.name}" if s.id else s.name for s in change.scenarios]
    criteria.append(TEST_RESULT_ITEM)
    done, total = change.tasks

    owner = (
        f"@{proposal.owner}"
        if proposal.owner
        else "(proposal.md에 `담당:` 줄이 없습니다)"
    )
    requirements = (
        ", ".join(f"docs/prd.md의 {req}" for req in proposal.requirements)
        if proposal.requirements
        else "(proposal.md에 `요구사항:` 줄이 없습니다)"
    )
    link = f"[{change.path}]({repo_url}/tree/{branch}/{change.path})"
    lines = [
        MARKER.format(id=change.id),
        "## 목적",
        proposal.why or "(proposal.md의 Why가 비어 있습니다)",
        "",
        "## 완료 조건",
        *(f"- [ ] {item}" for item in criteria),
        "",
        "## 담당자 / 연결 문서",
        f"담당: {owner}",
        f"요구사항: {requirements}",
        f"OpenSpec: {link} (작업 {done}/{total})",
    ]
    if proposal.scope:
        lines.append(f"범위: {proposal.scope}")
    return {
        "id": change.id,
        "archived": change.archived,
        "path": change.path,
        "title": f"[{prefix}] {name}",
        "managed": "\n".join(lines) + "\n",
        "criteria": criteria,
        "owner": proposal.owner,
    }


def plan(repo: Path, repo_url: str, branch: str) -> list[dict]:
    changes: dict[str, openspec.Change] = {}
    for change in openspec.load_changes(repo):
        # A re-proposed change keeps the id of an archived one; the active one wins.
        if change.id not in changes or not change.archived:
            changes[change.id] = change
    planned = []
    for change in changes.values():
        item = render(change, repo_url, branch)
        item["proposal_commit"] = first_added(
            repo, f"{openspec.CHANGES_DIR}/{change.id}/proposal.md"
        )
        item["archive_commit"] = (
            first_added(repo, f"{change.path}/proposal.md") if change.archived else None
        )
        planned.append(item)
    return planned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository checkout")
    parser.add_argument(
        "--repo-url", required=True, help="e.g. https://github.com/owner/repo"
    )
    parser.add_argument("--branch", required=True, help="branch the links point to")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    repo = Path(args.repo)
    result = {
        # Lets the workflow refuse to close every Issue when the OpenSpec folder is missing.
        "openspec_present": (repo / openspec.CHANGES_DIR).is_dir(),
        "changes": plan(repo, args.repo_url.rstrip("/"), args.branch),
    }
    Path(args.out).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
