#!/usr/bin/env python3
# ABOUTME: Validates static walkthrough pages for basic structural integrity.
# ABOUTME: Checks copy targets, placeholders, metadata, and section coverage.
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


FIRST_COMMENT_RE = re.compile(r"<!--(?P<body>.*?)-->", re.DOTALL)
ABOUTME_RE = re.compile(r"ABOUTME:\s+\S.*\n\s*ABOUTME:\s+\S", re.MULTILINE)
TEMPLATE_PLACEHOLDERS = (
    "Walkthrough Page Template",
    "Replace this with the concept, workflow, or onboarding promise.",
    "State who this is for, what they will understand, and what they can copy or run from this page.",
    "Show the few nouns, stages, or decisions the reader must keep in their head.",
    "replace-with-real-command",
    "Replace with output captured from a real run, or label it as example output.",
    "What it owns, why it exists, and what breaks if it is wrong.",
    "How it connects to the next stage. Link to exact files when useful.",
    "What the reader should expect to see and where to inspect it.",
    "Name the success signal: a file, metric, UI state, log line, or artifact.",
    "Name one realistic failure mode and the fastest root-cause check.",
    "Replace this footer with links to source docs, next steps, or ownership notes.",
)


@dataclass
class PageFacts:
    title: str = ""
    has_viewport: bool = False
    sections: int = 0
    ids: list[str] = field(default_factory=list)
    copy_targets: list[str] = field(default_factory=list)
    code_ids: list[str] = field(default_factory=list)
    buttons: int = 0


class WalkthroughParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.facts = PageFacts()
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "meta" and attr.get("name") == "viewport":
            self.facts.has_viewport = True
        if tag == "section":
            self.facts.sections += 1
        if "id" in attr and attr["id"]:
            self.facts.ids.append(attr["id"])
            if tag == "code":
                self.facts.code_ids.append(attr["id"])
        if "data-copy-for" in attr and attr["data-copy-for"]:
            self.facts.copy_targets.append(attr["data-copy-for"])
        if tag == "button":
            self.facts.buttons += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.facts.title += data.strip()


def has_aboutme_header(text: str) -> bool:
    search_window = text[:4096]
    first_comment = FIRST_COMMENT_RE.search(search_window)
    if first_comment and ABOUTME_RE.search(first_comment.group("body").strip()):
        return True
    return bool(ABOUTME_RE.search(text[:2048]))


def validate_page(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{path} does not exist"]
    if not path.is_file():
        return [f"{path} is not a file"]

    text = path.read_text(encoding="utf-8")
    parser = WalkthroughParser()
    parser.feed(text)
    facts = parser.facts

    if not has_aboutme_header(text):
        errors.append("missing two ABOUTME lines in the first HTML comment or page header")
    if "<!doctype html>" not in text[:200].lower():
        errors.append("missing <!doctype html> near the top")
    if not facts.title:
        errors.append("missing <title>")
    if facts.title == "Walkthrough Page Template":
        errors.append("template title was not replaced")
    if not facts.has_viewport:
        errors.append("missing viewport meta tag")
    if facts.sections < 3:
        errors.append("expected at least 3 <section> elements")

    duplicates = sorted({item for item in facts.ids if facts.ids.count(item) > 1})
    for duplicate in duplicates:
        errors.append(f"duplicate id: {duplicate}")

    known_ids = set(facts.ids)
    for target in facts.copy_targets:
        if target not in known_ids:
            errors.append(f"copy button points at missing id: {target}")

    if facts.code_ids and not facts.copy_targets:
        errors.append("code blocks exist but no copy buttons were found")

    for placeholder in TEMPLATE_PLACEHOLDERS:
        if placeholder in text:
            errors.append(f"template placeholder remains: {placeholder}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a static walkthrough HTML page.")
    parser.add_argument("path", type=Path, help="Path to an HTML walkthrough page")
    args = parser.parse_args()

    errors = validate_page(args.path)
    if errors:
        print("walkthrough page validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"walkthrough page validation passed: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
