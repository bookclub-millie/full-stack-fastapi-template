"""Parse bun.lock / uv.lock and the cooldown settings that guard them.

Everything here treats file contents as untrusted data: no evaluation, only
parsing into plain values.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import timedelta

import tomllib

NPM_REGISTRY_URLS = ("https://registry.npmjs.org/",)
PYPI_REGISTRY_URLS = ("https://pypi.org/simple", "https://pypi.org/simple/")


@dataclass(frozen=True, order=True)
class Package:
    ecosystem: str  # "npm" | "pypi"
    name: str
    version: str
    source: str  # "registry" | "local" | "other"
    detail: str  # where a non-registry package comes from


def loads_jsonc(text: str) -> object:
    """Load bun.lock, which is JSON plus trailing commas."""
    out: list[str] = []
    in_string = escaped = False
    pending_comma = False
    for ch in text:
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == ",":
            if pending_comma:
                out.append(",")
            pending_comma = True
            continue
        if ch in " \t\r\n":
            out.append(ch)
            continue
        if pending_comma and ch not in "]}":
            out.append(",")
        pending_comma = False
        if ch == '"':
            in_string = True
        out.append(ch)
    return json.loads("".join(out))


def _split_spec(spec: str) -> tuple[str, str]:
    # "@scope/name@1.2.3" -> ("@scope/name", "1.2.3")
    at = spec.rfind("@")
    if at <= 0:
        return spec, ""
    return spec[:at], spec[at + 1 :]


def parse_bun_lock(text: str) -> set[Package]:
    data = loads_jsonc(text)
    packages: set[Package] = set()
    entries = data.get("packages", {}) if isinstance(data, dict) else {}
    for entry in entries.values():
        if not isinstance(entry, list) or not entry or not isinstance(entry[0], str):
            continue
        name, version = _split_spec(entry[0])
        if version.startswith(("workspace:", "link:", "file:")):
            packages.add(Package("npm", name, version, "local", version))
            continue
        tarball = entry[1] if len(entry) > 1 and isinstance(entry[1], str) else None
        if tarball is None or ":" in version or "/" in version:
            # github:, git+, https:// tarballs and other exotic specs
            packages.add(Package("npm", name, version, "other", version))
        elif tarball == "" or tarball.startswith(NPM_REGISTRY_URLS):
            packages.add(Package("npm", name, version, "registry", ""))
        else:
            packages.add(Package("npm", name, version, "other", tarball))
    return packages


def normalize_pypi_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_uv_lock(text: str) -> set[Package]:
    data = tomllib.loads(text)
    packages: set[Package] = set()
    for entry in data.get("package", []):
        name = normalize_pypi_name(str(entry.get("name", "")))
        version = str(entry.get("version", ""))
        source = entry.get("source", {})
        if not isinstance(source, dict):
            source = {}
        if source.get("registry") in PYPI_REGISTRY_URLS:
            packages.add(Package("pypi", name, version, "registry", ""))
        elif source.keys() & {"editable", "virtual", "directory", "path"}:
            packages.add(
                Package(
                    "pypi", name, version, "local", json.dumps(source, sort_keys=True)
                )
            )
        else:
            packages.add(
                Package(
                    "pypi", name, version, "other", json.dumps(source, sort_keys=True)
                )
            )
    return packages


def added_packages(base: set[Package], head: set[Package]) -> list[Package]:
    return sorted(head - base)


_DURATION = re.compile(
    r"^P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
)


def parse_duration(value: str) -> timedelta | None:
    """Parse the ISO 8601 spans uv writes into uv.lock (no months/years)."""
    match = _DURATION.match(value)
    if not match or value in ("P", "PT"):
        return None
    weeks, days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return timedelta(
        weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds
    )


def uv_cooldown(lock_text: str | None) -> tuple[timedelta | None, set[str]]:
    """Return (exclude-newer span, per-package overrides) recorded in uv.lock."""
    if not lock_text:
        return None, set()
    options = tomllib.loads(lock_text).get("options", {})
    span = options.get("exclude-newer-span")
    overrides = options.get("exclude-newer-package", {})
    excluded = (
        {normalize_pypi_name(name) for name in overrides}
        if isinstance(overrides, dict)
        else set()
    )
    return (parse_duration(span) if isinstance(span, str) else None), excluded


def bun_cooldown(bunfig_text: str | None) -> tuple[timedelta | None, set[str]]:
    """Return (minimumReleaseAge, excludes) from bunfig.toml."""
    if not bunfig_text:
        return None, set()
    install = tomllib.loads(bunfig_text).get("install", {})
    age = install.get("minimumReleaseAge")
    excludes = install.get("minimumReleaseAgeExcludes", [])
    excluded = {str(name) for name in excludes} if isinstance(excludes, list) else set()
    if isinstance(age, bool) or not isinstance(age, int):
        return None, excluded
    return timedelta(seconds=age), excluded
