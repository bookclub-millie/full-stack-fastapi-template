"""TC ids in test names: the ones collect_evidence counts, and near misses it would drop.

pytest functions named `test_tc_07_...` under backend/tests, Playwright
`test("TC-07 ...")` titles under frontend/tests/e2e and vitest `it("TC-07 ...")`
titles in frontend/src/**/*.test.ts are collected. Everything
here reads source as text (Python through `ast.parse`); nothing is executed.
See docs/adr/001-openspec-docs-traceability.md.
"""

from __future__ import annotations

import ast
import bisect
import re
from dataclasses import dataclass

# Up to six digits: more cannot be a real id, and int() of a huge number raises.
TC_ID = re.compile(r"\bTC-(\d{1,6})\b")  # documents and Playwright titles
PYTEST_TC = re.compile(r"\btest_tc_?(\d{1,6})(?!\d)", re.IGNORECASE)
# A TC-like tag the collector would not read: TC01, TC_01, tc-01, testTC01, test_x_tc_01.
NEAR_MISS = re.compile(r"(?:(?<![A-Z])TC|(?<![A-Za-z0-9])tc)[-_ ]?\d+")

# Where collect_evidence gets results: Test Backend runs `pytest tests/` in backend,
# Playwright Tests runs frontend/playwright.config.ts (testDir ./tests/e2e), and
# Frontend Quality runs vitest with frontend/vitest.config.ts (src/**/*.test.ts).
PYTHON_TESTS = "backend/tests/"
PLAYWRIGHT_TESTS = "frontend/tests/e2e/"
VITEST_TESTS = "frontend/src/"
VITEST_SUFFIX = ".test.ts"
LOCATIONS = (
    f"{PYTHON_TESTS}(pytest), {PLAYWRIGHT_TESTS}(Playwright), "
    f"{VITEST_TESTS}**/*{VITEST_SUFFIX}(vitest)"
)
# Test files elsewhere (backend/app, .test.tsx, Storybook) are read only to report
# TC ids that would never be collected.
SCAN_ROOTS = ("backend/", "frontend/", "packages/")
_SKIP_DIRS = re.compile(r"(?:^|/)(?:node_modules|\.venv|site-packages)/")
_PYTHON_FILE = re.compile(r"(?:^|/)(?:test_[^/]*|[^/]*_test)\.py$")
_JS_FILE = re.compile(r"\.(?:spec|test)\.[cm]?[jt]sx?$")
_PYTHON_DEF = re.compile(
    r"^[ \t]*(?:async[ \t]+)?def[ \t]+(test\w*)[ \t]*\(", re.MULTILINE
)
# test(...), test.only(...), test.describe(...), it(...), describe.each(...) with a
# string title, also when the formatter moved the title to the next line. Titles are
# read on one line and up to 500 characters, so hostile input stays linear.
_JS_CALL = re.compile(
    r"(?<![.\w$])(test|it|describe)(?:\.(\w+))?(?:\.(\w+))?\s{0,200}\(\s{0,200}"
    r"([\"'`])((?:\\.|(?!\4)[^\\\n]){0,500})\4"
)
# Comments and string literals, so a call written inside them is not read.
_JS_TOKEN = re.compile(
    r"//[^\n]*|/\*.*?(?:\*/|\Z)"
    r"|\"(?:\\.|[^\"\\\n])*\"?|'(?:\\.|[^'\\\n])*'?|`(?:\\.|[^`\\])*`?",
    re.DOTALL,
)
# Modifiers that still declare one test: (runs, reported as SKIP). Anything else
# (describe, step, each, skipIf, ...) does not carry a collected title.
_PLAYWRIGHT_SPEC = {None: True, "only": True, "skip": False, "fixme": False}
_VITEST_SPEC = {
    None: True,
    "only": True,
    "concurrent": True,
    "sequential": True,
    "skip": False,
    "todo": False,
}
# Expected failures are reported as passing when they fail.
_EXPECTED_FAILURE = {"fail", "fails"}
_PYTEST_SKIP = re.compile(r"\b(?:skip|skipif|xfail)\b")


def tc_id(number: str) -> str:
    """TC-1, TC-01 and TC-001 are the same TC."""
    return f"TC-{int(number):02d}"


def ids(text: str) -> list[str]:
    """TC ids in a document cell, normalized, in order."""
    return [tc_id(number) for number in TC_ID.findall(text)]


def pytest_tc(name: str) -> str | None:
    match = PYTEST_TC.search(name)
    return tc_id(match.group(1)) if match else None


def title_tc(title: str) -> str | None:
    match = TC_ID.search(title)
    return tc_id(match.group(1)) if match else None


def vitest_tc(name: str) -> str | None:
    """vitest JUnit names are `describe > title`; the title's id is the last one."""
    found = ids(name)
    return found[-1] if found else None


def pytest_form(tc: str = "TC-07") -> str:
    return f"pytest `test_tc_{tc.removeprefix('TC-')}_<설명>`"


def title_form(tc: str = "TC-07") -> str:
    return f'Playwright·vitest `test("{tc} <설명>", ...)`'


def is_test_file(path: str) -> bool:
    if _SKIP_DIRS.search(path):
        return False
    if path.startswith("backend/"):
        return bool(_PYTHON_FILE.search(path))
    return path.startswith(SCAN_ROOTS) and bool(_JS_FILE.search(path))


def is_vitest(path: str) -> bool:
    return path.startswith(VITEST_TESTS) and path.endswith(VITEST_SUFFIX)


def is_collected(path: str) -> bool:
    return path.startswith((PYTHON_TESTS, PLAYWRIGHT_TESTS)) or is_vitest(path)


@dataclass(frozen=True)
class TaggedTest:
    tc: str
    path: str
    line: int
    name: str
    runs: bool = True  # False for skip / fixme / pytest skip and xfail marks


@dataclass(frozen=True)
class NameProblem:
    path: str
    line: int
    name: str
    reason: str


def _line_finder(text: str):
    """offset -> 1-based line number, without rescanning the text per match."""
    starts = [match.end() for match in re.finditer("\n", text)]
    return lambda offset: bisect.bisect_right(starts, offset) + 1


def _skips(decorators: list[ast.expr]) -> bool:
    return any(_PYTEST_SKIP.search(ast.unparse(d)) for d in decorators)


def _python_tests(text: str) -> list[tuple[str, int, bool]] | None:
    """(name, line, runs) of the functions pytest collects, or None if unparsable.

    Module-level `test*` functions and `test*` methods of `Test*` classes, as
    pytest collects by default (backend has no pytest configuration).
    """
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    found: list[tuple[str, int, bool]] = []

    def visit(body: list[ast.stmt], in_class: bool, skipped: bool) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test"):
                    runs = not (skipped or _skips(node.decorator_list))
                    found.append((node.name, node.lineno, runs))
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                visit(node.body, True, skipped or _skips(node.decorator_list))
            elif not in_class and isinstance(node, ast.Assign):
                # `pytestmark = pytest.mark.skip(...)` skips the whole module.
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
                if "pytestmark" in names and _PYTEST_SKIP.search(
                    ast.unparse(node.value)
                ):
                    skipped = True

    try:
        visit(tree.body, False, False)
    except RecursionError:
        return None
    return found


def _js_code(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Text with comments blanked (offsets kept) and the spans of string literals."""
    parts: list[str] = []
    strings: list[tuple[int, int]] = []
    last = 0
    for match in _JS_TOKEN.finditer(text):
        if match.group().startswith("/"):
            parts += [text[last : match.start()], re.sub(r"[^\n]", " ", match.group())]
            last = match.end()
        else:
            strings.append(match.span())
    parts.append(text[last:])
    return "".join(parts), strings


def _tagged_or_problem(
    path: str, line: int, name: str, found: list[str], form: str, runs: bool
) -> TaggedTest | NameProblem | None:
    if len(set(found)) > 1:
        return NameProblem(
            path,
            line,
            name,
            f"TC ID가 여러 개면 첫 번째({found[0]})만 수집됩니다. 테스트를 TC마다 나누세요",
        )
    if found and not is_collected(path):
        return NameProblem(
            path,
            line,
            name,
            f"이 위치의 테스트 결과는 수집되지 않습니다. TC 테스트는 {LOCATIONS}에 두세요",
        )
    if found:
        return TaggedTest(found[0], path, line, name, runs)
    if NEAR_MISS.search(name):
        return NameProblem(
            path, line, name, f"수집되지 않는 TC 표기입니다. {form} 형식으로 쓰세요"
        )
    return None


def _scan_python(path: str, text: str) -> tuple[list[TaggedTest], list[NameProblem]]:
    tests = _python_tests(text)
    if tests is None:
        # Syntax this Python cannot parse (the gate may run an older Python than
        # the backend): fall back to reading `def test...` lines.
        line_of = _line_finder(text)
        tests = [
            (m.group(1), line_of(m.start(1)), True) for m in _PYTHON_DEF.finditer(text)
        ]
    tagged: list[TaggedTest] = []
    problems: list[NameProblem] = []
    for name, line, runs in tests:
        found = [tc_id(n) for n in PYTEST_TC.findall(name)]
        form = pytest_form(found[0] if found else "TC-07")
        result = _tagged_or_problem(path, line, name, found, form, runs)
        if isinstance(result, TaggedTest):
            tagged.append(result)
        elif result:
            problems.append(result)
    return tagged, problems


def _scan_js(path: str, text: str) -> tuple[list[TaggedTest], list[NameProblem]]:
    line_of = _line_finder(text)
    code, strings = _js_code(text)
    string_starts = [start for start, _ in strings]
    vitest = is_vitest(path)
    spec_modifiers = _VITEST_SPEC if vitest else _PLAYWRIGHT_SPEC
    spec_functions = {"test", "it"} if vitest else {"test"}
    tagged: list[TaggedTest] = []
    problems: list[NameProblem] = []
    for match in _JS_CALL.finditer(code):
        at = bisect.bisect_right(string_starts, match.start()) - 1
        if at >= 0 and match.start() < strings[at][1]:
            continue  # `test("...")` written inside a string literal
        function, first, second, _, title = match.groups()
        found = ids(title)
        if not (found or NEAR_MISS.search(title)):
            continue
        line = line_of(match.start())
        if function in spec_functions and first in spec_modifiers and second is None:
            form = title_form(found[0] if found else "TC-07")
            result = _tagged_or_problem(
                path, line, title, found, form, spec_modifiers[first]
            )
            if isinstance(result, TaggedTest):
                tagged.append(result)
            elif result:
                problems.append(result)
            continue
        called = ".".join(filter(None, (function, first, second)))
        if not is_collected(path):
            reason = f"이 위치의 테스트 결과는 수집되지 않습니다. TC 테스트는 {LOCATIONS}에 두세요"
        elif first in _EXPECTED_FAILURE and second is None:
            reason = f"{called}()은 실패를 기대하는 테스트라 실패해도 통과로 기록됩니다. TC는 test()에 붙이세요"
        else:
            reason = f"{called}() 제목의 TC ID는 수집되지 않습니다. 각 test() 제목에 붙이세요"
        problems.append(NameProblem(path, line, title, reason))
    return tagged, problems


def scan(path: str, text: str) -> tuple[list[TaggedTest], list[NameProblem]]:
    """Tests with a TC id in `path`, and TC-like names the collector would miss."""
    if path.endswith(".py"):
        return _scan_python(path, text)
    return _scan_js(path, text)
