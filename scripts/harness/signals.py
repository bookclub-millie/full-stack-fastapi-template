"""Heuristic reward-hacking signals in a PR diff.

A signal is not a verdict: it marks a change that a second person must look at
before merge (test removal, skip markers, weakened config, new dependencies...).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from fnmatch import fnmatch

import tomllib
from lockfiles import normalize_pypi_name

TITLES = {
    "harness-config": "하네스·CI·에이전트 설정 변경",
    "test-removed": "테스트 파일·테스트 함수 감소",
    "assertion-drop": "테스트 assertion 감소",
    "test-skip": "skip·xfail·only 마커 추가",
    "test-config": "테스트·커버리지 설정 변경",
    "suppression": "lint·타입 검사 억제 주석 추가",
    "broad-except": "광범위한 예외 처리 추가",
    "new-dependency": "새 직접 의존성",
    "young-package": "최근에 처음 등록된 패키지",
}

HARNESS_PATHS = (
    ".github/*",
    "scripts/harness/*",
    "AGENTS.md",
    "*/AGENTS.md",
    "CLAUDE.md",
    "*/CLAUDE.md",
    ".claude/*",
    ".agents/*",
    ".codex/*",
    ".mcp.json",
    "bunfig.toml",
    "*/bunfig.toml",
    ".pre-commit-config.yaml",
    ".gitleaks.toml",
    ".gitleaksignore",
    "zizmor.yml",
)
UV_CONFIG_PATHS = ("pyproject.toml", "*/pyproject.toml", "uv.toml", "*/uv.toml")
TEST_PATHS = (
    "*/tests/*",
    "tests/*",
    "*test_*.py",
    "*_test.py",
    "*conftest.py",
    "*.spec.ts",
    "*.spec.tsx",
    "*.test.ts",
    "*.test.tsx",
)
# Generated or vendored files: content signals there are noise.
CONTENT_IGNORED = (
    "frontend/src/client/*",
    "*.gen.ts",
    "backend/app/email-templates/*",
    "bun.lock",
    "uv.lock",
    "scripts/harness/*",
)
TEST_CONFIG_ANY_CHANGE = (
    "*playwright.config.*",
    "*vitest.config.*",
    "*jest.config.*",
    "*pytest.ini",
    "*.coveragerc",
    "*scripts/test*.sh",
    "*scripts/tests-start.sh",
)
TEST_CONFIG_KEYED = (".github/*", "*pyproject.toml", "*setup.cfg", "*tox.ini")
MANIFESTS = ("package.json", "*/package.json", "pyproject.toml", "*/pyproject.toml")

TEST_CONFIG_KEYS = re.compile(
    r"fail[_-]under|COVERAGE_THRESHOLD|addopts|testpaths|\bomit\b|exclude_(?:lines|also)"
    r"|--cov|coverage\s+(?:run|report)|pytest|playwright\s+test"
)
UV_COOLDOWN_KEYS = re.compile(r"exclude-newer")
PY_TEST_DEF = re.compile(r"^\s*(?:async\s+)?def\s+test\w*\s*\(", re.MULTILINE)
JS_TEST_CALL = re.compile(
    r"\b(?:test|it)(?:\.(?:only|skip|fixme|fail|slow))?\s*\(\s*['\"`]"
)
PY_ASSERT = re.compile(r"\bassert\b|\bpytest\.raises\b")
JS_EXPECT = re.compile(r"\bexpect(?:\.\w+)?\s*\(")
SKIP_MARKER = re.compile(
    r"pytest\.mark\.(?:skip|skipif|xfail)\b|pytest\.(?:skip|xfail|importorskip)\s*\("
    r"|unittest\.skip|@skip\b"
    r"|\b(?:test|it|describe)(?:\.describe)?\.(?:skip|only|fixme|todo)\s*\("
    r"|\b[xf](?:it|describe)\s*\("  # jasmine/jest-style focused or excluded tests
)
SUPPRESSION = re.compile(
    r"#\s*type:\s*ignore|#\s*noqa\b|#\s*pragma:\s*no\s*cover|#\s*(?:ty|pyright|mypy):\s*ignore"
    r"|@ts-(?:ignore|expect-error|nocheck)\b|eslint-disable|biome-ignore"
)
BROAD_EXCEPT = re.compile(
    r"^\s*except\s*:|^\s*except\s+\(?\s*(?:BaseException|Exception)\s*\)?\s*(?:as\s+\w+\s*)?:"
)
REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


@dataclass
class FileChange:
    path: str
    status: str  # A, M, D, R (rename; old_path is set)
    old_path: str | None = None
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    base_text: str | None = None
    head_text: str | None = None


@dataclass
class Signal:
    id: str
    title: str
    items: list[str]


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _is_test(path: str | None) -> bool:
    return (
        bool(path)
        and not _matches(path, CONTENT_IGNORED)
        and _matches(path, TEST_PATHS)
    )


def _count(pattern: re.Pattern[str], text: str | None) -> int:
    return len(pattern.findall(text or ""))


def _test_patterns(path: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    if path.endswith(".py"):
        return PY_TEST_DEF, PY_ASSERT
    return JS_TEST_CALL, JS_EXPECT


def wants_text(path: str | None) -> bool:
    """Whether collect_signals needs the full base/head text of this file."""
    return bool(path) and (_is_test(path) or _matches(path, MANIFESTS))


def manifest_dependencies(path: str, text: str | None) -> set[str]:
    if not text:
        return set()
    try:
        if path.endswith("package.json"):
            data = json.loads(text)
            names: set[str] = set()
            for key in (
                "dependencies",
                "devDependencies",
                "peerDependencies",
                "optionalDependencies",
            ):
                section = data.get(key, {})
                if isinstance(section, dict):
                    names.update(section)
            return names
        data = tomllib.loads(text)
    except (ValueError, tomllib.TOMLDecodeError):
        return set()
    requirements: list[object] = list(data.get("project", {}).get("dependencies", []))
    for group in data.get("project", {}).get("optional-dependencies", {}).values():
        requirements.extend(group)
    for group in data.get("dependency-groups", {}).values():
        requirements.extend(group)
    names = set()
    for requirement in requirements:
        if isinstance(requirement, str) and (
            match := REQUIREMENT_NAME.match(requirement)
        ):
            names.add(normalize_pypi_name(match.group(1)))
    return names


def collect_signals(changes: list[FileChange]) -> list[Signal]:
    found: dict[str, list[str]] = {key: [] for key in TITLES}

    def add(signal_id: str, item: str) -> None:
        if item not in found[signal_id]:
            found[signal_id].append(item)

    for change in changes:
        path = change.path
        lines = change.added + change.removed

        if _matches(path, HARNESS_PATHS) or (
            change.old_path and _matches(change.old_path, HARNESS_PATHS)
        ):
            add("harness-config", path)
        elif _matches(path, UV_CONFIG_PATHS) and any(
            UV_COOLDOWN_KEYS.search(line) for line in lines
        ):
            add("harness-config", f"{path}: exclude-newer")

        # Test files that disappear, shrink, or lose assertions.
        was_test = _is_test(change.old_path or path)
        if change.status == "D" and was_test:
            add("test-removed", f"{path}: 삭제")
        elif change.status == "R" and was_test and not _is_test(path):
            add("test-removed", f"{change.old_path} → {path}: 테스트 경로 밖으로 이동")
        elif (
            _is_test(path)
            and change.base_text is not None
            and change.head_text is not None
        ):
            test_pattern, assert_pattern = _test_patterns(path)
            before, after = (
                _count(test_pattern, change.base_text),
                _count(test_pattern, change.head_text),
            )
            if after < before:
                add("test-removed", f"{path}: 테스트 {before} → {after}")
            before, after = (
                _count(assert_pattern, change.base_text),
                _count(assert_pattern, change.head_text),
            )
            if after < before:
                add("assertion-drop", f"{path}: assertion {before} → {after}")

        if _matches(path, TEST_CONFIG_ANY_CHANGE) and lines:
            add("test-config", path)
        elif _matches(path, TEST_CONFIG_KEYED):
            for line in lines:
                if TEST_CONFIG_KEYS.search(line):
                    add("test-config", f"{path}: {line.strip()}")

        if not _matches(path, CONTENT_IGNORED):
            for line in change.added:
                if SKIP_MARKER.search(line):
                    add("test-skip", f"{path}: {line.strip()}")
                if SUPPRESSION.search(line):
                    add("suppression", f"{path}: {line.strip()}")
                if path.endswith(".py") and BROAD_EXCEPT.search(line):
                    add("broad-except", f"{path}: {line.strip()}")

        if _matches(path, MANIFESTS) and change.status != "D":
            new = manifest_dependencies(path, change.head_text) - manifest_dependencies(
                path, change.base_text
            )
            for name in sorted(new):
                add("new-dependency", f"{path}: {name}")

    return [Signal(key, TITLES[key], items) for key, items in found.items() if items]
