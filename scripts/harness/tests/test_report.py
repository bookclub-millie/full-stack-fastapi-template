import unittest

from report import MARKER, MAX_ITEMS, code, render


def make_report(**overrides) -> dict:
    report = {
        "head": "a" * 40,
        "checks": [
            {
                "id": "secrets",
                "title": "비밀값 스캔",
                "status": "pass",
                "items": [],
                "log": "",
            },
            {
                "id": "workflows",
                "title": "워크플로 보안",
                "status": "skip",
                "items": [],
                "log": "",
            },
        ],
        "signals": [],
        "deterministic_failed": False,
        "needs_ack": False,
    }
    report.update(overrides)
    return report


class CodeSpanTest(unittest.TestCase):
    def test_neutralizes_markup_and_invisible_characters(self) -> None:
        self.assertEqual(code("a`b\u200bc\nd\u202ee"), "`a'b c d e`")

    def test_truncates_long_items(self) -> None:
        self.assertTrue(code("x" * 500).endswith("…`"))


class RenderTest(unittest.TestCase):
    def test_clean_report(self) -> None:
        body = render(make_report())
        self.assertTrue(body.startswith(MARKER))
        self.assertIn("확인이 필요한 신호가 없습니다", body)

    def test_failures_and_signals_are_listed(self) -> None:
        checks = [
            {
                "id": "workflows",
                "title": "워크플로 보안",
                "status": "fail",
                "items": ["zizmor exit 13"],
                "log": " INFO audit: completed a.yml\nerror[x]: ```bad```",
            },
        ]
        signals = [
            {
                "id": "test-skip",
                "title": "skip 마커",
                "items": [f"t{i}: @user" for i in range(MAX_ITEMS + 3)],
            }
        ]
        body = render(
            make_report(
                checks=checks,
                signals=signals,
                deterministic_failed=True,
                needs_ack=True,
            )
        )
        self.assertIn("❌ 실패", body)
        self.assertNotIn("```bad```", body)
        self.assertIn("error[x]", body)
        self.assertNotIn("INFO", body)
        self.assertIn("`t0: @user`", body)
        self.assertIn("외 3건", body)
        self.assertIn("harness-ack", body)


if __name__ == "__main__":
    unittest.main()
