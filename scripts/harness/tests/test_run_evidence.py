import json
import unittest
from unittest import mock

import collect_evidence
import run_evidence

SHA = "d" * 40


class RunEvidenceTest(unittest.TestCase):
    def fake_gh(self, runs_after_dispatch, dispatched):
        state = {"dispatched": False, "polls": 0}

        def gh(*args: str) -> str:
            if args[:2] == ("repo", "view"):
                return "o/r\n"
            if args[0] == "api":
                return SHA + "\n"
            if args[:2] == ("workflow", "run"):
                dispatched.append(args[2])
                state["dispatched"] = True
                return ""
            if args[:2] == ("run", "list"):
                old = {
                    "databaseId": 5,
                    "headSha": "e" * 40,
                    "status": "completed",
                    "conclusion": "success",
                    "url": "old",
                }
                if not state["dispatched"]:
                    return json.dumps([old])
                state["polls"] += 1
                return json.dumps([*runs_after_dispatch(state["polls"]), old])
            raise AssertionError(args)

        return gh

    def run_main(self, gh, evidence):
        with (
            mock.patch.object(run_evidence, "_gh", gh),
            mock.patch.object(run_evidence.time, "sleep", lambda _: None),
            mock.patch.object(
                collect_evidence, "collect", return_value=(evidence, [])
            ) as collect,
            mock.patch("sys.argv", ["run_evidence.py"]),
            mock.patch("builtins.print") as printed,
        ):
            code = run_evidence.main()
        output = "\n".join(str(c.args[0]) for c in printed.call_args_list if c.args)
        return code, collect, output

    def test_dispatches_waits_and_prints_rows(self) -> None:
        dispatched: list[str] = []

        def after(polls: int) -> list[dict]:
            status = "completed" if polls > 3 else "in_progress"
            return [
                {
                    "databaseId": 7,
                    "headSha": SHA,
                    "status": status,
                    "conclusion": "success",
                    "url": "u",
                }
            ]

        evidence = [
            collect_evidence.Evidence(
                "TC-01", "PASS", ["t PASS"], [("Test Backend", "u", "t")]
            )
        ]
        code, collect, output = self.run_main(self.fake_gh(after, dispatched), evidence)
        self.assertEqual(code, 0)
        self.assertEqual(dispatched, list(run_evidence.WORKFLOWS))
        collect.assert_called_once_with("o/r", SHA)
        self.assertIn(f"| TC-01 | {SHA} |", output)

    def test_stops_when_the_ref_moved(self) -> None:
        def after(_: int) -> list[dict]:
            return [
                {
                    "databaseId": 7,
                    "headSha": "f" * 40,
                    "status": "in_progress",
                    "conclusion": None,
                    "url": "u",
                }
            ]

        code, collect, _ = self.run_main(self.fake_gh(after, []), [])
        self.assertEqual(code, 1)
        collect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
