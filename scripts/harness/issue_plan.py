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


def added_commits(repo: Path) -> dict[str, tuple[str, str]]:
    """Latest (sha, ISO date) that added each file under openspec/changes; renames count as adds.

    One history walk for all changes instead of one per file.
    """
    try:
        out = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "log",
                "--no-renames",
                "--diff-filter=A",
                "--format=commit %H %cI",
                "--name-only",
                "--",
                openspec.CHANGES_DIR,
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except subprocess.CalledProcessError:
        return {}
    latest: dict[str, tuple[str, str]] = {}
    commit = ("", "")
    for line in out.splitlines():
        if line.startswith("commit "):
            _, sha, date = line.split()
            commit = (sha, date)
        elif line and line not in latest:  # git log lists newest first
            latest[line] = commit
    return latest


def render(change: openspec.Change, repo_url: str, branch: str) -> dict:
    proposal = change.proposal
    name = proposal.title or change.id
    prefix = ", ".join(proposal.requirements) or "OpenSpec"
    criteria = [f"{s.id} {s.name}" if s.id else s.name for s in change.scenarios]
    criteria.append(TEST_RESULT_ITEM)
    done, total = change.tasks

    # No @mention: an unchecked name could ping an unrelated GitHub user.
    # The sync assigns the Issue when the login is assignable.
    owner = (
        f"`{proposal.owner}`"
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
        "owner": proposal.owner,
    }


def plan(repo: Path, repo_url: str, branch: str) -> list[dict]:
    changes: dict[str, openspec.Change] = {}
    for change in openspec.load_changes(repo):
        # Same id twice: an active change (re-proposal) wins, then the latest archive.
        kept = changes.get(change.id)
        if (
            kept is None
            or not change.archived
            or (kept.archived and change.path > kept.path)
        ):
            changes[change.id] = change
    added = added_commits(repo)
    planned = []
    for change in changes.values():
        item = render(change, repo_url, branch)
        none = (None, None)
        proposal = added.get(f"{openspec.CHANGES_DIR}/{change.id}/proposal.md", none)
        item["proposal_commit"], item["proposal_date"] = proposal
        archive = (
            added.get(f"{change.path}/proposal.md", none) if change.archived else none
        )
        item["archive_commit"] = archive[0]
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
