# ABOUTME: Tests helper scripts bundled with the walkthrough-page skill.
# ABOUTME: Covers Markdown inventory extraction and static page validation.
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "walkthrough-page" / "scripts"


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class WalkthroughPageScriptTests(unittest.TestCase):
    def test_markdown_inventory_extracts_teaching_material(self) -> None:
        import tempfile

        markdown_inventory = load_script("markdown_inventory")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "walkthrough.md"
            source.write_text(
                """# Project onboarding

Start here.

## Run it

```bash
uv run phenobench --help
```

- [x] Install deps
- [ ] Run smoke

Read [docs](docs/onboarding.md).
""",
                encoding="utf-8",
            )

            inventory = markdown_inventory.inventory_markdown(source)

        self.assertEqual(inventory["title"], "Project onboarding")
        self.assertEqual(
            inventory["headings"],
            [
                {"level": 1, "text": "Project onboarding", "line": 1},
                {"level": 2, "text": "Run it", "line": 5},
            ],
        )
        self.assertEqual(
            inventory["code_blocks"],
            [
                {
                    "language": "bash",
                    "line_start": 7,
                    "line_end": 9,
                    "preview": "uv run phenobench --help",
                }
            ],
        )
        self.assertEqual(
            inventory["checklist_items"],
            [
                {"checked": True, "text": "Install deps", "line": 11},
                {"checked": False, "text": "Run smoke", "line": 12},
            ],
        )
        self.assertEqual(
            inventory["links"],
            [{"text": "docs", "url": "docs/onboarding.md", "line": 14}],
        )

    def test_markdown_inventory_handles_setext_tilde_fences_and_crlf(self) -> None:
        import tempfile

        markdown_inventory = load_script("markdown_inventory")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "walkthrough.md"
            source.write_text(
                "Project onboarding\r\n"
                "==================\r\n"
                "\r\n"
                "Run it\r\n"
                "------\r\n"
                "\r\n"
                "~~~bash\r\n"
                "uv run tool\r\n"
                "~~~\r\n",
                encoding="utf-8",
            )

            inventory = markdown_inventory.inventory_markdown(source)

        self.assertEqual(inventory["title"], "Project onboarding")
        self.assertEqual(
            inventory["headings"],
            [
                {"level": 1, "text": "Project onboarding", "line": 1},
                {"level": 2, "text": "Run it", "line": 4},
            ],
        )
        self.assertEqual(
            inventory["code_blocks"],
            [
                {
                    "language": "bash",
                    "line_start": 7,
                    "line_end": 9,
                    "preview": "uv run tool",
                }
            ],
        )

    def test_validate_page_rejects_template_placeholders(self) -> None:
        import tempfile

        validate_page = load_script("validate_page")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                """<!--
ABOUTME: Example walkthrough page.
ABOUTME: Demonstrates validation failure.
-->
<!doctype html>
<html><head><meta name="viewport" content="width=device-width"><title>Walkthrough Page Template</title></head>
<body>
<section></section><section></section><section></section>
<pre><code id="cmd">Replace with real command</code></pre>
<button data-copy-for="missing">Copy</button>
</body></html>
""",
                encoding="utf-8",
            )

            errors = validate_page.validate_page(page)

        self.assertIn("template title was not replaced", errors)
        self.assertIn("copy button points at missing id: missing", errors)
        self.assertIn("template placeholder remains: Walkthrough Page Template", errors)

    def test_validate_page_accepts_legitimate_todo_and_replace_text(self) -> None:
        import tempfile

        validate_page = load_script("validate_page")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                """<!--
ABOUTME: Example walkthrough page.
ABOUTME: Documents a real command workflow.
-->
<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Maintenance walkthrough</title>
</head>
<body>
  <section><h2>Model</h2><p>TODO: keep this note because it is part of the source code.</p></section>
  <section><h2>Run</h2><pre><code id="cmd">sed 's/foo/bar/' file.txt</code></pre><button data-copy-for="cmd">Copy</button></section>
  <section><h2>Artifacts</h2><p>Replace this string with a configured value when running locally.</p></section>
</body>
</html>
""",
                encoding="utf-8",
            )

            errors = validate_page.validate_page(page)

        self.assertEqual(errors, [])

    def test_validate_page_detects_template_command_placeholder(self) -> None:
        import tempfile

        validate_page = load_script("validate_page")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                """<!--
ABOUTME: Example walkthrough page.
ABOUTME: Demonstrates template placeholder detection.
-->
<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project walkthrough</title>
</head>
<body>
  <section><h2>Model</h2></section>
  <section><h2>Run</h2><pre><code id="cmd">replace-with-real-command --help</code></pre><button data-copy-for="cmd">Copy</button></section>
  <section><h2>Artifacts</h2></section>
</body>
</html>
""",
                encoding="utf-8",
            )

            errors = validate_page.validate_page(page)

        self.assertIn("template placeholder remains: replace-with-real-command", errors)

    def test_validate_page_accepts_aboutme_in_first_html_comment_after_long_head(self) -> None:
        import tempfile

        validate_page = load_script("validate_page")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                f"""<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project walkthrough</title>
  <style>{'x' * 900}</style>
</head>
<!--
ABOUTME: Example walkthrough page.
ABOUTME: Keeps page metadata in the first HTML comment.
-->
<body>
  <section><h2>Model</h2></section>
  <section><h2>Run</h2><pre><code id="cmd">uv run tool --help</code></pre><button data-copy-for="cmd">Copy</button></section>
  <section><h2>Artifacts</h2></section>
</body>
</html>
""",
                encoding="utf-8",
            )

            errors = validate_page.validate_page(page)

        self.assertEqual(errors, [])

    def test_validate_page_accepts_complete_static_page(self) -> None:
        import tempfile

        validate_page = load_script("validate_page")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                """<!--
ABOUTME: Example walkthrough page.
ABOUTME: Demonstrates a complete static walkthrough.
-->
<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project walkthrough</title>
</head>
<body>
  <section><h2>Model</h2></section>
  <section><h2>Run</h2><pre><code id="cmd">uv run tool --help</code></pre><button data-copy-for="cmd">Copy</button></section>
  <section><h2>Artifacts</h2></section>
</body>
</html>
""",
                encoding="utf-8",
            )

            errors = validate_page.validate_page(page)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
