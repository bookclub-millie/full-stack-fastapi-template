import json
import unittest
from datetime import datetime, timezone
from unittest import mock

import collect_evidence
import run_evidence

SHA = "d" * 40


class RunEvidenceTest(unittest.TestCase):
    def test_dispatches_waits_and_prints_rows(self) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        dispatched: list[str] = []
        polls = {"n": 0}

        def fake_gh(*args: str) -> str:
            if args[:2] == ("repo", "view"):
                return "o/r\n"
            if args[0] == "api":
                return SHA + "\n"
            if args[:2] == ("workflow", "run"):
                dispatched.append(args[2])
                self.assertEqual(args[args.index("--ref") + 1], "master")
                return ""
            if args[:2] == ("run", "list"):
                polls["n"] += 1
                status = "completed" if polls["n"] > 3 else "in_progress"
                run = {
                    "databaseId": 1,
                    "headSha": SHA,
                    "status": status,
                    "conclusion": "success" if status == "completed" else None,
                    "createdAt": now,
                    "url": "u",
                }
                other = {**run, "headSha": "e" * 40}  # a run on another commit
                return json.dumps([run, other])
            raise AssertionError(args)

        evidence = [
            collect_evidence.Evidence(
                "TC-01", "PASS", ["t PASS"], [("Test Backend", "u", "t")]
            )
        ]
        with (
            mock.patch.object(run_evidence, "_gh", fake_gh),
            mock.patch.object(run_evidence.time, "sleep", lambda _: None),
            mock.patch.object(
                collect_evidence, "collect", return_value=(evidence, [])
            ) as collect,
            mock.patch("sys.argv", ["run_evidence.py"]),
            mock.patch("builtins.print") as printed,
        ):
            self.assertEqual(run_evidence.main(), 0)
        self.assertEqual(dispatched, list(run_evidence.WORKFLOWS))
        collect.assert_called_once_with("o/r", SHA)
        output = "\n".join(str(c.args[0]) for c in printed.call_args_list if c.args)
        self.assertIn(f"| TC-01 | {SHA} |", output)


if __name__ == "__main__":
    unittest.main()
