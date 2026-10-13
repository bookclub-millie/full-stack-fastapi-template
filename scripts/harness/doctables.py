"""Read the Markdown tables of the docs/*.md templates as rows of {header: cell}."""

from __future__ import annotations

import re

_PIPE = re.compile(r"(?<!\\)\|")
_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")


def _cells(line: str) -> list[str]:
    inner = line.strip()
    inner = inner.removeprefix("|")
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [cell.strip().replace("\\|", "|") for cell in _PIPE.split(inner)]


def section(text: str | None, heading: str) -> str:
    """Body of the `## heading` section (up to the next `## `)."""
    lines: list[str] = []
    inside = False
    for line in (text or "").splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == heading
            continue
        if inside:
            lines.append(line)
    return "\n".join(lines)


def table(text: str | None, heading: str) -> list[dict[str, str]]:
    """Rows of the first table in the `## heading` section."""
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in section(text, heading).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header is not None:
                break
            continue
        if header is None:
            header = _cells(stripped)
        elif not _SEPARATOR.match(stripped):
            cells = _cells(stripped)
            rows.append(
                {
                    name: (cells[i] if i < len(cells) else "")
                    for i, name in enumerate(header)
                }
            )
    return rows


def filled(row: dict[str, str]) -> int:
    return sum(1 for value in row.values() if value.strip())


def cell(row: dict[str, str], *names: str) -> str:
    """First column whose header starts with one of `names`."""
    for name in names:
        for header, value in row.items():
            if header.startswith(name):
                return value
    return ""


def all_rows(text: str | None) -> list[dict[str, str]]:
    """Rows of every table in the document."""
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None
        elif header is None:
            header = _cells(stripped)
        elif not _SEPARATOR.match(stripped):
            cells = _cells(stripped)
            rows.append(
                {
                    name: (cells[i] if i < len(cells) else "")
                    for i, name in enumerate(header)
                }
            )
    return rows
