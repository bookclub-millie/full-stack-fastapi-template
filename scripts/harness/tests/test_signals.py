import unittest

from signals import FileChange, Signal, collect_signals, manifest_dependencies


def change(path, status="M", added=(), removed=(), base=None, head=None, old_path=None):
    return FileChange(
        path=path,
        status=status,
        old_path=old_path,
        added=list(added),
        removed=list(removed),
        base_text=base,
        head_text=head,
    )


def ids(signals: list[Signal]) -> set[str]:
    return {s.id for s in signals}


class HarnessConfigTest(unittest.TestCase):
    def test_workflow_and_agent_files_are_flagged(self) -> None:
        for path in (
            ".github/workflows/test.yml",
            "AGENTS.md",
            "backend/CLAUDE.md",
            ".claude/settings.json",
            "bunfig.toml",
            "scripts/harness/gate.py",
            ".pre-commit-config.yaml",
            ".gitleaks.toml",
        ):
            with self.subTest(path=path):
                self.assertIn("harness-config", ids(collect_signals([change(path)])))

    def test_uv_cooldown_edit_in_pyproject_is_flagged(self) -> None:
        signals = collect_signals(
            [change("pyproject.toml", added=['exclude-newer = "1 day"'])]
        )
        self.assertIn("harness-config", ids(signals))

    def test_other_pyproject_edits_are_not_harness_config(self) -> None:
        signals = collect_signals([change("pyproject.toml", added=['"typer>=0.27"'])])
        self.assertNotIn("harness-config", ids(signals))

    def test_ordinary_source_change_is_clean(self) -> None:
        self.assertEqual(
            collect_signals([change("backend/app/main.py", added=["x = 1"])]), []
        )


class TestIntegrityTest(unittest.TestCase):
    def test_deleted_test_file(self) -> None:
        signals = collect_signals(
            [
                change(
                    "backend/tests/api/test_items.py",
                    status="D",
                    base="def test_a():\n    assert 1\n",
                )
            ]
        )
        self.assertIn("test-removed", ids(signals))

    def test_test_renamed_out_of_test_tree(self) -> None:
        signals = collect_signals(
            [
                change(
                    "backend/app/old_items.py",
                    status="R",
                    old_path="backend/tests/test_items.py",
                    base="",
                    head="",
                )
            ]
        )
        self.assertIn("test-removed", ids(signals))

    def test_fewer_test_functions(self) -> None:
        base = "def test_a():\n    assert 1\n\nasync def test_b():\n    assert 2\n"
        head = "def test_a():\n    assert 1\n"
        signals = collect_signals(
            [change("backend/tests/test_x.py", base=base, head=head)]
        )
        self.assertIn("test-removed", ids(signals))

    def test_fewer_playwright_tests_and_expects(self) -> None:
        base = "test('a', async () => { expect(1).toBe(1) })\ntest(\"b\", async () => { expect(2).toBe(2) })\n"
        head = "test('a', async () => { expect(1).toBe(1) })\n"
        signals = collect_signals(
            [change("frontend/tests/items.spec.ts", base=base, head=head)]
        )
        self.assertTrue({"test-removed", "assertion-drop"} <= ids(signals))

    def test_fewer_assertions(self) -> None:
        base = "def test_a():\n    assert x == 1\n    assert y == 2\n"
        head = "def test_a():\n    assert x == 1\n"
        signals = collect_signals(
            [change("backend/tests/test_x.py", base=base, head=head)]
        )
        self.assertEqual(ids(signals), {"assertion-drop"})

    def test_adding_tests_is_clean(self) -> None:
        base = "def test_a():\n    assert 1\n"
        head = base + "\ndef test_b():\n    assert 2\n"
        self.assertEqual(
            collect_signals(
                [
                    change(
                        "backend/tests/test_x.py",
                        added=["def test_b():"],
                        base=base,
                        head=head,
                    )
                ]
            ),
            [],
        )

    def test_skip_and_focus_markers(self) -> None:
        for line in (
            "@pytest.mark.skip(reason='flaky')",
            "@pytest.mark.xfail",
            "pytest.skip('later')",
            "test.skip('a', async () => {})",
            "test.only('a', async () => {})",
            "test.describe.fixme('x', () => {})",
            "test.fail('a', async () => {})",
            "it.fails('a', () => {})",
            "it.only('a', () => {})",
            "xit('a', () => {})",
            "fdescribe('a', () => {})",
        ):
            with self.subTest(line=line):
                signals = collect_signals(
                    [change("backend/tests/test_x.py", added=[line])]
                )
                self.assertIn("test-skip", ids(signals))

    def test_test_config_change(self) -> None:
        for path, line in (
            (
                ".github/workflows/test-backend.yml",
                "run: uv run coverage report --fail-under=50",
            ),
            ("backend/pyproject.toml", "fail_under = 50"),
            ("frontend/playwright.config.ts", "retries: 5,"),
            ("backend/scripts/test.sh", "coverage run -m pytest tests/api"),
        ):
            with self.subTest(path=path):
                self.assertIn(
                    "test-config", ids(collect_signals([change(path, added=[line])]))
                )


class SuppressionTest(unittest.TestCase):
    def test_lint_and_type_suppressions(self) -> None:
        for line in (
            "x = foo()  # type: ignore",
            "import os  # noqa: F401",
            "def f():  # pragma: no cover",
            "// @ts-expect-error",
            "// @ts-ignore",
            "/* eslint-disable */",
            "// biome-ignore lint/suspicious/noExplicitAny: legacy",
        ):
            with self.subTest(line=line):
                self.assertIn(
                    "suppression",
                    ids(collect_signals([change("backend/app/x.py", added=[line])])),
                )

    def test_broad_except(self) -> None:
        for line in (
            "except:",
            "    except Exception:",
            "except BaseException as exc:",
        ):
            with self.subTest(line=line):
                self.assertIn(
                    "broad-except",
                    ids(collect_signals([change("backend/app/x.py", added=[line])])),
                )

    def test_specific_except_is_clean(self) -> None:
        self.assertEqual(
            collect_signals([change("backend/app/x.py", added=["except ValueError:"])]),
            [],
        )

    def test_generated_code_is_ignored(self) -> None:
        signals = collect_signals(
            [
                change(
                    "frontend/src/client/sdk.gen.ts",
                    added=["// @ts-ignore", "/* eslint-disable */"],
                )
            ]
        )
        self.assertEqual(signals, [])


class DependencyTest(unittest.TestCase):
    def test_package_json_dependencies(self) -> None:
        text = '{"dependencies": {"axios": "1"}, "devDependencies": {"@types/node": "1"}, "peerDependencies": {"react": "19"}}'
        self.assertEqual(
            manifest_dependencies("frontend/package.json", text),
            {"axios", "@types/node", "react"},
        )

    def test_pyproject_dependencies(self) -> None:
        text = (
            '[project]\ndependencies = ["FastAPI[standard]>=0.1", "pydantic_settings"]\n'
            '[project.optional-dependencies]\ndev = ["pytest"]\n'
            '[dependency-groups]\ndev = ["mypy>=1", {include-group = "lint"}]\n'
        )
        self.assertEqual(
            manifest_dependencies("backend/pyproject.toml", text),
            {"fastapi", "pydantic-settings", "pytest", "mypy"},
        )

    def test_new_direct_dependency_is_flagged(self) -> None:
        base = '{"dependencies": {"axios": "1"}}'
        head = '{"dependencies": {"axios": "1", "left-padder": "1"}}'
        signals = collect_signals(
            [change("frontend/package.json", base=base, head=head)]
        )
        self.assertEqual(ids(signals), {"new-dependency"})
        self.assertIn("left-padder", signals[0].items[0])

    def test_version_bump_is_clean(self) -> None:
        base = '{"dependencies": {"axios": "1.0.0"}}'
        head = '{"dependencies": {"axios": "1.1.0"}}'
        self.assertEqual(
            collect_signals([change("frontend/package.json", base=base, head=head)]), []
        )


if __name__ == "__main__":
    unittest.main()
