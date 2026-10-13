#!/usr/bin/env python3
"""Harness gate: analyze a PR as data and write a JSON + Markdown report.

The CI job runs this file from the trusted base-branch checkout with
``python3 -I``. It never executes code from the PR: it reads git objects from
the PR checkout, lockfiles, registry metadata and the reports of gitleaks and
zizmor (both run in network-less containers before this script).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

# -I drops the script directory from sys.path; add only this trusted directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lockfiles
import registry
import report
import signals
import traceability

import openspec

MIN_RELEASE_AGE = timedelta(days=7)
YOUNG_PACKAGE_AGE = timedelta(days=30)
DIFF_OPTIONS = ("--no-ext-diff", "--no-textconv", "--no-color", "-M")
LOOKUP_WORKERS = 8

Lookup = Callable[..., registry.Release]


class Git:
    def __init__(self, repo: str) -> None:
        self.repo = repo

    def run(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", self.repo, "-c", "core.quotePath=false", *args],
            check=True,
            capture_output=True,
            text=True,
            errors="replace",
        ).stdout

    def verify(self, rev: str) -> str:
        return self.run(
            "rev-parse", "--verify", "--end-of-options", f"{rev}^{{commit}}"
        ).strip()

    def exists(self, sha: str) -> bool:
        try:
            self.run("cat-file", "-e", f"{sha}^{{commit}}")
        except subprocess.CalledProcessError:
            return False
        return True

    def show(self, rev: str, path: str) -> str | None:
        try:
            return self.run("show", f"{rev}:{path}")
        except subprocess.CalledProcessError:
            return None


def _parse_hunks(patch: str) -> tuple[list[str], list[str]]:
    added: list[str] = []
    removed: list[str] = []
    in_hunk = False
    for line in patch.splitlines():
        if line.startswith("@@"):
            in_hunk = True
        elif in_hunk and line.startswith("+"):
            added.append(line[1:])
        elif in_hunk and line.startswith("-"):
            removed.append(line[1:])
    return added, removed


def collect_changes(git: Git, base: str, head: str) -> list[signals.FileChange]:
    tokens = git.run("diff", "--name-status", "-z", *DIFF_OPTIONS, base, head).split(
        "\0"
    )
    entries: list[tuple[str, str | None, str]] = []
    i = 0
    while i < len(tokens) and tokens[i]:
        code = tokens[i][0]
        if code in "RC":
            entries.append((code, tokens[i + 1], tokens[i + 2]))
            i += 3
        else:
            entries.append((code, None, tokens[i + 1]))
            i += 2

    # In a -U0 patch every content line starts with "+", "-" or "\\", so a line
    # starting with "diff --git " is always a file header.
    patch = git.run("diff", "-U0", *DIFF_OPTIONS, base, head)
    sections = re.split(r"^diff --git ", patch, flags=re.MULTILINE)[1:]
    if len(sections) != len(entries):
        # Unusual paths can break section alignment; fall back to one diff per file.
        sections = [
            git.run(
                "diff",
                "-U0",
                *DIFF_OPTIONS,
                base,
                head,
                "--",
                *filter(None, (old, new)),
            )
            for _, old, new in entries
        ]

    changes = []
    for (code, old, new), section in zip(entries, sections, strict=True):
        added, removed = _parse_hunks(section)
        change = signals.FileChange(
            path=new, status=code, old_path=old, added=added, removed=removed
        )
        if signals.wants_text(new) or signals.wants_text(old):
            change.base_text = None if code == "A" else git.show(base, old or new)
            change.head_text = None if code == "D" else git.show(head, new)
        changes.append(change)
    return changes


def _check(
    check_id: str, title: str, status: str, items: list[str], log: str = ""
) -> dict:
    return {
        "id": check_id,
        "title": title,
        "status": status,
        "items": items,
        "log": log,
    }


def check_secrets(exit_code: str, report_path: str | None) -> dict:
    title = "비밀값 스캔 (gitleaks)"
    if exit_code == "0":
        return _check("secrets", title, "pass", [])
    if exit_code == "3" and report_path:
        findings = json.loads(Path(report_path).read_text() or "[]")
        items = [
            f"{f['File']}:{f['StartLine']} {f['RuleID']} (commit {str(f['Commit'])[:7]})"
            for f in findings
        ]
        return _check(
            "secrets",
            title,
            "fail",
            items or ["gitleaks가 누출을 보고했지만 상세 결과가 비어 있습니다"],
        )
    return _check(
        "secrets",
        title,
        "fail",
        [f"gitleaks 실행 오류 (exit {exit_code}) — 확인할 수 없어 실패 처리"],
    )


def check_workflows(exit_code: str, log_path: str | None) -> dict:
    title = "워크플로 보안 (zizmor)"
    if exit_code == "skipped":
        return _check("workflows", title, "skip", [])
    log = Path(log_path).read_text(errors="replace") if log_path else ""
    if exit_code == "0":
        return _check("workflows", title, "pass", [])
    return _check("workflows", title, "fail", [f"zizmor exit {exit_code}"], log)


def check_supply_chain(
    git: Git, base: str, head: str, changed: set[str], now: datetime, lookup: Lookup
) -> tuple[dict, list[str]]:
    failures: list[str] = []
    young: list[str] = []
    bun_lock, uv_lock = git.show(head, "bun.lock"), git.show(head, "uv.lock")

    bun_age, bun_excluded = lockfiles.bun_cooldown(git.show(head, "bunfig.toml"))
    if bun_lock is not None and (bun_age is None or bun_age < MIN_RELEASE_AGE):
        failures.append(
            "bunfig.toml: [install] minimumReleaseAge 는 604800(7일) 이상이어야 합니다"
        )
    uv_span, uv_excluded = lockfiles.uv_cooldown(uv_lock)
    if uv_lock is not None and (uv_span is None or uv_span < MIN_RELEASE_AGE):
        failures.append(
            'uv.lock: exclude-newer-span 이 7일 이상이어야 합니다 ([tool.uv] exclude-newer = "7 days" 후 uv lock)'
        )

    added: list[lockfiles.Package] = []
    base_names: set[tuple[str, str]] = set()
    for path, parse in (
        ("bun.lock", lockfiles.parse_bun_lock),
        ("uv.lock", lockfiles.parse_uv_lock),
    ):
        if path not in changed:
            continue
        try:
            base_text, head_text = git.show(base, path), git.show(head, path)
            base_set = parse(base_text) if base_text else set()
            head_set = parse(head_text) if head_text else set()
        except ValueError as error:  # JSON and TOML decode errors
            failures.append(f"{path}: 파싱 실패 ({error})")
            continue
        base_names |= {(p.ecosystem, p.name) for p in base_set}
        for package in lockfiles.added_packages(base_set, head_set):
            if package.source == "other":
                failures.append(
                    f"{path}: {package.name}@{package.version} — 레지스트리 밖 소스 {package.detail}"
                )
            elif package.source == "registry":
                added.append(package)

    exempt = {("npm", name) for name in bun_excluded} | {
        ("pypi", name) for name in uv_excluded
    }

    def resolve(
        package: lockfiles.Package,
    ) -> tuple[lockfiles.Package, registry.Release | Exception]:
        try:
            return package, lookup(
                package, need_first=(package.ecosystem, package.name) not in base_names
            )
        except Exception as error:  # noqa: BLE001 -- any lookup problem fails the check (fail closed)
            return package, error

    with ThreadPoolExecutor(max_workers=LOOKUP_WORKERS) as pool:
        results = list(pool.map(resolve, added))

    for package, result in results:
        label = f"{package.ecosystem}:{package.name}@{package.version}"
        if isinstance(result, registry.NotFound):
            failures.append(f"{label} — 레지스트리에 없는 패키지 (이름 확인 필요)")
            continue
        if isinstance(result, Exception):
            failures.append(
                f"{label} — 레지스트리 조회 실패 ({type(result).__name__}), 확인할 수 없어 실패 처리"
            )
            continue
        if result.published is None:
            failures.append(f"{label} — 게시 시각을 확인할 수 없음")
        elif (
            now - result.published < MIN_RELEASE_AGE
            and (package.ecosystem, package.name) not in exempt
        ):
            days = (now - result.published).total_seconds() / 86400
            failures.append(f"{label} — 게시 {days:.1f}일 전 (7일 cooldown 미만)")
        if result.first_published and now - result.first_published < YOUNG_PACKAGE_AGE:
            young.append(f"{label}: 첫 등록 {(now - result.first_published).days}일 전")

    status = "fail" if failures else "pass"
    title = "공급망 (lockfile 출처·출시 7일 cooldown)"
    return _check("supply-chain", title, status, failures), young


def check_docs(
    git: Git, base: str, head: str, changes: list[signals.FileChange]
) -> tuple[dict, list[dict]]:
    """OpenSpec ↔ docs traceability (ADR-001): (check, notes)."""
    archived: set[str] = set()
    touched: set[str] = set()
    existed_at_base: dict[str, bool] = {}
    for change in changes:
        for path in filter(None, (change.path, change.old_path)):
            if (found := openspec.locate(path)) is None:
                continue
            directory, change_id, is_archive = found
            touched.add(change_id)
            if is_archive and path == change.path and change.status in "AR":
                # Archived by this PR only if the archive folder is new.
                if directory not in existed_at_base:
                    existed_at_base[directory] = (
                        git.show(base, f"{directory}/proposal.md") is not None
                    )
                if not existed_at_base[directory]:
                    archived.add(change_id)

    files: dict[str, str] = {}
    if touched:
        listed = git.run(
            "ls-tree", "-r", "--name-only", head, "--", openspec.CHANGES_DIR
        )
        for path in listed.splitlines():
            found = openspec.locate(path)
            if not (path.endswith(".md") and found and found[1] in touched):
                continue
            if (text := git.show(head, path)) is not None:
                files[path] = text
    docs = {
        path: git.show(head, path)
        for path in (
            traceability.PRD,
            traceability.E2E,
            traceability.DEV,
            traceability.EXPERIENCE,
            traceability.SECURITY,
        )
    }
    changed = {c.path for c in changes}
    failures, notes = traceability.check(
        docs,
        openspec.changes_from_files(files),
        archived=archived,
        touched=touched,
        claims_changed=bool(changed & {traceability.PRD, traceability.E2E}),
        sha_exists=git.exists,
    )
    title = "문서 추적성 (archive 기록·근거 없는 완료)"
    check = _check("docs", title, "fail" if failures else "pass", failures)
    return check, [{"title": t, "items": items} for t, items in notes.items()]


def analyze(
    repo: str,
    base: str,
    head: str,
    *,
    gitleaks_exit: str,
    gitleaks_report: str | None,
    zizmor_exit: str,
    zizmor_log: str | None,
    now: datetime | None = None,
    lookup: Lookup = registry.lookup,
) -> dict:
    git = Git(repo)
    base, head = git.verify(base), git.verify(head)
    now = now or datetime.now(timezone.utc)

    changes = collect_changes(git, base, head)
    changed = {c.path for c in changes}
    supply_chain, young = check_supply_chain(git, base, head, changed, now, lookup)
    checks = [
        check_secrets(gitleaks_exit, gitleaks_report),
        check_workflows(zizmor_exit, zizmor_log),
        supply_chain,
    ]
    docs_check, notes = check_docs(git, base, head, changes)
    checks.append(docs_check)

    found = signals.collect_signals(changes)
    if young:
        found.append(
            signals.Signal("young-package", signals.TITLES["young-package"], young)
        )
    return {
        "version": 1,
        "base": base,
        "head": head,
        "checks": checks,
        "signals": [{"id": s.id, "title": s.title, "items": s.items} for s in found],
        "deterministic_failed": any(c["status"] == "fail" for c in checks),
        "needs_ack": bool(found),
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="PR checkout (read as data)")
    parser.add_argument("--base", required=True, help="merge base commit")
    parser.add_argument("--head", required=True, help="PR head commit")
    parser.add_argument("--gitleaks-exit", required=True)
    parser.add_argument("--gitleaks-report")
    parser.add_argument("--zizmor-exit", required=True, help="exit code, or 'skipped'")
    parser.add_argument("--zizmor-log")
    parser.add_argument("--json", required=True, dest="json_path")
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()

    result = analyze(
        args.repo,
        args.base,
        args.head,
        gitleaks_exit=args.gitleaks_exit,
        gitleaks_report=args.gitleaks_report,
        zizmor_exit=args.zizmor_exit,
        zizmor_log=args.zizmor_log,
    )
    Path(args.json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    Path(args.markdown).write_text(report.render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
