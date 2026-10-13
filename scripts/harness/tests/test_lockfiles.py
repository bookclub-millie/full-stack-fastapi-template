import unittest
from datetime import timedelta

from lockfiles import (
    Package,
    added_packages,
    bun_cooldown,
    loads_jsonc,
    parse_bun_lock,
    parse_duration,
    parse_uv_lock,
    uv_cooldown,
)

BUN_LOCK = """{
  "lockfileVersion": 1,
  "workspaces": {
    "": { "name": "root", },
    "packages/ui": { "name": "@kds/ui", },
  },
  "packages": {
    "@kds/ui": ["@kds/ui@workspace:packages/ui"],
    "axios": ["axios@1.20.0", "", { "dependencies": {} }, "sha512-a"],
    "@types/node": ["@types/node@26.6.4", "", {}, "sha512-b"],
    "pkg-up/path-exists": ["path-exists@3.0.0", "", {}, "sha512-c"],
    "mirror": ["mirror@1.0.0", "https://registry.npmmirror.com/mirror/-/mirror-1.0.0.tgz", {}, "sha512-d"],
    "gh": ["is-number@github:jonschlinkert/is-number#98e8ff1", {}, "id", "sha512-e"],
    "tar": ["is-odd@https://example.com/is-odd-3.0.1.tgz", {}, "sha512-f"],
    "comma, inside": ["weird@1.0.0", "", { "x": "a,}" }, "sha512-g"],
  }
}
"""

UV_LOCK = """
version = 1
revision = 3

[options]
exclude-newer = "0001-01-01T00:00:00Z" # This has no effect
exclude-newer-span = "P7D"

[options.exclude-newer-package]
certifi = { timestamp = "0001-01-01T00:00:00Z", span = "P30D" }
markupsafe = false

[[package]]
name = "app"
version = "0.1.0"
source = { editable = "backend" }

[[package]]
name = "Typing_Extensions"
version = "4.15.0"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "iniconfig"
version = "2.1.0"
source = { git = "https://github.com/pytest-dev/iniconfig?rev=v2.1.0#34793a64" }

[[package]]
name = "custom"
version = "1.0.0"
source = { registry = "https://mirror.example.com/simple" }
"""


class JsoncTest(unittest.TestCase):
    def test_trailing_commas_outside_strings_are_removed(self) -> None:
        data = loads_jsonc('{"a": [1, 2,], "b": "x,}", }')
        self.assertEqual(data, {"a": [1, 2], "b": "x,}"})

    def test_escaped_quotes_do_not_end_strings(self) -> None:
        self.assertEqual(loads_jsonc('{"a": "q\\",}",}'), {"a": 'q",}'})


class BunLockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.packages = {p.name: p for p in parse_bun_lock(BUN_LOCK)}

    def test_default_registry_packages(self) -> None:
        self.assertEqual(
            self.packages["axios"], Package("npm", "axios", "1.20.0", "registry", "")
        )
        self.assertEqual(self.packages["@types/node"].version, "26.6.4")
        self.assertEqual(self.packages["path-exists"].source, "registry")

    def test_workspace_is_local(self) -> None:
        self.assertEqual(self.packages["@kds/ui"].source, "local")

    def test_non_registry_sources(self) -> None:
        self.assertEqual(self.packages["mirror"].source, "other")
        self.assertIn("npmmirror", self.packages["mirror"].detail)
        self.assertEqual(self.packages["is-number"].source, "other")
        self.assertEqual(self.packages["is-odd"].source, "other")

    def test_string_contents_survive(self) -> None:
        self.assertEqual(self.packages["weird"].version, "1.0.0")


class UvLockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.packages = {p.name: p for p in parse_uv_lock(UV_LOCK)}

    def test_names_are_normalized(self) -> None:
        self.assertEqual(
            self.packages["typing-extensions"],
            Package("pypi", "typing-extensions", "4.15.0", "registry", ""),
        )

    def test_editable_is_local(self) -> None:
        self.assertEqual(self.packages["app"].source, "local")

    def test_git_and_custom_registry_are_other(self) -> None:
        self.assertEqual(self.packages["iniconfig"].source, "other")
        self.assertEqual(self.packages["custom"].source, "other")

    def test_cooldown_options(self) -> None:
        span, excluded = uv_cooldown(UV_LOCK)
        self.assertEqual(span, timedelta(days=7))
        self.assertEqual(excluded, {"certifi", "markupsafe"})

    def test_missing_cooldown(self) -> None:
        self.assertEqual(uv_cooldown("version = 1\n"), (None, set()))


class BunfigTest(unittest.TestCase):
    def test_reads_age_and_excludes(self) -> None:
        age, excluded = bun_cooldown(
            '[install]\nminimumReleaseAge = 604800\nminimumReleaseAgeExcludes = ["@types/node"]\n'
        )
        self.assertEqual(age, timedelta(days=7))
        self.assertEqual(excluded, {"@types/node"})

    def test_missing_file_or_key(self) -> None:
        self.assertEqual(bun_cooldown(None), (None, set()))
        self.assertEqual(bun_cooldown("[install]\n"), (None, set()))

    def test_non_integer_age_is_treated_as_missing(self) -> None:
        self.assertEqual(
            bun_cooldown('[install]\nminimumReleaseAge = "7d"\n'), (None, set())
        )


class DurationTest(unittest.TestCase):
    def test_iso_durations(self) -> None:
        self.assertEqual(parse_duration("P7D"), timedelta(days=7))
        self.assertEqual(parse_duration("P1W"), timedelta(days=7))
        self.assertEqual(parse_duration("P1DT12H"), timedelta(days=1, hours=12))
        self.assertIsNone(parse_duration("P1M"))
        self.assertIsNone(parse_duration("7 days"))


class AddedPackagesTest(unittest.TestCase):
    def test_only_new_name_version_pairs(self) -> None:
        base = {
            Package("npm", "a", "1.0.0", "registry", ""),
            Package("npm", "b", "1.0.0", "registry", ""),
        }
        head = {
            Package("npm", "a", "1.0.1", "registry", ""),
            Package("npm", "b", "1.0.0", "registry", ""),
        }
        self.assertEqual(
            added_packages(base, head), [Package("npm", "a", "1.0.1", "registry", "")]
        )


if __name__ == "__main__":
    unittest.main()
