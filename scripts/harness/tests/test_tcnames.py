import time
import unittest

from tcnames import ids, is_collected, is_test_file, scan, tc_id

E2E = "frontend/tests/e2e/a.spec.ts"
PLAYWRIGHT = """
test.describe("TC-02 묶음", () => {
  test("TC-01 저장 후 보인다", async () => {})
  test.skip('TC-3 건너뜀', async () => {})
  test("TC01 잘못", async () => {})
  test("TC-04 TC-05 둘", async () => {})
  test.step("TC-06 단계", async () => {})
  test("UTC 9 시간대", async () => {})
  test(`TC-07 템플릿`, async () => {})
  const ok = /TC-\\d+/.test("TC-08")
  test("결제TC-09", async () => {})
  test(
    'TC-10 줄바꿈된 제목',
    async () => {}
  )
  test.fail("TC-11 실패 기대", async () => {})
  // test("TC-12 주석")
  /* test("TC-13 블록
     test("TC-14") */
  const s = 'test("TC-15 문자열")'
  test("TC-16 http://x.y/z", async () => {})
})
"""

PYTEST = '''
"""
def test_tc_20_docstring(): pass
"""
import pytest

def test_tc_01_ok(): pass
def outer():
    def test_tc_21_nested(): pass
class Helper:
    def test_tc_22_not_collected(self): pass
class TestX:
    async def test_tc_2_ok(self): pass
    def testTC03(self): pass
    class TestInner:
        def test_tc_05_inner(self): pass
def test_login_tc_04(): pass
def test_utc8(): pass
def helper_tc_05(): pass
if False:
    def test_tc_23_if_false(): pass
@pytest.mark.skip(reason="todo")
def test_tc_06_skipped(): pass
@pytest.mark.xfail
def test_tc_07_xfail(): pass
'''


class NormalizeTest(unittest.TestCase):
    def test_same_tc_whatever_the_padding(self) -> None:
        self.assertEqual({tc_id("1"), tc_id("01"), tc_id("001")}, {"TC-01"})
        self.assertEqual(ids("TC-1, TC-012 · AC-01"), ["TC-01", "TC-12"])

    def test_huge_numbers_are_not_ids(self) -> None:
        self.assertEqual(ids("TC-" + "1" * 5000 + " TC-1234567"), [])
        _, problems = scan(
            "backend/tests/test_x.py", f"def test_tc_{'9' * 5000}(): pass\n"
        )
        self.assertEqual(len(problems), 1)


class FilesTest(unittest.TestCase):
    def test_test_files_and_collected_locations(self) -> None:
        cases = {
            "backend/tests/api/test_items.py": (True, True),
            "backend/tests/conftest.py": (False, True),
            "backend/app/tests/test_x.py": (True, False),
            "frontend/tests/e2e/items.spec.ts": (True, True),
            "frontend/tests/e2e/auth.setup.ts": (False, True),
            "frontend/tests/visual/kds.spec.ts": (True, False),
            "frontend/src/lib/utils.test.ts": (True, True),
            "frontend/src/routes/login.test.tsx": (True, False),
            "packages/ui/src/button.test.tsx": (True, False),
            "frontend/node_modules/x/a.test.ts": (False, False),
            "backend/.venv/lib/site-packages/x/test_y.py": (False, False),
            "backend/app/main.py": (False, False),
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual((is_test_file(path), is_collected(path)), expected)


class ScanTest(unittest.TestCase):
    def test_playwright_titles(self) -> None:
        tagged, problems = scan(E2E, PLAYWRIGHT)
        self.assertEqual(
            [(t.tc, t.line, t.runs) for t in tagged],
            [
                ("TC-01", 3, True),
                ("TC-03", 4, False),
                ("TC-07", 9, True),
                ("TC-10", 12, True),
                ("TC-16", 21, True),
            ],
        )
        reasons = {p.line: p.reason for p in problems}
        self.assertEqual(sorted(reasons), [2, 5, 6, 7, 11, 16])
        self.assertIn("test.describe()", reasons[2])
        self.assertIn('`test("TC-07 <설명>", ...)` 형식', reasons[5])
        self.assertIn("첫 번째(TC-04)만", reasons[6])
        self.assertIn("test.step()", reasons[7])
        self.assertIn("수집되지 않는 TC 표기", reasons[11])
        self.assertIn("test.fail()", reasons[16])

    def test_tc_outside_collected_locations(self) -> None:
        for path, text in [
            (
                "frontend/src/lib/a.test.tsx",
                'it("TC-01 단위", () => {})\nit("평범", () => {})\n',
            ),
            ("backend/app/tests/test_x.py", "def test_tc_01_x(): pass\n"),
        ]:
            with self.subTest(path=path):
                tagged, problems = scan(path, text)
                self.assertEqual(tagged, [])
                self.assertEqual(len(problems), 1)
                self.assertIn("수집되지 않습니다", problems[0].reason)

    def test_vitest_titles(self) -> None:
        text = (
            "import { describe, expect, it, test } from 'vitest'\n"
            "describe('묶음', () => {\n"
            "  it('TC-05 통과', () => { expect(1).toBe(1) })\n"
            "  it.skip('TC-07 건너뜀', () => {})\n"
            "  it.todo('TC-08 할 일')\n"
            "  it.fails('TC-09 실패 기대', () => {})\n"
            "  it.concurrent('TC-11 동시', async () => {})\n"
            "})\n"
            "test('TC-10 최상위', () => {})\n"
            "describe('TC-12 묶음', () => {})\n"
        )
        tagged, problems = scan("frontend/src/lib/a.test.ts", text)
        self.assertEqual(
            [(t.tc, t.runs) for t in tagged],
            [
                ("TC-05", True),
                ("TC-07", False),
                ("TC-08", False),
                ("TC-11", True),
                ("TC-10", True),
            ],
        )
        reasons = {p.line: p.reason for p in problems}
        self.assertIn("it.fails()은 실패를 기대하는 테스트", reasons[6])
        self.assertIn("describe() 제목의 TC ID는 수집되지 않습니다", reasons[10])
        # `it` is not a Playwright test function.
        _, problems = scan(E2E, "it('TC-01 x', () => {})\n")
        self.assertIn("it() 제목의 TC ID는 수집되지 않습니다", problems[0].reason)

    def test_pytest_collects_only_real_tests(self) -> None:
        tagged, problems = scan("backend/tests/api/test_x.py", PYTEST)
        self.assertEqual(
            [(t.tc, t.name, t.runs) for t in tagged],
            [
                ("TC-01", "test_tc_01_ok", True),
                ("TC-02", "test_tc_2_ok", True),
                ("TC-05", "test_tc_05_inner", True),
                ("TC-06", "test_tc_06_skipped", False),
                ("TC-07", "test_tc_07_xfail", False),
            ],
        )
        self.assertEqual(
            sorted(p.name for p in problems), ["testTC03", "test_login_tc_04"]
        )

    def test_module_skip_and_unparsable_files(self) -> None:
        tagged, _ = scan(
            "backend/tests/test_y.py",
            "import pytest\npytestmark = pytest.mark.skip\ndef test_tc_01(): pass\n",
        )
        self.assertEqual([(t.tc, t.runs) for t in tagged], [("TC-01", False)])
        # Syntax this Python cannot parse falls back to reading def lines.
        tagged, _ = scan("backend/tests/test_z.py", "def test_tc_02(:\n")
        self.assertEqual([t.tc for t in tagged], ["TC-02"])

    def test_hostile_input_stays_fast(self) -> None:
        for path, text in [
            (E2E, 'test("' * 200_000),
            (E2E, "/*" * 300_000),
            (E2E, ('test("' + "a" * 400 + "\n") * 3000),
            ("backend/tests/test_z.py", "(" * 100_000),
        ]:
            started = time.monotonic()
            scan(path, text)
            self.assertLess(time.monotonic() - started, 2, path)


if __name__ == "__main__":
    unittest.main()
