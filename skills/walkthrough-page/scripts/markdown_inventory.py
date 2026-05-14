#!/usr/bin/env python3
# ABOUTME: Extracts a compact teaching inventory from Markdown source files.
# ABOUTME: Finds headings, fenced code, checklist items, and links for walkthrough planning.
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^```([A-Za-z0-9_+.-]*)\s*$")
CHECKLIST_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def clean_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def preview_code(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return ""


def inventory_markdown(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings: list[dict[str, Any]] = []
    code_blocks: list[dict[str, Any]] = []
    checklist_items: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []

    in_code = False
    code_language = ""
    code_start = 0
    code_lines: list[str] = []

    for index, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match and not in_code:
            in_code = True
            code_language = fence_match.group(1)
            code_start = index
            code_lines = []
            continue

        if fence_match and in_code:
            code_blocks.append(
                {
                    "language": code_language,
                    "line_start": code_start,
                    "line_end": index,
                    "preview": preview_code(code_lines),
                }
            )
            in_code = False
            code_language = ""
            code_start = 0
            code_lines = []
            continue

        if in_code:
            code_lines.append(line)
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            headings.append(
                {
                    "level": len(heading_match.group(1)),
                    "text": clean_inline_markdown(heading_match.group(2).rstrip("# ")),
                    "line": index,
                }
            )

        checklist_match = CHECKLIST_RE.match(line)
        if checklist_match:
            checklist_items.append(
                {
                    "checked": checklist_match.group(1).lower() == "x",
                    "text": clean_inline_markdown(checklist_match.group(2)),
                    "line": index,
                }
            )

        for link_match in LINK_RE.finditer(line):
            links.append(
                {
                    "text": clean_inline_markdown(link_match.group(1)),
                    "url": link_match.group(2),
                    "line": index,
                }
            )

    title = next((heading["text"] for heading in headings if heading["level"] == 1), "")
    return {
        "source": str(path),
        "title": title,
        "headings": headings,
        "code_blocks": code_blocks,
        "checklist_items": checklist_items,
        "links": links,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a compact inventory from Markdown.")
    parser.add_argument("path", type=Path, help="Markdown file to inspect")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    inventory = inventory_markdown(args.path)
    indent = 2 if args.pretty else None
    print(json.dumps(inventory, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
