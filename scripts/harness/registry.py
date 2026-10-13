"""Publish-time lookups against the public npm and PyPI registries."""

from __future__ import annotations

import functools
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime

from lockfiles import Package

USER_AGENT = "harness-gate/1 (+https://github.com/fastapi/full-stack-fastapi-template)"
TIMEOUT_SECONDS = 30
ATTEMPTS = 3


class NotFound(Exception):
    pass


@dataclass
class Release:
    published: datetime | None  # when this exact version was uploaded
    first_published: datetime | None  # when the package name first appeared


def _get_json(url: str, accept: str = "application/json") -> object:
    request = urllib.request.Request(
        url,
        headers={"Accept": accept, "Accept-Encoding": "gzip", "User-Agent": USER_AGENT},
    )
    for attempt in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return json.loads(body)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise NotFound(url) from error
            if error.code < 500 and error.code != 429 or attempt == ATTEMPTS - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == ATTEMPTS - 1:
                raise
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@functools.cache
def _npm_times(name: str) -> dict[str, object]:
    # Only the full packument carries publish times (it can be several MB).
    packument = _get_json(
        "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@")
    )
    times = packument.get("time", {}) if isinstance(packument, dict) else {}
    return times if isinstance(times, dict) else {}


def npm_release(name: str, version: str) -> Release:
    times = _npm_times(name)
    return Release(_parse_time(times.get(version)), _parse_time(times.get("created")))


def pypi_release(name: str, version: str, *, need_first: bool) -> Release:
    quoted = urllib.parse.quote(name)
    data = _get_json(
        f"https://pypi.org/pypi/{quoted}/{urllib.parse.quote(version)}/json"
    )
    uploads = [_parse_time(f.get("upload_time_iso_8601")) for f in data.get("urls", [])]
    published = min((t for t in uploads if t), default=None)
    first = None
    if need_first:
        simple = _get_json(
            f"https://pypi.org/simple/{quoted}/",
            accept="application/vnd.pypi.simple.v1+json",
        )
        files = [_parse_time(f.get("upload-time")) for f in simple.get("files", [])]
        first = min((t for t in files if t), default=None)
    return Release(published, first)


def lookup(package: Package, *, need_first: bool) -> Release:
    if package.ecosystem == "npm":
        return npm_release(package.name, package.version)
    return pypi_release(package.name, package.version, need_first=need_first)
