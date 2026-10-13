"""Render the gate report as Markdown for the PR comment and job summary.

Every string that came from the PR (paths, package names, tool output) is put
inside code spans or code blocks so it cannot mention users, link, or inject
markup.
"""

from __future__ import annotations

import re

MARKER = "<!-- harness-gate -->"
ACK_LABEL = "harness-ack"
MAX_ITEMS = 25
MAX_ITEM_LENGTH = 200
MAX_LOG_LINES = 40

_CONTROL = re.compile(r"[\x00-\x1f\x7f\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF]")


def code(text: str) -> str:
    text = _CONTROL.sub(" ", str(text)).replace("`", "'").strip()
    if len(text) > MAX_ITEM_LENGTH:
        text = text[:MAX_ITEM_LENGTH] + "…"
    return f"`{text}`" if text else "` `"


def _items(items: list[str]) -> list[str]:
    lines = [f"  - {code(item)}" for item in items[:MAX_ITEMS]]
    if len(items) > MAX_ITEMS:
        lines.append(f"  - 외 {len(items) - MAX_ITEMS}건 (job summary 참고)")
    return lines


def _log(log: str) -> list[str]:
    # Drop progress lines (zizmor prints " INFO ..." per file) and keep the findings.
    kept = [line for line in log.splitlines() if line.strip() and " INFO " not in line]
    tail = [_CONTROL.sub(" ", line) for line in kept][-MAX_LOG_LINES:]
    body = "\n".join(tail).replace("```", "'''")
    return ["  ```text", *("  " + line for line in body.splitlines()), "  ```"]


def render(report: dict) -> str:
    status_icon = {"pass": "✅ 통과", "fail": "❌ 실패", "skip": "➖ 해당 없음"}
    lines = [
        MARKER,
        "## Harness Gate",
        "",
        f"head {code(report['head'][:12])} 기준 자동 검사 결과입니다. 이 결과는 PR 코드를 실행하지 않고 base 브랜치의 검사 코드로 만들었습니다.",
        "",
        "### 결정적 검사 (`harness/checks`)",
        "",
        "| 검사 | 결과 |",
        "|---|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['title']} | {status_icon[check['status']]} |")
    for check in report["checks"]:
        if check["status"] != "fail":
            continue
        lines += ["", f"- **{check['title']}**", *_items(check["items"])]
        if check.get("log"):
            lines += _log(check["log"])
    if report["deterministic_failed"]:
        lines += [
            "",
            "결정적 검사 실패는 사람 확인으로 넘길 수 없습니다. 원인을 고친 커밋을 push하세요.",
        ]

    lines += ["", "### 사람 확인이 필요한 신호 (`harness/ack`)", ""]
    if not report["signals"]:
        lines.append("확인이 필요한 신호가 없습니다.")
    else:
        for signal in report["signals"]:
            lines += [
                f"- **{signal['title']}** ({len(signal['items'])}건)",
                *_items(signal["items"]),
            ]
        lines += [
            "",
            (
                f"PR 작성자가 아닌 write 권한자가 변경 이유를 확인하고 `{ACK_LABEL}` 라벨을 붙이면 통과합니다. "
                "새 커밋이 push되면 라벨이 자동으로 해제되므로 다시 확인해야 합니다."
            ),
        ]
    return "\n".join(lines) + "\n"
