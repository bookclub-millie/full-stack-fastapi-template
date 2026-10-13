#!/usr/bin/env python3
"""Check TC ids in test names against docs/e2e-test.md before you push.

    python3 -I scripts/harness/tc_check.py [--base origin/master]

Reads the tracked test files (`git add` new ones first) of the checkout as text;
no test is run. It applies the TC part of the Harness Gate's 문서 추적성 check
to every test file. Archives that are not on the base branch yet are treated as
archived by this change; older archives are only reported as notes, as the gate
does. The prek hook `tc-check` runs this. See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tcnames
import traceability

import openspec

DEFAULT_BASES = ("origin/HEAD", "origin/master", "origin/main")


def strict(
    e2e: str | None,
    tests: dict[str, str],
    changes: list[openspec.Change],
    archived: set[str] | None = None,
) -> tuple[list[str], dict[str, list[str]]]:
    """check_tests as if this change touched every test file.

    archived: changes treated as archived by this change (default: every archive).
    """
    return traceability.check_tests(
        {traceability.E2E: e2e},
        tests,
        changes,
        archived={c.id for c in changes if c.archived}
        if archived is None
        else archived,
        changed={*tests, traceability.E2E},
    )


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "-c", "core.quotePath=false", *args],
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    ).stdout


def _tracked_tests(root: Path) -> dict[str, str]:
    listed = _git(root, "ls-files", "-z", "--cached", "--", *tcnames.SCAN_ROOTS)
    tests: dict[str, str] = {}
    for path in filter(None, listed.split("\0")):
        file = root / path
        # The gate reads a committed symlink as its target path, not as a test.
        if tcnames.is_test_file(path) and file.is_file() and not file.is_symlink():
            tests[path] = file.read_text(encoding="utf-8", errors="replace")
    return tests


def _archives_on(root: Path, base: str | None) -> set[str] | None:
    """Archive directories present on `base`, or None when no base branch is found."""
    for ref in (base,) if base else DEFAULT_BASES:
        try:
            commit = _git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        except subprocess.CalledProcessError:
            continue
        listed = _git(
            root,
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            commit.strip(),
            "--",
            f"{openspec.CHANGES_DIR}/archive",
        )
        return {
            found[0] for path in listed.split("\0") if (found := openspec.locate(path))
        }
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repo", default=".", help="any directory in the checkout")
    parser.add_argument(
        "--base",
        help="branch the archives are compared with (default: origin/HEAD, origin/master, origin/main)",
    )
    args = parser.parse_args()

    try:
        root = Path(_git(Path(args.repo), "rev-parse", "--show-toplevel").strip())
    except (subprocess.CalledProcessError, OSError):
        print(f"git 저장소가 아닙니다: {args.repo}", file=sys.stderr)
        return 2
    e2e = root / traceability.E2E
    if not e2e.is_file():
        print(f"{traceability.E2E}가 없어 TC를 확인할 수 없습니다.", file=sys.stderr)
        return 2

    changes = openspec.load_changes(root)
    on_base = _archives_on(root, args.base)
    if on_base is None:
        print(
            "참고: 기준 브랜치를 찾지 못해 모든 archive를 이번 변경으로 보고 검사합니다."
        )
        archived = None
    else:
        archived = {c.id for c in changes if c.archived and c.path not in on_base}
    failures, notes = strict(
        e2e.read_text(encoding="utf-8"), _tracked_tests(root), changes, archived
    )
    for title, items in notes.items():
        print(f"참고: {title}")
        for item in items:
            print(f"  - {item}")
    for failure in failures:
        print(f"실패: {failure}")
    if failures:
        print(
            f"\nTC 연결 문제 {len(failures)}건. 형식: {tcnames.pytest_form()}, "
            f"{tcnames.title_form()}. 위치: {tcnames.LOCATIONS}. "
            f"테스트의 TC는 {traceability.E2E} 테스트 시나리오에 행이 있어야 합니다."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
